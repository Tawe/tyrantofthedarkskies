# Room Contributions

This folder contains individual room definition files.

## File Format

Each file should be named `{room_id}.json` and contain a single room definition.

## Required Fields

- `room_id`: Unique identifier (must match filename)
- `name`: Display name
- `description`: Room description
- `exits`: Object mapping directions to target room IDs
- `items`: Array of item IDs in the room
- `npcs`: Array of NPC IDs in the room (static; always present)
- `spawn_groups`: Optional. Present encounters: creatures spawned at runtime when players enter. Each entry: `spawn_id`, `template_id` (NPC template), `max_alive`, `cooldown_seconds`. Use empty `npcs` and `spawn_groups` for encounter rooms (e.g. Kelp Plains).
- `zone`: Optional. Zone id for random encounter table (docs/random_encounters.md): `unflooded_sea`, `kelp_plains`, `rift_forest`. When set, entering the room may trigger a zone-table encounter (combat spawn with shared encounter_id).
- `flags`: Array of room flags (safe, dangerous, dark, shop, etc.)
- `combat_tags`: Array of combat tags (open, cramped, slick, etc.)

## Example

See `black_anchor_common.json` for a complete example.

## Validation

All room files are automatically validated on pull request.
