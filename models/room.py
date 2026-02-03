"""Room model for MUD world state."""


class Room:
    def __init__(self, room_id, name, description):
        self.room_id = room_id
        self.name = name
        self.description = description
        self.exits = {}
        self.items = []
        self.npcs = []
        self.players = set()
        self.flags = []
        self.combat_tags = []  # open, cramped, slick, obscured, elevated
        self.spawn_groups = []
        self.zone = None
        self.interactables = []
        self.hidden_exits = []
        self.region_id = None
        self.weather_exposure = None
        self.ambient_lines = []
        self.enter_flavor = []

    def to_dict(self):
        return {
            "room_id": self.room_id,
            "name": self.name,
            "description": self.description,
            "exits": self.exits,
            "items": self.items,
            "npcs": self.npcs,
            "flags": self.flags,
            "combat_tags": self.combat_tags,
            "spawn_groups": getattr(self, "spawn_groups", []),
            "zone": getattr(self, "zone", None),
            "interactables": getattr(self, "interactables", []),
            "hidden_exits": getattr(self, "hidden_exits", []),
            "region_id": getattr(self, "region_id", None),
            "weather_exposure": getattr(self, "weather_exposure", None),
            "ambient_lines": getattr(self, "ambient_lines", []),
            "enter_flavor": getattr(self, "enter_flavor", []),
        }

    def from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
