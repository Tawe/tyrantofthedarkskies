# Contributing to Tyrant of the Dark Skies

Thank you for your interest in contributing! This guide will help you add content to the game.

## 🎯 How to Contribute

The game uses a JSON-based contribution system. You can add:

- **Rooms** - New areas to explore
- **NPCs** - Characters and creatures
- **Items** - Weapons, armor, and objects
- **Maneuvers** - Combat abilities
- **Races** - Playable character races
- **Planets** - Cosmic influences
- **Starsigns** - Fate-based abilities
- **Weapons** - Weapon templates
- **Weapon Modifiers** - Material modifiers

## 📝 Contribution Process

1. **Fork the repository**
2. **Create a branch** for your contribution
3. **Add your content** as JSON files in the appropriate `contributions/` folder
4. **Test locally** to ensure it works
5. **Submit a pull request** with a description of your additions
6. **Automatic Sync**: Once merged, your contributions are automatically synced to Firebase! 🎉

> **Note**: The repository includes a GitHub Actions workflow that automatically syncs contribution files to Firebase when they're added or modified. See [Contributions Sync Documentation](docs/contributions_sync.md) for details.

## 📁 File Organization

All contributions go in the `contributions/` directory:

```
contributions/
├── rooms/          # Room definitions
├── npcs/           # NPC definitions
├── items/          # Item definitions (weapons/, armor/, objects/)
├── maneuvers/      # Maneuver definitions
├── races/          # Race definitions
├── planets/        # Planet definitions
├── starsigns/      # Starsign definitions
├── weapons/        # Weapon templates
└── weapon_modifiers/ # Material modifiers
```

## 📋 Format Guidelines

### Rooms

**File:** `contributions/rooms/<room_id>.json`

```json
{
  "room_id": "example_room",
  "name": "Example Room",
  "description": "A detailed description of the room.",
  "exits": {
    "north": "target_room_id",
    "south": "another_room_id"
  },
  "flags": ["safe", "public"],
  "items": ["item_id_1", "item_id_2"],
  "npcs": ["npc_id"]
}
```

**Required Fields:**
- `room_id`: Unique identifier (must match filename)
- `name`: Display name
- `description`: Room description

**Optional Fields:**
- `exits`: Object with direction → target_room_id mappings
- `flags`: Array of room flags (safe, dangerous, dark, public, shop, healing)
- `items`: Array of item IDs that spawn here
- `npcs`: Array of NPC IDs that spawn here

See `contributions/rooms/README.md` for more details.

### NPCs

**File:** `contributions/npcs/<npc_id>.json`

```json
{
  "npc_id": "example_npc",
  "name": "Example NPC",
  "description": "A description of the NPC.",
  "level": 5,
  "attributes": {
    "physical": 12,
    "mental": 10,
    "spiritual": 8,
    "social": 14
  },
  "hostile": false,
  "shop": {
    "buy_multiplier": 1.2,
    "sell_multiplier": 0.8
  }
}
```

See `contributions/npcs/README.md` for complete format.

### Items

**File:** `contributions/items/<category>/<item_id>.json`

Categories: `weapons/`, `armor/`, `objects/`

```json
{
  "item_id": "example_sword",
  "name": "Example Sword",
  "description": "A fine example sword.",
  "item_type": "weapon",
  "weapon_template": "shortsword",
  "durability": 100,
  "value": 50
}
```

See `contributions/items/README.md` for details.

### Maneuvers

**File:** `contributions/maneuvers/<maneuver_id>.json`

```json
{
  "maneuver_id": "example_maneuver",
  "name": "Example Maneuver",
  "description": "What this maneuver does.",
  "tier": "low",
  "requirements": {
    "level": 1,
    "skills": {
      "fighting": 5
    }
  }
}
```

See `contributions/maneuvers/README.md` for complete format.

### Races

**File:** `contributions/races/<race_id>.json`

