# Item Contributions

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
