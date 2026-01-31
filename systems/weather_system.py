"""Regional weather system (docs/weather_system.md)."""

import os
import json
import random
import time


class WeatherService:
    """Manages per-region weather state, transitions, overlays, and light mechanical effects."""

    def __init__(self, firebase=None, world_time=None, use_firebase=False):
        self.firebase = firebase
        self.world_time = world_time
        self.use_firebase = use_firebase
        self.region_weather = {}
        self.weather_transitions = {}
        self.weather_overlays = {}
        self.weather_change_messages = {}

    def load(self):
        """Load regional weather state from Firebase and transitions/overlays from contributions/weather/."""
        if self.use_firebase and self.firebase:
            try:
                data = self.firebase.load_config("region_weather")
                if data and isinstance(data, dict):
                    self.region_weather = data
                    print(f"Loaded weather for {len(self.region_weather)} regions from Firebase")
            except Exception as e:
                print(f"Error loading region_weather from Firebase: {e}")
        weather_dir = "contributions/weather"
        if os.path.exists(weather_dir):
            for name, attr in [
                ("transitions.json", "weather_transitions"),
                ("overlays.json", "weather_overlays"),
                ("change_messages.json", "weather_change_messages"),
            ]:
                path = os.path.join(weather_dir, name)
                if os.path.exists(path):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        setattr(self, attr, data)
                    except Exception as e:
                        print(f"Error loading {name}: {e}")
        if not self.weather_transitions:
            self.weather_transitions = {
                "clear": {"clear": 50, "fog": 30, "wind": 20},
                "fog": {"fog": 40, "clear": 40, "squall": 20},
                "wind": {"wind": 50, "clear": 30, "squall": 20},
                "squall": {"wind": 50, "clear": 50},
                "cold_snap": {"cold_snap": 40, "clear": 60},
                "salt_rain": {"salt_rain": 50, "clear": 50},
            }
        if not self.weather_overlays:
            self.weather_overlays = {
                "clear": {"outdoor": "The air is still and clear.", "sheltered": "The sky is clear beyond shelter.", "coastal": "Clear skies over the water."},
                "fog": {"outdoor": "A cold fog crawls through, muffling sound and swallowing distant shapes.", "sheltered": "Fog drifts past, dimming the world beyond.", "coastal": "Sea fog rolls in, thick and clammy."},
                "wind": {"outdoor": "The wind blows steadily, tugging at clothes and foliage.", "sheltered": "Wind whistles past your shelter.", "coastal": "Wind whips off the water, sharp and salt-tanged."},
                "squall": {"outdoor": "A squall drives rain and wind; visibility drops.", "sheltered": "A squall batters the world outside.", "coastal": "A squall whips the coast; spray and rain sting."},
                "cold_snap": {"outdoor": "A cold snap bites; breath fogs and fingers numb.", "sheltered": "Cold seeps in despite shelter.", "coastal": "Bitter wind off the water cuts through."},
                "salt_rain": {"outdoor": "Salt rain falls, stinging skin and metal.", "sheltered": "Salt rain drums beyond shelter.", "coastal": "Salt rain and spray lash the coast."},
            }
        if not self.weather_change_messages:
            self.weather_change_messages = {
                "clear": "The weather clears.",
                "fog": "Fog rolls in, thickening the air.",
                "wind": "The wind rises.",
                "squall": "A squall sweeps in.",
                "cold_snap": "A cold snap descends.",
                "salt_rain": "Salt rain begins to fall.",
            }

    def get_region_weather(self, region_id):
        """Return current weather state for region; init with clear if missing."""
        if not region_id:
            return None
        now = self.world_time.get_world_seconds() if self.world_time else int(time.time())
        if region_id not in self.region_weather:
            self.region_weather[region_id] = {
                "region_id": region_id,
                "weather_type": "clear",
                "intensity": 0,
                "started_at": now,
                "next_change_at": now + 900,
                "seed": random.randint(1, 2**31 - 1),
            }
            self._save_region_weather()
        return self.region_weather[region_id]

    def _save_region_weather(self):
        """Persist region_weather to Firebase."""
        if self.use_firebase and self.firebase:
            try:
                self.firebase.save_config("region_weather", self.region_weather)
            except Exception as e:
                print(f"Error saving region_weather to Firebase: {e}")

    def _roll_next_weather(self, region_id):
        """Roll next weather from transition table; set next_change_at. Returns (old_type, new_type)."""
        state = self.get_region_weather(region_id)
        old_type = state["weather_type"]
        table = self.weather_transitions.get(old_type, {"clear": 100})
        choices = list(table.keys())
        weights = [table[c] for c in choices]
        new_type = random.choices(choices, weights=weights, k=1)[0]
        now = self.world_time.get_world_seconds() if self.world_time else int(time.time())
        duration = random.randint(600, 1800)
        state["weather_type"] = new_type
        state["intensity"] = min(3, state.get("intensity", 0) + (1 if new_type != "clear" else -1))
        state["intensity"] = max(0, state["intensity"])
        state["started_at"] = now
        state["next_change_at"] = now + duration
        self._save_region_weather()
        return (old_type, new_type)

    def maybe_update_region_weather(self, region_id, get_room, get_players, send_to_player):
        """If now >= next_change_at, roll new weather and notify players in region."""
        if not region_id or not self.world_time:
            return
        state = self.get_region_weather(region_id)
        now = self.world_time.get_world_seconds()
        if now < state.get("next_change_at", 0):
            return
        old_type, new_type = self._roll_next_weather(region_id)
        if old_type == new_type:
            return
        msg = self.weather_change_messages.get(new_type, "The weather changes.")
        players = get_players() if callable(get_players) else get_players
        for name, player in (players.items() if isinstance(players, dict) else []):
            r = get_room(getattr(player, "room_id", None)) if get_room else None
            if r and getattr(r, "region_id", None) == region_id:
                send_to_player(player, msg)

    def get_weather_overlay(self, region_id, weather_exposure):
        """Return short overlay line for current regional weather and exposure, or None if indoor/none."""
        if weather_exposure == "indoor" or not region_id:
            return None
        state = self.get_region_weather(region_id)
        wtype = state.get("weather_type", "clear")
        exposure = weather_exposure if weather_exposure in ("sheltered", "outdoor", "coastal") else "outdoor"
        overlays = self.weather_overlays
        if isinstance(overlays, dict) and wtype in overlays:
            row = overlays[wtype] if isinstance(overlays[wtype], dict) else {}
            return row.get(exposure) or row.get("outdoor")
        return None

    def get_weather_modifier_for_room(self, room_id, effect_type, get_room):
        """Return weather modifier for room. Indoor rooms return 0.
        effect_type: 'ranged_accuracy_far' (fog), 'disengage_failure' (squall), 'durability_loss' (salt_rain), 'stamina_drain' (cold_snap).
        """
        room = get_room(room_id) if room_id and get_room else None
        if not room:
            return 0
        exposure = getattr(room, "weather_exposure", None)
        if exposure == "indoor":
            return 0
        region_id = getattr(room, "region_id", None)
        if not region_id:
            return 0
        state = self.get_region_weather(region_id)
        wtype = state.get("weather_type", "clear")
        intensity = max(0, min(3, state.get("intensity", 0)))
        scale = (intensity + 1) / 4.0
        if effect_type == "ranged_accuracy_far" and wtype == "fog":
            return int(-15 * scale)
        if effect_type == "disengage_failure" and wtype == "squall":
            return int(20 * scale)
        if effect_type == "durability_loss" and wtype == "salt_rain":
            return scale
        if effect_type == "stamina_drain" and wtype == "cold_snap" and exposure in ("outdoor", "coastal"):
            return int(2 * scale)
        return 0
