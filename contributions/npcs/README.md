# NPC Contributions

This folder contains individual NPC definition files.

## File Format

Each file should be named `{npc_id}.json` and contain a single NPC definition.

## Required Fields

- `npc_id`: Unique identifier (must match filename)
- `name`: Display name
- `description`: NPC description
- `health`, `max_health`: Health values
- `attributes`: Object with physical, mental, spiritual, social
- `combat_role`: One of: Brute, Minion, Boss, Artillery, Healer, Controller, or null
- `tier`: Low, Mid, High, or Epic
- `is_hostile`: Boolean

## Example

See `jalia.json` for a complete example.

## Validation

All NPC files are automatically validated on pull request.
