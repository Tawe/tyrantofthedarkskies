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
- `npcs`: Array of NPC IDs in the room
- `flags`: Array of room flags (safe, dangerous, dark, shop, etc.)
- `combat_tags`: Array of combat tags (open, cramped, slick, etc.)

## Example

See `black_anchor_common.json` for a complete example.

## Validation

All room files are automatically validated on pull request.
