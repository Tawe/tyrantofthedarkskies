#!/usr/bin/env python3
"""Split consolidated JSON files into individual contribution files."""

import json
import os
from pathlib import Path

def create_contributions_structure():
    """Create the contributions directory structure."""
    base_dir = Path("contributions")
    directories = [
        base_dir / "npcs",
        base_dir / "rooms",
        base_dir / "items",  # Subfolders created in split_items()
        base_dir / "items" / "weapons",
        base_dir / "items" / "armor",
        base_dir / "items" / "objects",
        base_dir / "shop_items",
        base_dir / "planets",
        base_dir / "races",
        base_dir / "starsigns",
        base_dir / "maneuvers",
        base_dir / "weapons",
        base_dir / "weapon_modifiers"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def split_npcs():
    """Split npcs.json into individual files."""
    npcs_file = Path("mud_data/npcs.json")
    output_dir = Path("contributions/npcs")
    
    if not npcs_file.exists():
        print(f"File not found: {npcs_file}")
        return 0
    
    with open(npcs_file, 'r', encoding='utf-8') as f:
        npcs = json.load(f)
    
    count = 0
    for npc in npcs:
        npc_id = npc.get('npc_id')
        if not npc_id:
            print(f"Warning: NPC missing npc_id, skipping: {npc.get('name', 'unknown')}")
            continue
        
        filename = f"{npc_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(npc, f, indent=2, ensure_ascii=False)
        
        count += 1
        print(f"  Created: {filename}")
    
    print(f"Split {count} NPCs into individual files")
    return count

def split_rooms():
    """Split rooms.json into individual files."""
    rooms_file = Path("mud_data/rooms.json")
    output_dir = Path("contributions/rooms")
    
    if not rooms_file.exists():
        print(f"File not found: {rooms_file}")
        return 0
    
    with open(rooms_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        rooms = data.get('rooms', data) if isinstance(data, dict) else data
    
    count = 0
    for room in rooms:
        room_id = room.get('room_id')
        if not room_id:
            print(f"Warning: Room missing room_id, skipping: {room.get('name', 'unknown')}")
            continue
        
        filename = f"{room_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(room, f, indent=2, ensure_ascii=False)
        
        count += 1
        print(f"  Created: {filename}")
    
    print(f"Split {count} rooms into individual files")
    return count

def split_items():
    """Split items.json into individual files, organized by subfolders."""
    items_file = Path("mud_data/items.json")
    base_output_dir = Path("contributions/items")
    
    # Create subfolders
    weapons_dir = base_output_dir / "weapons"
    armor_dir = base_output_dir / "armor"
    objects_dir = base_output_dir / "objects"
    weapons_dir.mkdir(parents=True, exist_ok=True)
    armor_dir.mkdir(parents=True, exist_ok=True)
    objects_dir.mkdir(parents=True, exist_ok=True)
    
    if not items_file.exists():
        print(f"File not found: {items_file}")
        return 0
    
    with open(items_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        items = data.get('items', data) if isinstance(data, dict) else data
    
    if not isinstance(items, list):
        # If it's a dict, convert to list
        items = list(items.values()) if isinstance(items, dict) else [items]
    
    count = 0
    weapons_count = 0
    armor_count = 0
    objects_count = 0
    
    for item in items:
        item_id = item.get('item_id')
        if not item_id:
            print(f"Warning: Item missing item_id, skipping: {item.get('name', 'unknown')}")
            continue
        
        item_type = item.get('item_type', 'item').lower()
        
        # Determine subfolder based on item_type
        if item_type == 'weapon':
            output_dir = weapons_dir
            weapons_count += 1
        elif item_type == 'armor':
            output_dir = armor_dir
            armor_count += 1
        else:
            # consumable, item, tool, etc. go in objects
            output_dir = objects_dir
            objects_count += 1
        
        filename = f"{item_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(item, f, indent=2, ensure_ascii=False)
        
        count += 1
        print(f"  Created: {output_dir.name}/{filename}")
    
    print(f"Split {count} items into individual files:")
    print(f"  Weapons: {weapons_count}")
    print(f"  Armor: {armor_count}")
    print(f"  Objects: {objects_count}")
    return count

def split_shop_items():
    """Split shop_items.json into individual files."""
    shop_items_file = Path("mud_data/shop_items.json")
    output_dir = Path("contributions/shop_items")
    
    if not shop_items_file.exists():
        print(f"File not found: {shop_items_file}")
        return 0
    
    with open(shop_items_file, 'r', encoding='utf-8') as f:
        shop_items = json.load(f)
    
    if not isinstance(shop_items, list):
        shop_items = list(shop_items.values()) if isinstance(shop_items, dict) else [shop_items]
    
    count = 0
    for item in shop_items:
        item_id = item.get('item_id')
        if not item_id:
            print(f"Warning: Shop item missing item_id, skipping: {item.get('name', 'unknown')}")
            continue
        
        filename = f"{item_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(item, f, indent=2, ensure_ascii=False)
        
        count += 1
        print(f"  Created: {filename}")
    
    print(f"Split {count} shop items into individual files")
    return count

def split_planets():
    """Split planets.json into individual files."""
    planets_file = Path("planets.json")
    output_dir = Path("contributions/planets")
    
    if not planets_file.exists():
        print(f"File not found: {planets_file}")
        return 0
    
    with open(planets_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        planets = data.get("planets", data) if isinstance(data, dict) else data
    
    if not isinstance(planets, list):
        planets = list(planets.values()) if isinstance(planets, dict) else [planets]
    
    count = 0
    for planet in planets:
        planet_id = planet.get('planet_id')
        if not planet_id:
            print(f"Warning: Planet missing planet_id, skipping: {planet.get('name', 'unknown')}")
            continue
        
        filename = f"{planet_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(planet, f, indent=2, ensure_ascii=False)
        
        count += 1
        print(f"  Created: {filename}")
    
    print(f"Split {count} planets into individual files")
    return count

def split_races():
    """Split races.json into individual files."""
    races_file = Path("races.json")
    output_dir = Path("contributions/races")
    
    if not races_file.exists():
        print(f"File not found: {races_file}")
        return 0
    
    with open(races_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        races = data.get("races", data) if isinstance(data, dict) else data
    
    if not isinstance(races, list):
        races = list(races.values()) if isinstance(races, dict) else [races]
    
    count = 0
    for race in races:
        race_id = race.get('race_id')
        if not race_id:
            print(f"Warning: Race missing race_id, skipping: {race.get('name', 'unknown')}")
            continue
        
        filename = f"{race_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(race, f, indent=2, ensure_ascii=False)
        
        count += 1
        print(f"  Created: {filename}")
    
    print(f"Split {count} races into individual files")
    return count

def split_starsigns():
    """Split starsigns.json into individual files."""
    starsigns_file = Path("starsigns.json")
    output_dir = Path("contributions/starsigns")
    
    if not starsigns_file.exists():
        print(f"File not found: {starsigns_file}")
        return 0
    
    with open(starsigns_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        starsigns = data.get("starsigns", data) if isinstance(data, dict) else data
    
    if not isinstance(starsigns, list):
        starsigns = list(starsigns.values()) if isinstance(starsigns, dict) else [starsigns]
    
    count = 0
    for starsign in starsigns:
        starsign_id = starsign.get('starsign_id')
        if not starsign_id:
            print(f"Warning: Starsign missing starsign_id, skipping: {starsign.get('name', 'unknown')}")
            continue
        
        filename = f"{starsign_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(starsign, f, indent=2, ensure_ascii=False)
        
        count += 1
        print(f"  Created: {filename}")
    
    print(f"Split {count} starsigns into individual files")
    return count

def split_maneuvers():
    """Split maneuvers.json into individual files."""
    maneuvers_file = Path("maneuvers.json")
    output_dir = Path("contributions/maneuvers")
    
    if not maneuvers_file.exists():
        print(f"File not found: {maneuvers_file}")
        return 0
    
    with open(maneuvers_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        maneuvers = data.get("maneuvers", data) if isinstance(data, dict) else data
    
    if not isinstance(maneuvers, list):
        maneuvers = list(maneuvers.values()) if isinstance(maneuvers, dict) else [maneuvers]
    
    count = 0
    for maneuver in maneuvers:
        maneuver_id = maneuver.get('maneuver_id')
        if not maneuver_id:
            print(f"Warning: Maneuver missing maneuver_id, skipping: {maneuver.get('name', 'unknown')}")
            continue
        
        filename = f"{maneuver_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(maneuver, f, indent=2, ensure_ascii=False)
        
        count += 1
        print(f"  Created: {filename}")
    
    print(f"Split {count} maneuvers into individual files")
    return count

def split_weapons():
    """Split weapons.json into individual files."""
    weapons_file = Path("weapons.json")
    output_dir = Path("contributions/weapons")
    
    if not weapons_file.exists():
        print(f"File not found: {weapons_file}")
        return 0
    
    with open(weapons_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        weapons = data.get("weapons", data) if isinstance(data, dict) else data
    
    if not isinstance(weapons, list):
        weapons = list(weapons.values()) if isinstance(weapons, dict) else [weapons]
    
    count = 0
    for weapon in weapons:
        weapon_id = weapon.get('id')
        if not weapon_id:
            print(f"Warning: Weapon missing id, skipping: {weapon.get('name', 'unknown')}")
            continue
        
        filename = f"{weapon_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(weapon, f, indent=2, ensure_ascii=False)
        
        count += 1
        print(f"  Created: {filename}")
    
    print(f"Split {count} weapons into individual files")
    return count

def split_weapon_modifiers():
    """Split weapon_modifiers.json into individual files."""
    modifiers_file = Path("weapon_modifiers.json")
    output_dir = Path("contributions/weapon_modifiers")
    
    if not modifiers_file.exists():
        print(f"File not found: {modifiers_file}")
        return 0
    
    with open(modifiers_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        modifiers = data.get("modifiers", data) if isinstance(data, dict) else data
    
    if not isinstance(modifiers, list):
        modifiers = list(modifiers.values()) if isinstance(modifiers, dict) else [modifiers]
    
    count = 0
    for modifier in modifiers:
        modifier_id = modifier.get('id')
        if not modifier_id:
            print(f"Warning: Modifier missing id, skipping: {modifier.get('name', 'unknown')}")
            continue
        
        filename = f"{modifier_id}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(modifier, f, indent=2, ensure_ascii=False)
        
        count += 1
        print(f"  Created: {filename}")
    
    print(f"Split {count} weapon modifiers into individual files")
    return count

def create_readme_files():
    """Create README files in each contributions folder."""
    
    npcs_readme = """# NPC Contributions

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
"""
    
    rooms_readme = """# Room Contributions

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
"""
    
    items_readme = """# Item Contributions

This folder contains individual item definition files.

## File Format

Each file should be named `{item_id}.json` and contain a single item definition.

## Required Fields

- `item_id`: Unique identifier (must match filename)
- `name`: Display name
- `description`: Item description
- `item_type`: One of: weapon, armor, consumable, item, tool
- `value`: Base value in coins

## Example

See `shortsword.json` for a complete example.

## Validation

All item files are automatically validated on pull request.
"""
    
    shop_items_readme = """# Shop Item Contributions

This folder contains individual shop item definition files.

Shop items are items that can be sold by merchants.

## File Format

Each file should be named `{item_id}.json` and contain a single shop item definition.

## Required Fields

- `item_id`: Unique identifier (must match filename)
- `name`: Display name
- `description`: Item description
- `item_type`: One of: weapon, armor, consumable, item, tool
- `value`: Base price in coins

## Example

See shop item examples for complete structure.

## Validation

All shop item files are automatically validated on pull request.
"""
    
    planets_readme = """# Planet Contributions

This folder contains individual planet definition files.

Planets represent the cosmic influence on a character's origin and abilities.

## File Format

Each file should be named `{planet_id}.json` and contain a single planet definition.

## Required Fields

- `planet_id`: Unique identifier (must match filename)
- `name`: Display name
- `theme`: Theme description
- `cosmic_role`: Role description
- `description`: Planet description
- `attribute_bonuses`: Object with physical, mental, spiritual, social bonuses
- `starting_skills`: Object with skill names and values
- `gift_maneuver`: Maneuver ID granted by this planet
- `passive_effect`: Description of passive effect
- `color`: Display color

## Example

See `veyra.json` for a complete example.

## Validation

All planet files are automatically validated on pull request.
"""
    
    races_readme = """# Race Contributions

This folder contains individual race definition files.

Races define the biological and cultural traits of character origins.

## File Format

Each file should be named `{race_id}.json` and contain a single race definition.

## Required Fields

- `race_id`: Unique identifier (must match filename)
- `name`: Display name
- `description`: Race description
- `cultural_traits`: Array of cultural trait strings
- `attribute_modifiers`: Object with physical, mental, spiritual, social modifiers
- `starting_skills`: Object with skill names and values
- `color`: Display color

## Optional Fields

- `free_points`: Number of free attribute points (for humans, typically 2)

## Example

See `human.json` for a complete example.

## Validation

All race files are automatically validated on pull request.
"""
    
    starsigns_readme = """# Starsign Contributions

This folder contains individual starsign definition files.

Starsigns represent fate at birth and provide permanent character traits.

## File Format

Each file should be named `{starsign_id}.json` and contain a single starsign definition.

## Required Fields

- `starsign_id`: Unique identifier (must match filename)
- `name`: Display name
- `theme`: Theme description
- `description`: Starsign description
- `attribute_modifiers`: Object with physical, mental, spiritual, social modifiers (+2 to one, -1 to another)
- `fated_mark`: Object with name and description of the fated mark
- `color`: Display color

## Example

See `ash_serpent.json` for a complete example.

## Validation

All starsign files are automatically validated on pull request.
"""
    
    maneuvers_readme = """# Maneuver Contributions

This folder contains individual maneuver definition files.

Maneuvers are special abilities that characters can learn and use in combat.

## File Format

Each file should be named `{maneuver_id}.json` and contain a single maneuver definition.

## Required Fields

- `maneuver_id`: Unique identifier (must match filename)
- `name`: Display name
- `tier`: One of: Lower, Mid, Higher, Epic
- `description`: Maneuver description
- `required_skills`: Object with skill requirements
- `required_level`: Minimum level required
- `attributes`: Array of attribute types (physical, mental, spiritual, social)
- `cost`: Object with resource costs (stamina, mana, etc.)
- `cooldown`: Cooldown in turns
- `effects`: Object with success, critical, failure, critical_failure effects

## Example

See `brace.json` for a complete example.

## Validation

All maneuver files are automatically validated on pull request.
"""
    
    weapons_readme = """# Weapon Template Contributions

This folder contains individual weapon template definition files.

Weapon templates define the base properties of weapon types that can be used to create actual weapon items.

## File Format

Each file should be named `{id}.json` and contain a single weapon template definition.

## Required Fields

- `id`: Unique identifier (must match filename)
- `name`: Display name
- `category`: One of: Melee, Ranged
- `class`: Weapon class (Sword, Dagger, Mace, etc.)
- `hands`: Number of hands required (1 or 2)
- `range`: Attack range (0 for melee, >0 for ranged)
- `damage_min`: Minimum damage
- `damage_max`: Maximum damage
- `damage_type`: One of: slashing, piercing, bludgeoning
- `crit_chance`: Critical hit chance (0.0 to 1.0)
- `speed_cost`: Speed cost multiplier
- `durability`: Base durability value
- `description`: Weapon description

## Example

See `longsword.json` for a complete example.

## Validation

All weapon template files are automatically validated on pull request.
"""
    
    weapon_modifiers_readme = """# Weapon Modifier Contributions

This folder contains individual weapon modifier definition files.

Weapon modifiers define material properties that can be applied to weapon templates to create variant weapons.

## File Format

Each file should be named `{id}.json` and contain a single weapon modifier definition.

## Required Fields

- `id`: Unique identifier (must match filename)
- `name`: Display name
- `damage_bonus`: Damage bonus (can be negative)
- `crit_bonus`: Critical hit chance bonus (0.0 to 1.0)
- `speed_multiplier`: Speed multiplier (1.0 = no change)
- `durability_bonus`: Durability bonus (can be negative)
- `notes`: Description of the modifier

## Optional Fields

- `damage_type_override`: Override the weapon's damage type (e.g., "piercing")

## Example

See `bone.json` for a complete example.

## Validation

All weapon modifier files are automatically validated on pull request.
"""
    
    readmes = {
        "contributions/npcs/README.md": npcs_readme,
        "contributions/rooms/README.md": rooms_readme,
        "contributions/items/README.md": items_readme,
        "contributions/shop_items/README.md": shop_items_readme,
        "contributions/planets/README.md": planets_readme,
        "contributions/races/README.md": races_readme,
        "contributions/starsigns/README.md": starsigns_readme,
        "contributions/maneuvers/README.md": maneuvers_readme,
        "contributions/weapons/README.md": weapons_readme,
        "contributions/weapon_modifiers/README.md": weapon_modifiers_readme
    }
    
    for filepath, content in readmes.items():
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created: {filepath}")

def main():
    """Main function to split all data files."""
    print("="*60)
    print("Splitting consolidated JSON files into individual files")
    print("="*60)
    
    # Create directory structure
    print("\n1. Creating directory structure...")
    create_contributions_structure()
    
    # Split files
    print("\n2. Splitting NPCs...")
    npc_count = split_npcs()
    
    print("\n3. Splitting rooms...")
    room_count = split_rooms()
    
    print("\n4. Splitting items...")
    item_count = split_items()
    
    print("\n5. Splitting shop items...")
    shop_item_count = split_shop_items()
    
    print("\n6. Splitting planets...")
    planet_count = split_planets()
    
    print("\n7. Splitting races...")
    race_count = split_races()
    
    print("\n8. Splitting starsigns...")
    starsign_count = split_starsigns()
    
    print("\n9. Splitting maneuvers...")
    maneuver_count = split_maneuvers()
    
    print("\n10. Splitting weapons...")
    weapon_count = split_weapons()
    
    print("\n11. Splitting weapon modifiers...")
    modifier_count = split_weapon_modifiers()
    
    # Create README files
    print("\n12. Creating README files...")
    create_readme_files()
    
    # Summary
    print("\n" + "="*60)
    print("Summary:")
    print(f"  NPCs: {npc_count} files")
    print(f"  Rooms: {room_count} files")
    print(f"  Items: {item_count} files")
    print(f"  Shop Items: {shop_item_count} files")
    print(f"  Planets: {planet_count} files")
    print(f"  Races: {race_count} files")
    print(f"  Starsigns: {starsign_count} files")
    print(f"  Maneuvers: {maneuver_count} files")
    print(f"  Weapons: {weapon_count} files")
    print(f"  Weapon Modifiers: {modifier_count} files")
    print("="*60)
    print("\n✅ Data splitting complete!")
    print("\nNote: Original files in mud_data/ are preserved.")
    print("The server will now load from contributions/ folders.")

if __name__ == "__main__":
    main()
