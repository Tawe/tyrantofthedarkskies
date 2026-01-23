# Planet Contributions

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
