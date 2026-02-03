"""Unit tests for systems.loot_system."""

import unittest
from unittest.mock import patch

from systems.loot_system import generate_loot, prepare_corpse_entity


class TestGenerateLoot(unittest.TestCase):
    """Tests for generate_loot()."""

    def test_empty_config_returns_rolled_structure(self):
        result = generate_loot({}, {}, {})
        self.assertTrue(result["rolled"])
        self.assertEqual(result["coins"], 0)
        self.assertEqual(result["items"], [])

    def test_guaranteed_items_included(self):
        items = {"stick": object(), "potion": object()}
        config = {
            "guaranteed": [
                {"item_id": "stick", "count": 1},
                {"item_id": "potion", "count": 2},
            ]
        }
        result = generate_loot(config, {}, items)
        self.assertTrue(result["rolled"])
        self.assertEqual(result["coins"], 0)
        self.assertEqual(len(result["items"]), 2)
        by_id = {e["item_id"]: e["count"] for e in result["items"]}
        self.assertEqual(by_id.get("stick"), 1)
        self.assertEqual(by_id.get("potion"), 2)

    def test_guaranteed_skips_missing_item_in_catalog(self):
        items = {"stick": object()}
        config = {"guaranteed": [{"item_id": "stick", "count": 1}, {"item_id": "nonexistent", "count": 1}]}
        result = generate_loot(config, {}, items)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["item_id"], "stick")

    def test_coins_dict_min_max(self):
        config = {"coins": {"min": 10, "max": 10}}
        with patch("systems.loot_system.random.randint", return_value=10):
            result = generate_loot(config, {}, {})
        self.assertEqual(result["coins"], 10)

    def test_coins_scalar(self):
        config = {"coins": 42}
        result = generate_loot(config, {}, {})
        self.assertEqual(result["coins"], 42)

    def test_legacy_entries_format(self):
        items = {"stick": object()}
        config = {"entries": [{"item": "stick", "chance": 100, "count": 1}]}
        with patch("systems.loot_system.random.randint", return_value=50):
            result = generate_loot(config, {}, items)
        self.assertTrue(result["rolled"])
        self.assertEqual(result["coins"], 0)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["item_id"], "stick")
        self.assertEqual(result["items"][0]["count"], 1)

    def test_legacy_entries_zero_chance_skips(self):
        items = {"stick": object()}
        config = {"entries": [{"item": "stick", "chance": 0, "count": 1}]}
        with patch("systems.loot_system.random.randint", return_value=1):
            result = generate_loot(config, {}, items)
        self.assertEqual(len(result["items"]), 0)

    def test_tables_rolls_from_weighted_table(self):
        items = {"stick": object()}
        loot_tables = {
            "trash": {
                "entries": [
                    {"item_id": "stick", "weight": 10, "min": 1, "max": 1},
                ]
            }
        }
        config = {"tables": [{"loot_table_id": "trash", "rolls": 1}]}
        with patch("systems.loot_system.random.randint", side_effect=[5, 1]):
            result = generate_loot(config, loot_tables, items)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["item_id"], "stick")

    def test_chance_uses_random(self):
        items = {"potion": object()}
        config = {"chance": [{"item_id": "potion", "chance": 1.0, "count": 1}]}
        with patch("systems.loot_system.random.random", return_value=0.0):
            result = generate_loot(config, {}, items)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["item_id"], "potion")

    def test_same_item_stacks_in_guaranteed(self):
        items = {"stick": object()}
        config = {"guaranteed": [{"item_id": "stick", "count": 1}, {"item_id": "stick", "count": 2}]}
        result = generate_loot(config, {}, items)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["item_id"], "stick")
        self.assertEqual(result["items"][0]["count"], 3)


class TestPrepareCorpseEntity(unittest.TestCase):
    """Tests for prepare_corpse_entity()."""

    def test_returns_template_id_and_entity_type(self):
        config = {"decay_seconds": 300}
        opts = prepare_corpse_entity(
            config, "goblin", "a goblin", "Alice",
            {}, {}, now=1000.0,
        )
        self.assertEqual(opts["template_id"], "goblin")
        self.assertEqual(opts["entity_type"], "corpse")

    def test_corpse_name_and_description(self):
        config = {}
        opts = prepare_corpse_entity(config, "skeleton", "Crowned Skeleton", None, {}, {}, now=1000.0)
        self.assertEqual(opts["name"], "corpse of Crowned Skeleton")
        self.assertIn("glints", opts["description"].lower())

    def test_ownership_includes_attacker_and_expiry(self):
        config = {}
        opts = prepare_corpse_entity(config, "goblin", "goblin", "Bob", {}, {}, now=1000.0)
        self.assertEqual(opts["ownership"]["mode"], "contributors")
        self.assertIn("Bob", opts["ownership"]["allowed_player_ids"])
        self.assertEqual(opts["ownership"]["expires_at"], 1060.0)

    def test_ownership_no_attacker(self):
        config = {}
        opts = prepare_corpse_entity(config, "goblin", "goblin", None, {}, {}, now=1000.0)
        self.assertEqual(opts["ownership"]["allowed_player_ids"], [])
        self.assertEqual(opts["ownership"]["expires_at"], 1060.0)

    def test_decay_uses_config(self):
        config = {"decay_seconds": 120}
        opts = prepare_corpse_entity(config, "goblin", "goblin", None, {}, {}, now=1000.0)
        self.assertEqual(opts["expires_at"], 1120.0)
        self.assertEqual(opts["decays_at"], 1120.0)

    def test_custom_corpse_template_id(self):
        config = {"corpse_template_id": "corpse_humanoid", "decay_seconds": 600}
        opts = prepare_corpse_entity(config, "bandit", "bandit", "Alice", {}, {}, now=0.0)
        self.assertEqual(opts["template_id"], "corpse_humanoid")
        self.assertEqual(opts["entity_type"], "corpse")

    def test_loot_included_from_generate_loot(self):
        items = {"stick": object()}
        config = {"guaranteed": [{"item_id": "stick", "count": 1}], "decay_seconds": 600}
        opts = prepare_corpse_entity(config, "goblin", "goblin", None, {}, items, now=0.0)
        self.assertIn("loot", opts)
        self.assertTrue(opts["loot"]["rolled"])
        self.assertEqual(len(opts["loot"]["items"]), 1)
        self.assertEqual(opts["loot"]["items"][0]["item_id"], "stick")

    def test_flags_lootable(self):
        opts = prepare_corpse_entity({}, "x", "x", None, {}, {}, now=0.0)
        self.assertIn("lootable", opts["flags"])
