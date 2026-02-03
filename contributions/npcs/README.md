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

## Dialogue (emote + say)

Per `docs/emote_tone_volume_system.md`, dialogue can be a **string** (legacy) or an **object**:

- `dialogue`: Array of strings or objects. Each object: `{ "emote": "optional action", "say": "spoken text" }`. Do not put quotation marks in `say`; the engine formats output (e.g. "Bram nods west.\nBram says: Guild board's through there.").
- `keywords`: Map keyword (and aliases) to a string or to `{ "emote": "...", "say": "...", "set_flag": "optional" }`.

Use `emote` for visible actions; use `say` only for spoken words. See `innkeeper_bram.json` for examples.

## Example

See `jalia.json` for a complete example. See `innkeeper_bram.json` for dialogue (emote/say) examples.

## Validation

All NPC files are automatically validated on pull request.
