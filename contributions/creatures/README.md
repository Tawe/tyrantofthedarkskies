# Creature Contributions

This folder contains **creature templates** used for present encounters (spawn groups), combat, and runtime entity instances. There is **one template per creature type**. Rooms that want multiple creatures of that type use a single `spawn_group` with that template and set `max_alive`; the game creates multiple **instances** from the same template, each with its own HP and instance ID.

## Schema (recommended)

Use the **creature template schema** from **docs/creature_templates.md**:

- `template_id`, `name`, `entity_type`, `tier`, `level_range`, `role`
- `stats`: `hp_max`, `attack` (speed_cost, accuracy, damage_min/max, damage_type, crit_chance)
- `skills`: capitalized keys (Dodging, Fighting, etc.)
- `behaviors`: pursue, leash_radius, leash_time, threat_profile, morale
- `loot`: `loot_table_id`, `xp_value`
- `maneuvers`: list of maneuver IDs

The loader maps this into the game’s NPC/template lookup so spawn_groups, combat, and runtime instances work. Legacy files using `npc_id`, `health`, `max_health`, `combat_role`, etc. are still supported.

Use **contributions/npcs/** for named NPCs (merchants, quest givers). Use **contributions/creatures/** for hostile or ambient creatures spawned via room `spawn_groups`.

## File Format

Each file should be named `{creature_id}.json`. The `npc_id` field must match the filename and must be unique across both NPCs and creatures.

Same required/optional fields as NPCs:

- `npc_id`: Unique identifier (must match filename)
- `name`, `description`: Display name and description
- `health`, `max_health`, `attributes`, `skills`
- `combat_role`, `tier`, `level`, `exp_value`
- `is_hostile`: Typically `true` for creatures
- `loot_table`: Optional; used when the creature is defeated

## Examples

- **Kelp Flea** (`kelp_flea.json`): minion, Unflooded Sea / Kelp Plains. A room can spawn multiple instances with one spawn_group: `template_id`: `"kelp_flea"`, `max_alive`: `2`.
- **Unflooded Sea:** reef_crab, reef_crab_brute, rift_wisp, unflooded_stalker, crabfolk_scout, ancient_sentinel_fragment.
- **Kelp Plains:** kelp_crawler, kelp_shade, kelp_plains_alpha, kelp_leviathan_spawn.
- **Rift Forest:** rift_skitterling, coral_stalker, rift_warden, rift_warden_mender, rift_forest_hunter, corrupted_guardian, rift_heart_sentinel.

## Validation

Creature files are loaded with NPCs; validation follows the same rules as NPC contributions.
