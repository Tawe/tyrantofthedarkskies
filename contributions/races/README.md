# Race Contributions

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
