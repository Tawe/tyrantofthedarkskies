"""Zone random encounter system (docs/random_encounters.md)."""

import os
import json
import random
import time
import uuid

ENCOUNTER_COOLDOWN_SECONDS = 120
ENCOUNTER_ROLL_CHANCE = 0.35
DEBUG_RANDOM_ENCOUNTERS = os.getenv("MUD_DEBUG_ENCOUNTERS", "").lower() in ("1", "true", "yes")


class EncounterService:
    """Loads zone encounter tables and compositions; rolls and spawns random encounters on room enter."""

    def __init__(self, runtime_state=None, npcs=None):
        self.runtime_state = runtime_state
        self.npcs = npcs or {}
        self.zone_encounter_tables = {}
        self.encounter_compositions = {}

    def load(self):
        """Load zone encounter tables and compositions from contributions/encounters/."""
        encounters_dir = "contributions/encounters"
        if not os.path.exists(encounters_dir):
            return
        comp_path = os.path.join(encounters_dir, "compositions.json")
        if os.path.exists(comp_path):
            try:
                with open(comp_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                for key, entries in raw.items():
                    self.encounter_compositions[key] = [
                        (e["template_id"], e["min_count"], e["max_count"])
                        for e in entries
                    ]
            except Exception as e:
                print(f"Error loading encounter compositions: {e}")
        for filename in os.listdir(encounters_dir):
            if filename in ("compositions.json", "README.md") or not filename.endswith(".json"):
                continue
            filepath = os.path.join(encounters_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                zone_id = data.get("zone_id")
                table = data.get("table", [])
                if not zone_id:
                    continue
                self.zone_encounter_tables[zone_id] = [
                    (e["min_roll"], e["max_roll"], e["encounter_type"], e.get("composition_key"))
                    for e in table
                ]
            except Exception as e:
                print(f"Error loading encounter zone {filename}: {e}")
        if self.zone_encounter_tables or self.encounter_compositions:
            print(f"Loaded {len(self.zone_encounter_tables)} zone encounter tables, {len(self.encounter_compositions)} compositions")
            if DEBUG_RANDOM_ENCOUNTERS:
                for zid, table in self.zone_encounter_tables.items():
                    print(f"  [encounter] zone={zid} rows={len(table)}")
                print(f"  [encounter] composition keys: {list(self.encounter_compositions.keys())}")

    def roll_random_encounter(self, room_id, get_room):
        """Roll zone random encounter table; spawn combat group with shared encounter_id if combat. get_room(room_id) returns Room or None."""
        debug = DEBUG_RANDOM_ENCOUNTERS
        if debug:
            print(f"[encounter] roll_random_encounter called room_id={room_id}")
        if not self.runtime_state:
            if debug:
                print("[encounter] skip: no runtime_state")
            return
        room = get_room(room_id) if get_room else None
        if not room:
            if debug:
                print(f"[encounter] skip: room not found {room_id}")
            return
        zone = getattr(room, "zone", None)
        if not zone or zone not in self.zone_encounter_tables:
            if debug:
                print(f"[encounter] skip: room zone={zone!r}, in_tables={zone in self.zone_encounter_tables if zone else False}")
            return
        state = self.runtime_state.get_or_create_room_state(room_id)
        now = time.time()
        if random.random() > ENCOUNTER_ROLL_CHANCE:
            if debug:
                print(f"[encounter] skip: roll chance failed (>{ENCOUNTER_ROLL_CHANCE})")
            return
        last_roll = state.get("last_encounter_roll_at", 0)
        if now - last_roll < ENCOUNTER_COOLDOWN_SECONDS:
            if debug:
                print(f"[encounter] skip: cooldown ({now - last_roll:.0f}s < {ENCOUNTER_COOLDOWN_SECONDS}s)")
            return
        roll = random.randint(1, 100)
        table = self.zone_encounter_tables[zone]
        matched = None
        for min_r, max_r, etype, comp_key in table:
            if min_r <= roll <= max_r:
                matched = (min_r, max_r, etype, comp_key)
                break
        else:
            if debug:
                print(f"[encounter] skip: d100={roll} matched no table row in zone={zone}")
            return
        if debug:
            print(f"[encounter] zone={zone} d100={roll} -> range {matched[0]}-{matched[1]} type={matched[2]} composition={matched[3]!r}")
        if matched[2] != "combat" or not matched[3]:
            self.runtime_state.set_room_state_fields(room_id, last_encounter_roll_at=now)
            if debug:
                print("[encounter] non-combat or no composition; cooldown set")
            return
        comp_key = matched[3]
        composition = self.encounter_compositions.get(comp_key)
        if not composition:
            if debug:
                print(f"[encounter] skip: composition {comp_key!r} not found (keys: {list(self.encounter_compositions.keys())[:10]}...)")
            return
        encounter_id = str(uuid.uuid4())
        spawned = []
        for template_id, cmin, cmax in composition:
            count = random.randint(cmin, cmax)
            template = self.npcs.get(template_id)
            if not template:
                if debug:
                    print(f"[encounter] skip template {template_id!r}: not in npcs")
                continue
            hp_max = getattr(template, "max_health", getattr(template, "health", 10))
            role_raw = getattr(template, "combat_role", None) or getattr(template, "role", "Minion")
            role_lower = role_raw.lower() if isinstance(role_raw, str) else "minion"
            for _ in range(count):
                instance_id = self.runtime_state.create_entity_instance(
                    template_id,
                    "creature",
                    tier=getattr(template, "tier", "Low"),
                    role=role_lower,
                    hp_current=hp_max,
                    hp_max=hp_max,
                    speed_cost=getattr(template, "speed_cost", 1.0),
                    encounter_id=encounter_id,
                    pursuit_mode=getattr(template, "pursuit_mode", None),
                )
                self.runtime_state.place_entity(instance_id, room_id)
                spawned.append((template_id, instance_id))
        self.runtime_state.set_room_state_fields(room_id, last_encounter_roll_at=now)
        if debug:
            print(f"[encounter] spawned room={room_id} composition={comp_key} encounter_id={encounter_id[:8]}... count={len(spawned)} {spawned}")
