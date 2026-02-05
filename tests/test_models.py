"""Tests for data models (Item, Room, Player, etc.)."""

import unittest


class TestItemModel(unittest.TestCase):
    """Tests for Item model."""

    def test_item_creation(self):
        from models.item import Item
        item = Item("sword_1", "Iron Sword", "A basic iron sword", "weapon")
        self.assertEqual(item.item_id, "sword_1")
        self.assertEqual(item.name, "Iron Sword")
        self.assertEqual(item.description, "A basic iron sword")
        self.assertEqual(item.item_type, "weapon")

    def test_is_weapon(self):
        from models.item import Item
        weapon = Item("sword", "Sword", "A sword", "weapon")
        self.assertTrue(weapon.is_weapon())

        melee = Item("axe", "Axe", "An axe", "item")
        melee.category = "Melee"
        self.assertTrue(melee.is_weapon())

        potion = Item("potion", "Potion", "A potion", "consumable")
        self.assertFalse(potion.is_weapon())

    def test_is_armor(self):
        from models.item import Item
        armor = Item("vest", "Vest", "A vest", "armor")
        self.assertTrue(armor.is_armor())

        armor2 = Item("helm", "Helm", "A helm", "item")
        armor2.armor_type = "light"
        self.assertTrue(armor2.is_armor())

        weapon = Item("sword", "Sword", "A sword", "weapon")
        self.assertFalse(weapon.is_armor())

    def test_get_effective_damage(self):
        from models.item import Item
        weapon = Item("sword", "Sword", "A sword", "weapon")
        weapon.damage_min = 5
        weapon.damage_max = 10
        self.assertEqual(weapon.get_effective_damage(), (5, 10))

    def test_get_effective_crit_chance(self):
        from models.item import Item
        weapon = Item("sword", "Sword", "A sword", "weapon")
        weapon.crit_chance = 0.15
        self.assertEqual(weapon.get_effective_crit_chance(), 0.15)

    def test_durability(self):
        from models.item import Item
        weapon = Item("sword", "Sword", "A sword", "weapon")
        weapon.max_durability = 100

        # Initially uses max_durability
        self.assertEqual(weapon.get_current_durability(), 100)

        # After reducing
        weapon.reduce_durability(10)
        self.assertEqual(weapon.get_current_durability(), 90)

        # Reduce to zero
        broken = weapon.reduce_durability(100)
        self.assertTrue(broken)
        self.assertEqual(weapon.get_current_durability(), 0)

    def test_armor_durability(self):
        from models.item import Item
        armor = Item("vest", "Vest", "A vest", "armor")
        armor.max_durability = 50

        # Reduce armor HP
        armor.reduce_armor_hp(20)
        self.assertEqual(armor.current_durability, 30)

        # Break armor
        broken = armor.reduce_armor_hp(50)
        self.assertTrue(broken)
        self.assertEqual(armor.current_durability, 0)

    def test_get_armor_slot(self):
        from models.item import Item
        armor = Item("vest", "Vest", "A vest", "armor")

        # With explicit slot
        armor.slot = "chest"
        self.assertEqual(armor.get_armor_slot(), "chest")

        # With armor_slots list
        armor.slot = None
        armor.armor_slots = ["Body"]
        self.assertEqual(armor.get_armor_slot(), "chest")

        armor.armor_slots = ["Offhand"]
        self.assertEqual(armor.get_armor_slot(), "shield")

        armor.armor_slots = ["Head"]
        self.assertEqual(armor.get_armor_slot(), "head")

        # Default
        armor.armor_slots = []
        self.assertEqual(armor.get_armor_slot(), "chest")

    def test_get_dr_for_damage_type(self):
        from models.item import Item
        armor = Item("vest", "Vest", "A vest", "armor")
        armor.damage_reduction = {"slashing": 5, "piercing": 3}
        armor.current_durability = 50

        self.assertEqual(armor.get_dr_for_damage_type("slashing"), 5)
        self.assertEqual(armor.get_dr_for_damage_type("piercing"), 3)
        self.assertEqual(armor.get_dr_for_damage_type("fire"), 0)

        # Broken armor gives no DR
        armor.current_durability = 0
        self.assertEqual(armor.get_dr_for_damage_type("slashing"), 0)

    def test_to_dict(self):
        from models.item import Item
        item = Item("sword", "Iron Sword", "A sword", "weapon")
        item.value = 100
        item.damage_min = 5
        item.damage_max = 10

        data = item.to_dict()
        self.assertEqual(data["item_id"], "sword")
        self.assertEqual(data["name"], "Iron Sword")
        self.assertEqual(data["value"], 100)

    def test_from_dict(self):
        from models.item import Item
        item = Item("", "", "", "item")
        item.from_dict({
            "item_id": "potion",
            "name": "Health Potion",
            "description": "Heals you",
            "value": 50,
        })
        self.assertEqual(item.item_id, "potion")
        self.assertEqual(item.name, "Health Potion")
        self.assertEqual(item.value, 50)

    def test_tags(self):
        from models.item import Item
        item = Item("shovel", "Basic Shovel", "A shovel", "weapon")
        item.tags = ["tool", "shovel"]
        self.assertIn("shovel", item.tags)
        self.assertIn("tool", item.tags)


