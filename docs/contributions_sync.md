# Automatic Contribution Sync to Firebase

This repository includes a GitHub Actions workflow that automatically syncs contribution files to Firebase when they're added or modified.

## How It Works

When you add or modify a JSON file in the `contributions/` directory and push to GitHub:

1. **GitHub Actions detects the change** - The workflow triggers on pushes/PRs that modify files in `contributions/**/*.json`
2. **Script identifies changed files** - Uses `git diff` to find which files were added/modified
3. **Files are synced to Firebase** - Each file is loaded and saved to the appropriate Firebase collection

## Supported Contribution Types

The sync script automatically handles these contribution types:

- **Maneuvers** (`contributions/maneuvers/`) → `game_data/maneuvers`
- **Planets** (`contributions/planets/`) → `game_data/planets`
- **Races** (`contributions/races/`) → `game_data/races`
- **Starsigns** (`contributions/starsigns/`) → `game_data/starsigns`
- **Weapons** (`contributions/weapons/`) → `game_data/weapons`
- **Weapon Modifiers** (`contributions/weapon_modifiers/`) → `game_data/weapon_modifiers`
- **Rooms** (`contributions/rooms/`) → `world/rooms`
- **NPCs** (`contributions/npcs/`) → `world/npcs`
- **Items** (`contributions/items/*/`) → `world/items`
- **Shop Items** (`contributions/shop_items/`) → `world/shop_items`

## Setup

### 1. Add Firebase Service Account Secret to GitHub

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `FIREBASE_SERVICE_ACCOUNT`
5. Value: Copy the entire contents of your `firebase-service-account.json` file (as a single-line JSON string)

**Important:** The value should be the JSON content as a string, not a file path. You can get it by running:
```bash
cat firebase-service-account.json | jq -c
```

Or manually copy the entire JSON object and ensure it's on a single line.

### 2. Test Locally (Optional)

You can test the sync script locally:

```bash
# Set environment variable
export FIREBASE_SERVICE_ACCOUNT='{"type":"service_account",...}'

# Run the sync script
python scripts/sync_contributions_to_firebase.py
```

## Usage

Simply add or modify JSON files in the `contributions/` directory and push to GitHub. The workflow will automatically:

- Detect the changed files
- Validate the JSON structure
- Extract the appropriate ID field
- Save to Firebase

## Workflow File

The workflow is defined in `.github/workflows/sync-contributions.yml` and runs:
- On pushes to `main` branch when `contributions/**/*.json` files change
- On pull requests to `main` branch when `contributions/**/*.json` files change

## Troubleshooting

### Workflow Not Running

- Check that files are actually in `contributions/` directory
- Verify files have `.json` extension
- Check GitHub Actions tab for workflow runs

### Sync Failing

- Verify `FIREBASE_SERVICE_ACCOUNT` secret is set correctly
- Check that JSON files have the required ID field (e.g., `maneuver_id`, `room_id`)
- Review workflow logs in GitHub Actions

### Files Not Syncing

- Ensure the file path matches one of the supported contribution directories
- Verify the JSON file has the correct ID field for its type
- Check that the file is valid JSON
