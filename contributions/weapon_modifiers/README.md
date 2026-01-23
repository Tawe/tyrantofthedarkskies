# Weapon Modifier Contributions

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
