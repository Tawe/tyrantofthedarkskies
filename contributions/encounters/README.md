# Encounter Contributions

This folder holds **random encounter tables** (see `docs/random_encounters.md`). Rooms with a `zone` (e.g. `kelp_plains`, `unflooded_sea`, `rift_forest`) use the matching zone table when a player enters.

## Files

- **`<zone_id>.json`** – One file per zone (e.g. `unflooded_sea.json`, `kelp_plains.json`, `rift_forest.json`). Each has:
  - `zone_id`: Must match the room’s `zone` field.
  - `name`: Display name (optional).
  - `table`: Array of encounter rows. Each row:
    - `min_roll`, `max_roll`: d100 range (inclusive).
    - `encounter_type`: `combat`, `social`, `environmental`, or `exploration`.
    - `composition_key`: Key into `compositions.json` for combat; `null` for non-combat.

- **`compositions.json`** – Maps `composition_key` to spawn definitions. Each value is an array of:
  - `template_id`: Creature template (from `contributions/creatures/`).
  - `min_count`, `max_count`: Count range to spawn (inclusive).

## Example

Zone row:

```json
{ "min_roll": 1, "max_roll": 20, "encounter_type": "combat", "composition_key": "kelp_fleas" }
```

Composition:

```json
"kelp_fleas": [
  { "template_id": "kelp_flea", "min_count": 3, "max_count": 5 }
]
```

Roll 1–20 in that zone → spawn 3–5 kelp fleas (one encounter group, shared `encounter_id`).
