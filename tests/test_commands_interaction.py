"""Tests for interaction commands (dig, etc.)."""

import unittest
from unittest.mock import patch
from tests.test_helpers import MockGame, MockPlayer, MockRoom, make_mock_items


class MockRoomWithInteractables(MockRoom):
    """Room with interactables for dig testing."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interactables = []


class TestDigCommand(unittest.TestCase):
    """Tests for dig_command."""

    def setUp(self):
        self.room = MockRoomWithInteractables()
        self.player = MockPlayer()
        self.player.attributes = {"physical": 10}
        self.player.equipped = {"weapon": None}
        self.player.interactable_searches = {}
        self.player.inventory = []

        self.game = MockGame(
            rooms={self.room.room_id: self.room},
            items=make_mock_items(),
        )

    def test_dig_no_target_shows_error(self):
        from commands.interaction import dig_command
        dig_command(self.game, self.player, [])
        self.assertTrue(any("dig what" in msg.lower() for _, msg in self.game._messages))

    def test_dig_no_interactable_shows_error(self):
        from commands.interaction import dig_command
        dig_command(self.game, self.player, ["mound"])
        self.assertTrue(any("can't dig" in msg.lower() for _, msg in self.game._messages))

    def test_dig_requires_flag(self):
        """Test dig action requires a flag to be set."""
        from commands.interaction import dig_command

        self.room.interactables = [{
            "object_id": "mound",
            "name": "mound of dirt",
            "keywords": ["mound", "dirt"],
            "actions": {
                "dig": {
                    "required_flag": "heard_rumor",
                    "no_flag_text": "Nothing special here.",
                    "attribute": "physical",
                    "difficulty": 10,
                }
            }
        }]

        # Player doesn't have the flag
        self.player.has_flag = lambda name: False

        dig_command(self.game, self.player, ["mound"])
        self.assertTrue(any("Nothing special" in msg for _, msg in self.game._messages))

    def test_dig_requires_tool(self):
        """Test dig action requires equipped tool."""
        from commands.interaction import dig_command

        self.room.interactables = [{
            "object_id": "mound",
            "name": "mound of dirt",
            "keywords": ["mound", "dirt"],
            "actions": {
                "dig": {
                    "requires_equipped_tag": "shovel",
                    "no_tool_text": "You need a shovel.",
                    "attribute": "physical",
                    "difficulty": 10,
                }
            }
        }]

        dig_command(self.game, self.player, ["mound"])
        self.assertTrue(any("need a shovel" in msg.lower() for _, msg in self.game._messages))

    def test_dig_already_done(self):
        """Test dig action respects limit_per_player."""
        from commands.interaction import dig_command

        self.room.interactables = [{
            "object_id": "mound",
            "name": "mound of dirt",
            "keywords": ["mound", "dirt"],
            "actions": {
                "dig": {
                    "attribute": "physical",
                    "difficulty": 10,
                    "limit_per_player": 1,
                    "already_done_text": "You've already dug here.",
                }
            }
        }]

        # Simulate having already dug
        self.player.interactable_searches = {"dig_mound": {"count": 1, "last_at": 0}}

        dig_command(self.game, self.player, ["mound"])
        self.assertTrue(any("already dug" in msg.lower() for _, msg in self.game._messages))

    @patch("random.randint", return_value=1)  # Always succeed (roll 1 <= 50%)
    def test_dig_success_gives_item(self, mock_rand):
        """Test successful dig gives item."""
        from commands.interaction import dig_command

        self.room.interactables = [{
            "object_id": "mound",
            "name": "mound of dirt",
            "keywords": ["mound", "dirt"],
            "actions": {
                "dig": {
                    "attribute": "physical",
                    "difficulty": 10,
                    "success": {
                        "gives_item": "stick",
                        "success_text": "You dig up a stick!",
                    }
                }
            }
        }]

        dig_command(self.game, self.player, ["mound"])
        self.assertIn("stick", self.player.inventory)

    @patch("random.randint", return_value=100)  # Always fail (roll 100 > any chance)
    def test_dig_failure(self, mock_rand):
        """Test failed dig shows fail text."""
        from commands.interaction import dig_command

        self.room.interactables = [{
            "object_id": "mound",
            "name": "mound of dirt",
            "keywords": ["mound", "dirt"],
            "actions": {
                "dig": {
                    "attribute": "physical",
                    "difficulty": 10,
                    "fail_text": "You dig but find nothing.",
                }
            }
        }]

        dig_command(self.game, self.player, ["mound"])
        self.assertTrue(any("find nothing" in msg.lower() for _, msg in self.game._messages))
        self.assertEqual(len(self.player.inventory), 0)

    def test_dig_with_tool_equipped(self):
        """Test dig works when correct tool is equipped."""
        from commands.interaction import dig_command

        # Create a shovel item with tags
        class ShovelItem:
            def __init__(self):
                self.name = "Basic Shovel"
                self.tags = ["tool", "shovel"]

        self.game._items["basic_shovel"] = ShovelItem()
        self.player.equipped = {"weapon": "basic_shovel"}

        self.room.interactables = [{
            "object_id": "mound",
            "name": "mound of dirt",
            "keywords": ["mound", "dirt"],
            "actions": {
                "dig": {
                    "requires_equipped_tag": "shovel",
                    "no_tool_text": "You need a shovel.",
                    "attribute": "physical",
                    "difficulty": 10,
                    "fail_text": "You dig but find nothing.",
                }
            }
        }]

        with patch("random.randint", return_value=100):  # Force failure to avoid item issues
            dig_command(self.game, self.player, ["mound"])

        # Should NOT get "need a shovel" message
        self.assertFalse(any("need a shovel" in msg.lower() for _, msg in self.game._messages))


class TestDigCommandUnknownRoom(unittest.TestCase):
    """Test dig in unknown room."""

    def test_dig_unknown_room(self):
        from commands.interaction import dig_command
        player = MockPlayer()
        player.room_id = "nonexistent"
        game = MockGame()
        dig_command(game, player, ["mound"])
        self.assertTrue(any("unknown location" in msg.lower() for _, msg in game._messages))


if __name__ == "__main__":
    unittest.main()
