"""Shared mocks and helpers for tests (used by both unittest and pytest)."""


class MockPlayer:
    """Minimal player for command tests."""
    def __init__(self, name="TestPlayer", room_id="room_1"):
        self.name = name
        self.room_id = room_id
        self.inventory = []
        self.gold = 0


class MockRoom:
    """Minimal room for command tests."""
    def __init__(self, room_id="room_1", name="Test Room", description="A test room."):
        self.room_id = room_id
        self.name = name
        self.description = description


class MockGame:
    """Minimal game object for command tests; attributes can be overridden."""
    def __init__(self, rooms=None, items=None, runtime_state=None):
        self._rooms = dict(rooms or {})
        self._items = dict(items or {})
        self.runtime_state = runtime_state
        self._messages = []
        self._broadcasts = []

    def get_room(self, room_id):
        return self._rooms.get(room_id)

    @property
    def items(self):
        return self._items

    def send_to_player(self, player, msg):
        self._messages.append((player.name, msg))

    def broadcast_to_room(self, room_id, msg, exclude_name=None):
        self._broadcasts.append((room_id, msg, exclude_name))

    def format_item(self, name):
        return name

    def format_success(self, msg):
        return msg

    def format_header(self, msg):
        return msg

    def format_error(self, msg):
        return msg


class MockRuntimeState:
    """Minimal runtime state for corpse/loot tests."""
    def __init__(self):
        self._entities_by_room = {}
        self._instances = {}
        self._next_id = 1
        self.remove_calls = []
        self.update_calls = []

    def get_entities_in_room(self, room_id):
        return list(self._entities_by_room.get(room_id, []))

    def add_entity_to_room(self, room_id, inst):
        inst = dict(inst)
        if "instance_id" not in inst:
            inst["instance_id"] = f"inst_{self._next_id}"
            self._next_id += 1
        self._instances[inst["instance_id"]] = inst
        self._entities_by_room.setdefault(room_id, []).append(inst)
        return inst["instance_id"]

    def update_entity_instance(self, instance_id, **kwargs):
        self.update_calls.append((instance_id, kwargs))
        inst = self._instances.get(instance_id)
        if inst:
            inst.update(kwargs)
        for room_id, entities in self._entities_by_room.items():
            for e in entities:
                if e.get("instance_id") == instance_id:
                    e.update(kwargs)
                    break

    def remove_entity_from_world(self, instance_id, delete_instance=True):
        self.remove_calls.append((instance_id, delete_instance))
        for room_id, entities in self._entities_by_room.items():
            self._entities_by_room[room_id] = [e for e in entities if e.get("instance_id") != instance_id]
        if delete_instance and instance_id in self._instances:
            del self._instances[instance_id]


def make_mock_items():
    """Item id -> object with .name."""
    class Item:
        def __init__(self, name):
            self.name = name
    return {
        "stick": Item("stick"),
        "gold_coin": Item("gold coin"),
        "potion": Item("healing potion"),
    }


def make_runtime_with_corpse(room_id="room_1"):
    """Runtime state with one corpse in the given room."""
    rt = MockRuntimeState()
    corpse = {
        "entity_type": "corpse",
        "name": "corpse of a goblin",
        "instance_id": "corpse_1",
        "loot": {
            "rolled": True,
            "coins": 5,
            "items": [{"item_id": "stick", "count": 1}, {"item_id": "potion", "count": 2}],
        },
        "ownership": {"allowed_player_ids": ["TestPlayer"], "expires_at": 999999999},
    }
    rt.add_entity_to_room(room_id, corpse)
    return rt
