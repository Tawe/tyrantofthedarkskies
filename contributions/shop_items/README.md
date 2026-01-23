# Shop Item Contributions

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