class TestRoomModel(unittest.TestCase):
    """Tests for Room model."""

    def test_room_creation(self):
        from models.room import Room
        room = Room("tavern", "The Black Anchor", "A cozy tavern.")
        self.assertEqual(room.room_id, "tavern")
        self.assertEqual(room.name, "The Black Anchor")
        self.assertEqual(room.description, "A cozy tavern.")

    def test_room_exits(self):
        from models.room import Room
        room = Room("tavern", "Tavern", "A tavern.")
        room.exits = {"north": "street", "south": "cellar"}
        self.assertEqual(room.exits["north"], "street")
        self.assertIn("south", room.exits)

    def test_room_items(self):
        from models.room import Room
        room = Room("tavern", "Tavern", "A tavern.")
        room.items = ["mug", "candle"]
        self.assertIn("mug", room.items)

    def test_room_players(self):
        from models.room import Room
        room = Room("tavern", "Tavern", "A tavern.")
        room.players = set()
        room.players.add("Player1")
        self.assertIn("Player1", room.players)


class TestPlayerModel(unittest.TestCase):
    """Tests for Player model."""

    def test_player_creation(self):
        from models.player import Player
        player = Player("TestPlayer", None, None)
        self.assertEqual(player.name, "TestPlayer")

    def test_player_inventory(self):
        from models.player import Player
        player = Player("TestPlayer", None, None)
        player.inventory.append("sword")
        self.assertIn("sword", player.inventory)

    def test_player_equipped(self):
        from models.player import Player
        player = Player("TestPlayer", None, None)
        player.equipped["weapon"] = "iron_sword"
        self.assertEqual(player.equipped["weapon"], "iron_sword")

    def test_player_flags(self):
        from models.player import Player
        player = Player("TestPlayer", None, None)
        if hasattr(player, "set_flag") and hasattr(player, "has_flag"):
            player.set_flag("test_flag")
            self.assertTrue(player.has_flag("test_flag"))
            player.set_flag("test_flag", False)
            self.assertFalse(player.has_flag("test_flag"))

    def test_player_attributes(self):
        from models.player import Player
        player = Player("TestPlayer", None, None)
        self.assertIn("physical", player.attributes)
        self.assertIn("mental", player.attributes)
        self.assertEqual(player.attributes["physical"], 10)

    def test_player_health(self):
        from models.player import Player
        player = Player("TestPlayer", None, None)
        self.assertEqual(player.health, 100)
        self.assertEqual(player.max_health, 100)


if __name__ == "__main__":
    unittest.main()
