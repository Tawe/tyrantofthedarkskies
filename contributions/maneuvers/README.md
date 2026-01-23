# Maneuver Contributions

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
