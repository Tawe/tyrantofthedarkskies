# Weapon Template Contributions

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
