"""Tests for inventory commands (get, drop, equip, etc.)."""

import unittest
from tests.test_helpers import MockGame, MockPlayer, MockRoom, MockRuntimeState, make_mock_items


class TestGetCommand(unittest.TestCase):
    """Tests for get_command including corpse loot fallback."""

    def setUp(self):
        self.room = MockRoom()
        self.room.items = []
        self.player = MockPlayer()
        self.game = MockGame(
            rooms={self.room.room_id: self.room},
            items=make_mock_items(),
        )

    def test_get_no_args_shows_error(self):
        from commands.inventory import get_command
        get_command(self.game, self.player, [])
        self.assertTrue(any("Get what?" in msg for _, msg in self.game._messages))

    def test_get_item_from_room(self):
        from commands.inventory import get_command
        self.room.items = ["stick"]
        get_command(self.game, self.player, ["stick"])
        self.assertIn("stick", self.player.inventory)
        self.assertNotIn("stick", self.room.items)

    def test_get_item_not_found(self):
        from commands.inventory import get_command
        get_command(self.game, self.player, ["sword"])
        self.assertTrue(any("don't see" in msg.lower() for _, msg in self.game._messages))

    def test_get_from_corpse_explicit(self):
        """Test 'take stick from corpse' syntax."""
        from commands.inventory import get_command
        rt = MockRuntimeState()
        corpse = {
            "entity_type": "corpse",
            "name": "corpse of a goblin",
            "instance_id": "corpse_1",
            "loot": {
                "rolled": True,
                "coins": 0,
                "items": [{"item_id": "stick", "count": 1}],
            },
        }
        rt.add_entity_to_room(self.room.room_id, corpse)
        self.game.runtime_state = rt

        get_command(self.game, self.player, ["stick", "from", "corpse"])
        self.assertIn("stick", self.player.inventory)

    def test_get_from_corpse_implicit(self):
        """Test 'take stick' finds item in corpse when not in room."""
        from commands.inventory import get_command
        rt = MockRuntimeState()
        corpse = {
            "entity_type": "corpse",
            "name": "corpse of a goblin",
            "instance_id": "corpse_1",
            "loot": {
                "rolled": True,
                "coins": 0,
                "items": [{"item_id": "stick", "count": 1}],
            },
        }
        rt.add_entity_to_room(self.room.room_id, corpse)
        self.game.runtime_state = rt

        get_command(self.game, self.player, ["stick"])
        self.assertIn("stick", self.player.inventory)

    def test_get_unknown_room(self):
        from commands.inventory import get_command
        self.player.room_id = "nonexistent"
        get_command(self.game, self.player, ["stick"])
        self.assertTrue(any("unknown location" in msg.lower() for _, msg in self.game._messages))


class TestDropCommand(unittest.TestCase):
    """Tests for drop_command."""

    def setUp(self):
        self.room = MockRoom()
        self.room.items = []
        self.player = MockPlayer()
        self.player.inventory = ["stick"]
        self.game = MockGame(
            rooms={self.room.room_id: self.room},
            items=make_mock_items(),
        )

    def test_drop_no_args_shows_error(self):
        from commands.inventory import drop_command
        drop_command(self.game, self.player, [])
        self.assertTrue(any("Drop what?" in msg for _, msg in self.game._messages))

    def test_drop_item(self):
        from commands.inventory import drop_command
        drop_command(self.game, self.player, ["stick"])
        self.assertNotIn("stick", self.player.inventory)
        self.assertIn("stick", self.room.items)

    def test_drop_item_not_in_inventory(self):
        from commands.inventory import drop_command
        drop_command(self.game, self.player, ["sword"])
        self.assertTrue(any("don't have" in msg.lower() for _, msg in self.game._messages))


class TestEquipCommand(unittest.TestCase):
    """Tests for equip_command."""

    def setUp(self):
        self.room = MockRoom()
        self.player = MockPlayer()
        self.player.equipped = {"weapon": None, "armor": None}

        # Create a weapon item with all required methods
        class WeaponItem:
            def __init__(self):
                self.name = "Iron Sword"
                self.item_type = "weapon"
                self.equip_slot = "weapon"
                self.hands = 1
                self.damage_min = 5
                self.damage_max = 10
                self.damage_type = "slashing"
                self.crit_chance = 0.1
                self.current_durability = 50
                self.max_durability = 50
            def is_weapon(self):
                return True
            def is_armor(self):
                return False
            def get_effective_damage(self):
                return (self.damage_min, self.damage_max)
            def get_effective_crit_chance(self):
                return self.crit_chance
            def get_current_durability(self):
                return self.current_durability

        self.player.inventory = ["iron_sword"]
        self.game = MockGame(
            rooms={self.room.room_id: self.room},
            items={"iron_sword": WeaponItem()},
        )

    def test_equip_no_args_shows_usage(self):
        from commands.inventory import equip_command
        equip_command(self.game, self.player, [])
        self.assertTrue(any("Equip what?" in msg for _, msg in self.game._messages))

    def test_equip_weapon(self):
        from commands.inventory import equip_command
        equip_command(self.game, self.player, ["iron", "sword"])
        self.assertEqual(self.player.equipped.get("weapon"), "iron_sword")

    def test_equip_item_not_in_inventory(self):
        from commands.inventory import equip_command
        self.player.inventory = []
        equip_command(self.game, self.player, ["iron", "sword"])
        self.assertTrue(any("don't have" in msg.lower() for _, msg in self.game._messages))


class TestUnequipCommand(unittest.TestCase):
    """Tests for unequip_command."""

    def setUp(self):
        self.room = MockRoom()
        self.player = MockPlayer()
        self.player.equipped = {"weapon": "iron_sword", "armor": None}
        self.player.inventory = ["iron_sword"]

        class WeaponItem:
            def __init__(self):
                self.name = "Iron Sword"
                self.item_type = "weapon"

        self.game = MockGame(
            rooms={self.room.room_id: self.room},
            items={"iron_sword": WeaponItem()},
        )

    def test_unequip_no_args_shows_usage(self):
        from commands.inventory import unequip_command
        unequip_command(self.game, self.player, [])
        self.assertTrue(any("Unequip what?" in msg or "unequip <slot>" in msg.lower() for _, msg in self.game._messages))

    def test_unequip_weapon(self):
        from commands.inventory import unequip_command
        unequip_command(self.game, self.player, ["weapon"])
        self.assertIsNone(self.player.equipped.get("weapon"))

    def test_unequip_empty_slot(self):
        from commands.inventory import unequip_command
        # Remove weapon from equipped entirely to test "slot not in equipped"
        del self.player.equipped["weapon"]
        unequip_command(self.game, self.player, ["weapon"])
        # Check for message about nothing equipped
        self.assertTrue(any(
            "don't have anything equipped" in msg.lower()
            for _, msg in self.game._messages
        ))


if __name__ == "__main__":
    unittest.main()
