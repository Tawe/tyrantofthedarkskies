"""Unit tests for commands.loot."""

import unittest
from unittest.mock import patch

from commands.loot import (
    can_loot_corpse,
    maybe_remove_empty_corpse,
    handle_take_from_corpse,
    loot_command,
)
from tests.test_helpers import (
    MockPlayer,
    MockRoom,
    MockGame,
    MockRuntimeState,
    make_mock_items,
    make_runtime_with_corpse,
)


class TestCanLootCorpse(unittest.TestCase):
    """Tests for can_loot_corpse()."""

    def setUp(self):
        self.game = MockGame(rooms={"room_1": MockRoom()}, items=make_mock_items())
        self.player = MockPlayer()

    def test_no_ownership_allows_loot(self):
        corpse = {"loot": {}, "ownership": {}}
        self.assertTrue(can_loot_corpse(self.game, self.player, corpse))

    def test_expired_ownership_allows_loot(self):
        with patch("commands.loot.time") as mtime:
            mtime.time.return_value = 2000.0
            corpse = {"ownership": {"expires_at": 1000.0, "allowed_player_ids": ["Other"]}}
            self.assertTrue(can_loot_corpse(self.game, self.player, corpse))

    def test_allowed_player_can_loot(self):
        with patch("commands.loot.time") as mtime:
            mtime.time.return_value = 500.0
            corpse = {"ownership": {"expires_at": 1000.0, "allowed_player_ids": ["TestPlayer"]}}
            self.assertTrue(can_loot_corpse(self.game, self.player, corpse))

    def test_other_player_cannot_loot_within_window(self):
        with patch("commands.loot.time") as mtime:
            mtime.time.return_value = 500.0
            corpse = {"ownership": {"expires_at": 1000.0, "allowed_player_ids": ["Killer"]}}
            self.assertFalse(can_loot_corpse(self.game, self.player, corpse))


class TestMaybeRemoveEmptyCorpse(unittest.TestCase):
    """Tests for maybe_remove_empty_corpse()."""

    def setUp(self):
        self.game = MockGame(rooms={"room_1": MockRoom()}, items=make_mock_items())

    def test_does_not_remove_if_coins_remain(self):
        rt = type("RT", (), {})()
        rt.remove_entity_from_world = lambda i, d: self.fail("should not remove")
        self.game.runtime_state = rt
        corpse = {"instance_id": "c1", "loot": {"coins": 1, "items": []}}
        maybe_remove_empty_corpse(self.game, corpse)

    def test_does_not_remove_if_items_remain(self):
        calls = []
        rt = type("RT", (), {})()
        rt.remove_entity_from_world = lambda i, d: calls.append((i, d))
        self.game.runtime_state = rt
        corpse = {"instance_id": "c1", "loot": {"coins": 0, "items": [{"item_id": "x", "count": 1}]}}
        maybe_remove_empty_corpse(self.game, corpse)
        self.assertEqual(len(calls), 0)

    def test_removes_when_empty(self):
        calls = []
        rt = type("RT", (), {})()
        rt.remove_entity_from_world = lambda i, delete_instance=True: calls.append((i, delete_instance))
        self.game.runtime_state = rt
        corpse = {"instance_id": "c1", "loot": {"coins": 0, "items": []}}
        maybe_remove_empty_corpse(self.game, corpse)
        self.assertEqual(calls, [("c1", True)])

    def test_no_runtime_state_does_not_crash(self):
        self.game.runtime_state = None
        corpse = {"instance_id": "c1", "loot": {"coins": 0, "items": []}}
        maybe_remove_empty_corpse(self.game, corpse)


class TestHandleTakeFromCorpse(unittest.TestCase):
    """Tests for handle_take_from_corpse()."""

    def setUp(self):
        self.room = MockRoom()
        self.player = MockPlayer()
        self.items = make_mock_items()
        self.game = MockGame(rooms={"room_1": self.room}, items=self.items)

    def test_returns_false_when_no_runtime_state(self):
        self.game.runtime_state = None
        self.assertFalse(
            handle_take_from_corpse(self.game, self.player, self.room, "stick", "corpse")
        )

    def test_returns_false_when_no_corpse_match(self):
        self.game.runtime_state = MockRuntimeState()
        self.assertFalse(
            handle_take_from_corpse(self.game, self.player, self.room, "stick", "dragon")
        )

    def test_denies_when_not_allowed_to_loot(self):
        rt = MockRuntimeState()
        corpse = {
            "entity_type": "corpse",
            "name": "corpse of goblin",
            "instance_id": "c1",
            "loot": {"coins": 0, "items": [{"item_id": "stick", "count": 1}]},
            "ownership": {"allowed_player_ids": ["Other"], "expires_at": 999999999},
        }
        rt.add_entity_to_room(self.room.room_id, corpse)
        self.game.runtime_state = rt
        with patch("commands.loot.time") as mtime:
            mtime.time.return_value = 0.0
            result = handle_take_from_corpse(self.game, self.player, self.room, "stick", "goblin")
        self.assertTrue(result)
        self.assertTrue(any("hesitate" in msg for _, msg in self.game._messages))

    def test_take_item_from_corpse(self):
        self.game.runtime_state = make_runtime_with_corpse(self.room.room_id)
        result = handle_take_from_corpse(self.game, self.player, self.room, "stick", "goblin")
        self.assertTrue(result)
        self.assertIn("stick", self.player.inventory)
        self.assertTrue(
            any("take" in msg.lower() and "stick" in msg for _, msg in self.game._messages)
        )
        self.assertTrue(self.game.runtime_state.update_calls)

    def test_take_coins_from_corpse(self):
        rt = MockRuntimeState()
        corpse = {
            "entity_type": "corpse",
            "name": "corpse of goblin",
            "instance_id": "c1",
            "loot": {"coins": 10, "items": []},
            "ownership": {"allowed_player_ids": ["TestPlayer"], "expires_at": 999999999},
        }
        rt.add_entity_to_room(self.room.room_id, corpse)
        self.game.runtime_state = rt
        result = handle_take_from_corpse(self.game, self.player, self.room, "coin", "goblin")
        self.assertTrue(result)
        self.assertEqual(self.player.gold, 10)
        self.assertTrue(any("coin" in msg.lower() for _, msg in self.game._messages))


