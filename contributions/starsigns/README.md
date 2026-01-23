# Starsign Contributions

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