```json
{
  "race_id": "example_race",
  "name": "Example Race",
  "description": "Description of the race.",
  "attribute_modifiers": {
    "physical": 2,
    "mental": 0,
    "spiritual": 1,
    "social": -1
  },
  "starting_skills": {
    "fighting": 5,
    "crafting": 3
  }
}
```

See `contributions/races/README.md` for details.

### Planets

**File:** `contributions/planets/<planet_id>.json`

```json
{
  "planet_id": "example_planet",
  "name": "Example Planet",
  "theme": "Theme description",
  "attribute_bonuses": {
    "physical": 1,
    "mental": 2
  },
  "gift_maneuver": "maneuver_id"
}
```

See `contributions/planets/README.md` for complete format.

### Starsigns

**File:** `contributions/starsigns/<starsign_id>.json`

```json
{
  "starsign_id": "example_starsign",
  "name": "Example Starsign",
  "theme": "Theme description",
  "attribute_modifiers": {
    "physical": 0,
    "mental": 1
  },
  "fated_mark": {
    "name": "Mark Name",
    "description": "Mark description"
  }
}
```

See `contributions/starsigns/README.md` for details.

## ✅ Quality Guidelines

1. **Follow the format** - Use existing files as examples
2. **Be consistent** - Match the style of existing content
3. **Test locally** - Make sure your content loads without errors
4. **Balance** - Consider game balance when adding items/NPCs
5. **Descriptions** - Write engaging, immersive descriptions
6. **Unique IDs** - Ensure your IDs don't conflict with existing content

## 🧪 Testing Your Contributions

1. **Start the server locally:**
   ```bash
   python3 mud_server.py
   ```

2. **Verify your content loads:**
   - Check server startup logs for any errors
   - Use in-game commands to verify your content appears
   - Test functionality (e.g., enter rooms, interact with NPCs)

3. **Check for errors:**
   - Invalid JSON syntax
   - Missing required fields
   - Invalid references (e.g., room IDs that don't exist)

## 📤 Submitting a Pull Request

1. **Write a clear title** describing your contribution
2. **Add a description** explaining what you added
3. **List your changes** - What files did you add/modify?
4. **Include screenshots** (if applicable) - Show your content in-game
5. **Reference issues** - If your PR fixes an issue, reference it

### PR Template

```markdown
## Description
Brief description of what you added

## Changes
- Added room: example_room
- Added NPC: example_npc
- Added item: example_sword

## Testing
- [ ] Tested locally
- [ ] Content loads without errors
- [ ] Verified in-game functionality

## Screenshots
(Optional - add screenshots of your content in-game)
```

## 🎨 Content Guidelines

### Writing Style

- **Immersive**: Write descriptions that draw players into the world
- **Consistent**: Match the tone and style of existing content
- **Clear**: Be specific and avoid ambiguity
- **Balanced**: Consider game balance and player experience

### Room Descriptions

- Include sensory details (sight, sound, smell)
- Mention notable features
- Set the mood and atmosphere
- Be concise but evocative

### NPC Descriptions

- Give personality and character
- Include physical appearance
- Hint at their role or purpose
- Make them memorable

### Item Descriptions

- Describe appearance and feel
- Mention practical details
- Add flavor text for immersion
- Keep it concise

## 🚫 What Not to Contribute

- **Offensive content** - Keep it appropriate for all audiences
- **Overpowered items** - Maintain game balance
- **Duplicate content** - Check existing content first
- **Incomplete content** - Finish your additions before submitting

## 💡 Ideas for Contributions

- **New areas**: Expand the world with new regions
- **Quests**: Add NPCs with quests and storylines
- **Items**: Create interesting weapons, armor, and objects
- **Creatures**: Add new enemies and NPCs
- **Races/Planets**: Expand character creation options
- **Maneuvers**: Add new combat abilities

## 📞 Questions?

- Open an issue for questions
- Check existing README files in contribution folders
- Review existing content as examples
- Ask in GitHub Discussions

## 🙏 Thank You!

Your contributions make the game better for everyone. We appreciate your time and effort!

---

**Ready to contribute?** Pick a contribution type, create your JSON files, and submit a pull request!
