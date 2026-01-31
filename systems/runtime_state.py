"""
Runtime state service per docs/runtime_state.md.

- R2: Entity instances (creatures, NPCs, items in the world).
- R3: Room-scoped state (seed, timers, spawn/loot state).
- R4: Lazy state creation (room_state on first entry or when needed).
- R5: Deterministic spawn/loot via room seed.
- R6: Cleanup/expiry support via timestamps.
"""

import time
import uuid
from typing import Dict, List, Optional, Any


# Default reset window (seconds). Rooms can reset spawn/loot eligibility after this.
DEFAULT_RESET_SECONDS = 3600  # 1 hour


def _now_ts() -> float:
    return time.time()


def _new_instance_id() -> str:
    return str(uuid.uuid4())


class RuntimeStateService:
    """Service for room state and entity instances. Uses FirebaseDataLayer when available."""

    def __init__(self, data_layer=None):
        self.data_layer = data_layer  # FirebaseDataLayer or None

    def _enabled(self) -> bool:
        return self.data_layer is not None

    def get_or_create_room_state(self, room_id: str) -> Dict:
        """
        Load room_state for room_id; create with defaults if missing (R4 lazy creation).
        Required: room_id, seed, created_at, last_active_at, last_reset_at, next_reset_at.
        """
        if not self._enabled():
            return {}
        state = self.data_layer.load_room_state(room_id)
        if state is not None:
            # R5: ensure spawn_timers and loot_timers exist for B5
            state.setdefault("spawn_timers", {})
            state.setdefault("loot_timers", {})
            return state
        now = _now_ts()
        state = {
            "room_id": room_id,
            "seed": int(now) % (2 ** 31),
            "created_at": now,
            "last_active_at": now,
            "last_reset_at": now,
            "next_reset_at": now + DEFAULT_RESET_SECONDS,
            "state_version": 1,
            "spawn_timers": {},   # R5: per spawn_id: last_spawn_at, next_spawn_at, alive_count
            "loot_timers": {},    # R5: per loot_id: last_loot_roll_at, next_loot_roll_at
        }
        self.data_layer.save_room_state(room_id, state)
        return state

    def update_room_last_active(self, room_id: str, *, state: Optional[Dict] = None) -> None:
        """Update last_active_at when players interact in the room (B1). Pass state from get_or_create_room_state to avoid a second load."""
        if not self._enabled():
            return
        if state is None:
            state = self.get_or_create_room_state(room_id)
        state["last_active_at"] = _now_ts()
        self.data_layer.save_room_state(room_id, state)

    def set_room_state_fields(self, room_id: str, *, state: Optional[Dict] = None, **fields) -> None:
        """Update arbitrary room_state fields (e.g. last_encounter_roll_at). Pass state to avoid an extra load."""
        if not self._enabled():
            return
        if state is None:
            state = self.get_or_create_room_state(room_id)
        for key, value in fields.items():
            state[key] = value
        self.data_layer.save_room_state(room_id, state)

    def get_spawn_timer(self, room_id: str, spawn_id: str) -> Dict:
        """R5/B5: Get timer for spawn_id (last_spawn_at, next_spawn_at, alive_count)."""
        state = self.get_or_create_room_state(room_id)
        timers = state.setdefault("spawn_timers", {})
        return dict(timers.get(spawn_id, {}))

    def update_spawn_timer(
        self,
        room_id: str,
        spawn_id: str,
        *,
        last_spawn_at: Optional[float] = None,
        next_spawn_at: Optional[float] = None,
        alive_count: Optional[int] = None,
    ) -> None:
        """R5/B5: Update spawn timer for spawn_id; merge with existing."""
        if not self._enabled():
            return
        state = self.get_or_create_room_state(room_id)
        timers = state.setdefault("spawn_timers", {})
        entry = dict(timers.get(spawn_id, {}))
        if last_spawn_at is not None:
            entry["last_spawn_at"] = last_spawn_at
        if next_spawn_at is not None:
            entry["next_spawn_at"] = next_spawn_at
        if alive_count is not None:
            entry["alive_count"] = alive_count
        timers[spawn_id] = entry
        self.data_layer.save_room_state(room_id, state)

    def get_loot_timer(self, room_id: str, loot_id: str) -> Dict:
        """R5/B5: Get timer for loot_id (last_loot_roll_at, next_loot_roll_at)."""
        state = self.get_or_create_room_state(room_id)
        timers = state.setdefault("loot_timers", {})
        return dict(timers.get(loot_id, {}))

    def update_loot_timer(
        self,
        room_id: str,
        loot_id: str,
        *,
        last_loot_roll_at: Optional[float] = None,
        next_loot_roll_at: Optional[float] = None,
    ) -> None:
        """R5/B5: Update loot timer for loot_id; merge with existing."""
        if not self._enabled():
            return
        state = self.get_or_create_room_state(room_id)
        timers = state.setdefault("loot_timers", {})
        entry = dict(timers.get(loot_id, {}))
        if last_loot_roll_at is not None:
            entry["last_loot_roll_at"] = last_loot_roll_at
        if next_loot_roll_at is not None:
            entry["next_loot_roll_at"] = next_loot_roll_at
        timers[loot_id] = entry
        self.data_layer.save_room_state(room_id, state)

    def try_consume_spawn_eligibility(
        self,
        room_id: str,
        spawn_id: str,
        *,
        max_alive: int = 1,
        cooldown_seconds: float = 60.0,
    ) -> bool:
        """
        C3: Atomically check and consume one spawn slot for spawn_id in room.
        Returns True if eligibility was consumed (caller may spawn); False if not eligible.
        Prevents duplicate spawn when two players enter simultaneously.
        """
        if not self._enabled() or not hasattr(self.data_layer, "run_room_state_transaction"):
            return False
        now = _now_ts()

        def _do(transaction, room_ref):
            snapshot = room_ref.get(transaction=transaction)
            state = snapshot.to_dict() if snapshot.exists else {}
            state.setdefault("spawn_timers", {})
            timers = state["spawn_timers"]
            entry = dict(timers.get(spawn_id, {}))
            alive = entry.get("alive_count", 0)
            next_at = entry.get("next_spawn_at", 0)
            if alive < max_alive and now >= next_at:
                entry["alive_count"] = alive + 1
                entry["last_spawn_at"] = now
                entry["next_spawn_at"] = now + cooldown_seconds
                timers[spawn_id] = entry
                state["spawn_timers"] = timers
                return (True, state)
            return (False, None)

        return self.data_layer.run_room_state_transaction(room_id, _do)

    def get_entities_in_room(self, room_id: str) -> List[Dict]:
        """
        Return list of entity instances currently in this room (entity_instance + position info).
        Each item: {instance_id, template_id, entity_type, ...instance fields, room_id, range_band?, ...}.
        B4: Expired instances (expires_at in the past) are removed from the world and excluded from results.
        """
        if not self._enabled():
            return []
        now = _now_ts()
        positions = self.data_layer.load_entity_positions_for_room(room_id)
        out = []
        for pos in positions:
            instance_id = pos.get("instance_id")
            if not instance_id:
                continue
            inst = self.data_layer.load_entity_instance(instance_id)
            if inst is None:
                continue
            expires_at = inst.get("expires_at")
            if expires_at is not None and expires_at <= now:
                self.remove_entity_from_world(instance_id, delete_instance=True)
                continue
            combined = {**inst, "instance_id": instance_id, **pos}
            out.append(combined)
        return out

    def create_entity_instance(
        self,
        template_id: str,
        entity_type: str,
        *,
        tier: Optional[str] = None,
        role: Optional[str] = None,
        hp_current: Optional[int] = None,
        hp_max: Optional[int] = None,
        attack_interval: Optional[float] = None,
        speed_cost: Optional[float] = None,
        accuracy: Optional[int] = None,
        quantity: Optional[int] = None,
        durability_current: Optional[int] = None,
        modifier_id: Optional[str] = None,
        status_effects: Optional[Dict] = None,
        expires_at: Optional[float] = None,
        spawn_group_id: Optional[str] = None,
        loot_group_id: Optional[str] = None,
        encounter_id: Optional[str] = None,
        pursuit_mode: Optional[str] = None,
        **extra,
    ) -> str:
        """
        Create an entity instance (R2). Returns instance_id.
        entity_type: 'creature' | 'npc' | 'item'
        P2: pursuit_mode for creatures: 'none' | 'short' | 'long'.
        """
        if not self._enabled():
            return ""
        instance_id = _new_instance_id()
        now = _now_ts()
        data = {
            "instance_id": instance_id,
            "template_id": template_id,
            "entity_type": entity_type,
            "created_at": now,
            **extra,
        }
        if entity_type in ("creature", "npc"):
            if tier is not None:
                data["tier"] = tier
            if role is not None:
                data["role"] = role
            if pursuit_mode is not None:
                data["pursuit_mode"] = pursuit_mode
            if hp_current is not None:
                data["hp_current"] = hp_current
            if hp_max is not None:
                data["hp_max"] = hp_max
            if attack_interval is not None:
                data["attack_interval"] = attack_interval
            if speed_cost is not None:
                data["speed_cost"] = speed_cost
            if accuracy is not None:
                data["accuracy"] = accuracy
        if entity_type == "item":
            if quantity is not None:
                data["quantity"] = quantity
            if durability_current is not None:
                data["durability_current"] = durability_current
            if modifier_id is not None:
                data["modifier_id"] = modifier_id
        if status_effects is not None:
            data["status_effects"] = status_effects
        if expires_at is not None:
            data["expires_at"] = expires_at
        if spawn_group_id is not None:
            data["spawn_group_id"] = spawn_group_id
        if loot_group_id is not None:
            data["loot_group_id"] = loot_group_id
        if encounter_id is not None:
            data["encounter_id"] = encounter_id
        self.data_layer.save_entity_instance(instance_id, data)
        return instance_id

    def place_entity(
        self,
        instance_id: str,
        room_id: str,
        *,
        range_band: Optional[str] = None,
        engaged_target_id: Optional[str] = None,
        leash_room_id: Optional[str] = None,
    ) -> None:
        """Set entity position (R8 movement / pursuit)."""
        if not self._enabled() or not instance_id:
            return
        kwargs = {}
        if range_band is not None:
            kwargs["range_band"] = range_band
        if engaged_target_id is not None:
            kwargs["engaged_target_id"] = engaged_target_id
        if leash_room_id is not None:
            kwargs["leash_room_id"] = leash_room_id
        self.data_layer.save_entity_position(instance_id, room_id, **kwargs)

    def remove_entity_from_world(self, instance_id: str, delete_instance: bool = False) -> None:
        """
        Remove entity from world (delete position). Optionally delete the instance record (B2 death).
        """
        if not self._enabled() or not instance_id:
            return
        self.data_layer.delete_entity_position(instance_id)
        if delete_instance:
            self.data_layer.delete_entity_instance(instance_id)

    def get_entity_instance(self, instance_id: str) -> Optional[Dict]:
        """Load a single entity instance by id."""
        if not self._enabled():
            return None
        return self.data_layer.load_entity_instance(instance_id)

    def get_entity_position(self, instance_id: str) -> Optional[Dict]:
        """Load position for one instance."""
        if not self._enabled():
            return None
        return self.data_layer.load_entity_position(instance_id)

    def maybe_reset_room(self, room_id: str) -> Dict:
        """
        If next_reset_at has passed, refresh room seed and reset timers (B5).
        Returns current room_state (after optional reset).
        """
        if not self._enabled():
            return {}
        state = self.get_or_create_room_state(room_id)
        now = _now_ts()
        if state.get("next_reset_at", 0) <= now:
            state["last_reset_at"] = now
            state["next_reset_at"] = now + DEFAULT_RESET_SECONDS
            state["seed"] = int(now) % (2 ** 31)
            state["state_version"] = state.get("state_version", 1) + 1
            self.data_layer.save_room_state(room_id, state)
        return state
