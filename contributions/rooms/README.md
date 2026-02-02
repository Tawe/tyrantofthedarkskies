# Room Contributions

This folder contains individual room definition files, grouped by area in subfolders. **Room text and exits must follow the style guide:** `docs/room.md`.

The server loads all `.json` files under `contributions/rooms/` recursively (flat or in subfolders); folder structure is for organization only.

## Folder layout

| Folder | Contents |
|--------|----------|
| `sunken_kings_cave/` | Cave adventure: `cave_*.json` (watery entry, pit, tomb, idol chamber, etc.) |
| `new_cove_town/` | Town and harbor: Black Anchor (booths, common, guild), docks, governor’s house, Jalia’s Goods, New Cove Square, wooden wall, Temple of Lumeris, Magitium outpost, city barracks |
| `kelp_plains/` | Kelp plains zone: `kelp_plains.json`, `buried_ruins.json` |
| `rift_forest/` | Rift forest zone: `rift_forest.json`, `crabfolk_settlement.json` |
| `unflooded_sea/` | Unflooded sea zone: `unflooded_sea.json`, `ancient_ruins.json` |

## File Format

Each file should be named `{room_id}.json` and contain a single room definition.

## Required Fields

- `room_id`: Unique identifier (must match filename)
- `name`: Display name
- `description`: Room description. Per `docs/room.md`, use sensory, diegetic hints for directions (e.g. "To one side, the cave narrows…") instead of naming unseen areas. Do not spoil destinations.
- `exits`: Object mapping directions to target room IDs
- `items`: Array of item IDs in the room
- `npcs`: Array of NPC IDs in the room (static; always present)
- `spawn_groups`: Optional. Present encounters: creatures spawned at runtime when players enter. Each entry: `spawn_id`, `template_id` (NPC template), `max_alive`, `cooldown_seconds`. Use empty `npcs` and `spawn_groups` for encounter rooms (e.g. Kelp Plains).
- `creature_presence`: Optional. When the room has spawned creatures, this lore-friendly sentence is appended to the room description instead of listing creature names. Example: `"Among the wet rocks, reef crabs click and scuttle."`
- `exit_hints`: Optional. **Use only for visible hazards** (pit, ledge, water), not for destination names. Per `docs/room.md`: default is directions only; add a label only when the action is obvious and present (e.g. `{ "north": "Attempt to cross the pit" }`). Do not use "Toward X", "To X", or "Back to X" for unseen areas.
- `ambient_lines`: Optional. Array of strings. When a player enters the room, one line is chosen at random and broadcast to everyone in the room (e.g. "A burst of laughter erupts from a table near the hearth."). Use to make social hubs feel alive without new commands.
- `enter_flavor`: Optional. Array of strings. When a player enters the room, one line is chosen at random and sent only to that player (e.g. "Innkeeper Bram glances up when you enter."). Use for light NPC acknowledgment.
- `hidden_exits`: Optional. List of `{ "direction", "target", "reveal_flag" }`. Exits are not shown until the player has the flag (e.g. after a search success). See `docs/room.md` Rule 4.
- `zone`: Optional. Zone id for random encounter table (docs/random_encounters.md): `unflooded_sea`, `kelp_plains`, `rift_forest`. When set, entering the room may trigger a zone-table encounter (combat spawn with shared encounter_id).
- `flags`: Array of room flags (safe, dangerous, dark, shop, etc.)
- `combat_tags`: Array of combat tags (open, cramped, slick, etc.)

## Style checklist (docs/room.md)

- Room description hints at each direction without naming unseen locations.
- Exits are listed without destination labels (default: directions only).
- Hazard exits (pit, climb, swim) may use a short action label, e.g. "Attempt to cross the pit".
- Secret exits are in `hidden_exits` and appear only after discovery (e.g. search sets `reveal_flag`).
- On secret discovery, success text should state the revealed direction (e.g. "A hidden passage is revealed to the east.").

## Example

See `new_cove_town/black_anchor_common.json` for a complete example.

## Validation

All room files are automatically validated on pull request.