class TestLootAllWithCorpseName(unittest.TestCase):
    """Tests for 'loot all <corpse_name>' feature."""

    def setUp(self):
        self.room = MockRoom()
        self.player = MockPlayer()
        self.game = MockGame(
            rooms={self.room.room_id: self.room},
            items=make_mock_items(),
        )
        self.rt = MockRuntimeState()
        self.game.runtime_state = self.rt

    def test_loot_all_with_corpse_name(self):
        """Test 'loot all goblin' takes from specific corpse."""
        corpse1 = {
            "entity_type": "corpse",
            "name": "corpse of a goblin",
            "instance_id": "corpse_1",
            "loot": {"rolled": True, "coins": 5, "items": [{"item_id": "stick", "count": 1}]},
        }
        corpse2 = {
            "entity_type": "corpse",
            "name": "corpse of a troll",
            "instance_id": "corpse_2",
            "loot": {"rolled": True, "coins": 10, "items": [{"item_id": "potion", "count": 1}]},
        }
        self.rt.add_entity_to_room(self.room.room_id, corpse1)
        self.rt.add_entity_to_room(self.room.room_id, corpse2)

        loot_command(self.game, self.player, ["all", "goblin"])

        # Should have looted goblin corpse
        self.assertIn("stick", self.player.inventory)
        self.assertEqual(self.player.gold, 5)
        # Should NOT have looted troll corpse
        self.assertNotIn("potion", self.player.inventory)

    def test_loot_all_no_matching_corpse(self):
        """Test 'loot all dragon' when no dragon corpse exists."""
        corpse = {
            "entity_type": "corpse",
            "name": "corpse of a goblin",
            "instance_id": "corpse_1",
            "loot": {"rolled": True, "coins": 5, "items": []},
        }
        self.rt.add_entity_to_room(self.room.room_id, corpse)

        loot_command(self.game, self.player, ["all", "dragon"])

        # Should show error message
        self.assertTrue(any("don't see" in msg.lower() for _, msg in self.game._messages))

    def test_loot_all_multiple_corpses_requires_name(self):
        """Test 'loot all' with multiple corpses prompts for name."""
        corpse1 = {
            "entity_type": "corpse",
            "name": "corpse of a goblin",
            "instance_id": "corpse_1",
            "loot": {"rolled": True, "coins": 5, "items": []},
        }
        corpse2 = {
            "entity_type": "corpse",
            "name": "corpse of a troll",
            "instance_id": "corpse_2",
            "loot": {"rolled": True, "coins": 10, "items": []},
        }
        self.rt.add_entity_to_room(self.room.room_id, corpse1)
        self.rt.add_entity_to_room(self.room.room_id, corpse2)

        loot_command(self.game, self.player, ["all"])

        # Should prompt for corpse name
        self.assertTrue(any("which corpse" in msg.lower() or "loot all <name>" in msg.lower() for _, msg in self.game._messages))


class TestLootCommand(unittest.TestCase):
    """Tests for loot_command()."""

    def setUp(self):
        self.room = MockRoom()
        self.player = MockPlayer()
        self.items = make_mock_items()
        self.game = MockGame(rooms={"room_1": self.room}, items=self.items)

    def test_unknown_room_sends_message(self):
        game = MockGame(rooms={}, items=self.items)
        loot_command(game, self.player, [])
        self.assertTrue(any("unknown" in msg.lower() for _, msg in game._messages))

    def test_no_corpses_sends_message(self):
        self.game.runtime_state = MockRuntimeState()
        loot_command(self.game, self.player, [])
        self.assertTrue(any("no corpses" in msg.lower() for _, msg in self.game._messages))

    def test_loot_list_shows_corpse_names(self):
        self.game.runtime_state = make_runtime_with_corpse(self.room.room_id)
        loot_command(self.game, self.player, [])
        self.assertTrue(
            any("corpse" in msg.lower() and "goblin" in msg.lower() for _, msg in self.game._messages)
        )

    def test_loot_corpse_name_shows_contents(self):
        self.game.runtime_state = make_runtime_with_corpse(self.room.room_id)
        loot_command(self.game, self.player, ["goblin"])
        self.assertTrue(
            any("Coins" in msg or "Items" in msg or "empty" in msg.lower() for _, msg in self.game._messages)
        )

    def test_loot_all_takes_items_and_coins(self):
        self.game.runtime_state = make_runtime_with_corpse(self.room.room_id)
        loot_command(self.game, self.player, ["all"])
        self.assertEqual(len(self.player.inventory), 3)
        self.assertEqual(self.player.gold, 5)
        self.assertTrue(any("take" in msg.lower() for _, msg in self.game._messages))
