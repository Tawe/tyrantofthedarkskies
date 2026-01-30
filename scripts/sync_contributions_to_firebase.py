#!/usr/bin/env python3
"""Sync contribution files to Firebase when they're added or modified."""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import firebase modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase.data_layer import FirebaseDataLayer

# Mapping of contribution directories to Firebase data types and ID fields
CONTRIBUTION_MAPPING = {
    'contributions/maneuvers': {
        'type': 'game_data',
        'data_type': 'maneuvers',
        'id_field': 'maneuver_id',
        'save_method': 'save_game_data'
    },
    'contributions/planets': {
        'type': 'game_data',
        'data_type': 'planets',
        'id_field': 'planet_id',
        'save_method': 'save_game_data'
    },
    'contributions/races': {
        'type': 'game_data',
        'data_type': 'races',
        'id_field': 'race_id',
        'save_method': 'save_game_data'
    },
    'contributions/starsigns': {
        'type': 'game_data',
        'data_type': 'starsigns',
        'id_field': 'starsign_id',
        'save_method': 'save_game_data'
    },
    'contributions/weapons': {
        'type': 'game_data',
        'data_type': 'weapons',
        'id_field': 'id',
        'save_method': 'save_game_data'
    },
    'contributions/weapon_modifiers': {
        'type': 'game_data',
        'data_type': 'weapon_modifiers',
        'id_field': 'id',
        'save_method': 'save_game_data'
    },
    'contributions/rooms': {
        'type': 'world',
        'data_type': 'rooms',
        'id_field': 'room_id',
        'save_method': 'save_room'
    },
    'contributions/npcs': {
        'type': 'world',
        'data_type': 'npcs',
        'id_field': 'npc_id',
        'save_method': 'save_npc'
    },
    'contributions/creatures': {
        'type': 'world',
        'data_type': 'npcs',
        'id_field': 'template_id',
        'save_method': 'save_npc'
    },
    'contributions/items/armor': {
        'type': 'world',
        'data_type': 'items',
        'id_field': 'item_id',
        'save_method': 'save_item'
    },
    'contributions/items/objects': {
        'type': 'world',
        'data_type': 'items',
        'id_field': 'item_id',
        'save_method': 'save_item'
    },
    'contributions/items/weapons': {
        'type': 'world',
        'data_type': 'items',
        'id_field': 'item_id',
        'save_method': 'save_item'
    },
    'contributions/shop_items': {
        'type': 'world',
        'data_type': 'shop_items',
        'id_field': 'item_id',
        'save_method': 'save_shop_item'
    }
}

def get_changed_files():
    """Get list of changed JSON files in contributions directory."""
    changed_files = []
    
    # Try to use git diff to detect changed files (works in GitHub Actions)
    try:
        import subprocess
        # Get files changed in the last commit (for push events)
        # Or files changed compared to base branch (for PR events)
        result = subprocess.run(
            ['git', 'diff', '--name-only', '--diff-filter=AM', 'HEAD~1', 'HEAD'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if result.returncode == 0:
            changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            print(f"Found {len(changed_files)} changed file(s) via git diff")
    except Exception as e:
        print(f"Warning: Could not use git diff: {e}")
    
    # Fallback: Check GitHub event (for PR events or if git diff fails)
    if not changed_files and os.getenv('GITHUB_EVENT_PATH'):
        try:
            with open(os.getenv('GITHUB_EVENT_PATH'), 'r') as f:
                event = json.load(f)
            
            # For push events
            if 'commits' in event:
                for commit in event.get('commits', []):
                    changed_files.extend(commit.get('added', []))
                    changed_files.extend(commit.get('modified', []))
        except Exception as e:
            print(f"Warning: Could not parse GitHub event: {e}")
    
    # Final fallback: scan all contribution files (for local testing)
    if not changed_files:
        print("No changed files detected, scanning all contribution files...")
        for contrib_dir in CONTRIBUTION_MAPPING.keys():
            if os.path.exists(contrib_dir):
                for root, dirs, files in os.walk(contrib_dir):
                    for filename in files:
                        if filename.endswith('.json') and filename != 'README.md':
                            filepath = os.path.join(root, filename)
                            # Make path relative to repo root
                            rel_path = os.path.relpath(filepath, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                            changed_files.append(rel_path.replace('\\', '/'))
    
    # Filter to only JSON files in contributions directory
    contribution_files = [
        f for f in changed_files 
        if f.startswith('contributions/') and f.endswith('.json')
    ]
    
    return contribution_files

def get_contribution_type(filepath):
    """Determine the contribution type based on file path."""
    # Normalize path
    filepath = filepath.replace('\\', '/')
    
    # Find matching directory
    for contrib_dir, mapping in CONTRIBUTION_MAPPING.items():
        if filepath.startswith(contrib_dir + '/'):
            return mapping
    
    # Try to match parent directory for nested structures
    parts = filepath.split('/')
    if len(parts) >= 3:
        parent_dir = '/'.join(parts[:3])  # e.g., 'contributions/items/armor'
        if parent_dir in CONTRIBUTION_MAPPING:
            return CONTRIBUTION_MAPPING[parent_dir]
    
    return None

def sync_file_to_firebase(filepath, firebase):
    """Sync a single contribution file to Firebase."""
    if not os.path.exists(filepath):
        print(f"  ⚠ File not found: {filepath}")
        return False
    
    # Determine contribution type
    mapping = get_contribution_type(filepath)
    if not mapping:
        print(f"  ⚠ Unknown contribution type for: {filepath}")
        return False
    
    try:
        # Load JSON file
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get ID field
        id_field = mapping['id_field']
        if id_field not in data:
            print(f"  ✗ Missing {id_field} in {filepath}")
            return False
        
        item_id = data[id_field]

        # Creature templates use template_id; game loads NPCs by npc_id — ensure npc_id is set
        if id_field == 'template_id':
            data = dict(data)
            data['npc_id'] = item_id
        
        # Save to Firebase
        save_method = getattr(firebase, mapping['save_method'])
        
        if mapping['type'] == 'game_data':
            save_method(mapping['data_type'], item_id, data)
        else:
            save_method(item_id, data)
        
        print(f"  ✅ Synced {mapping['data_type']}: {item_id}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON in {filepath}: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error syncing {filepath}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main sync function."""
    print("=" * 60)
    print("Syncing Contributions to Firebase")
    print("=" * 60)
    
    # Initialize Firebase
    try:
        firebase = FirebaseDataLayer()
        print("✅ Firebase initialized")
    except Exception as e:
        print(f"✗ Error initializing Firebase: {e}")
        print("Make sure FIREBASE_SERVICE_ACCOUNT environment variable is set.")
        sys.exit(1)
    
    # Get changed files
    changed_files = get_changed_files()
    
    if not changed_files:
        print("No contribution files to sync.")
        return
    
    print(f"\nFound {len(changed_files)} file(s) to sync:")
    for f in changed_files:
        print(f"  - {f}")
    
    # Sync each file
    print("\nSyncing files...")
    success_count = 0
    error_count = 0
    
    for filepath in changed_files:
        if sync_file_to_firebase(filepath, firebase):
            success_count += 1
        else:
            error_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Sync complete: {success_count} succeeded, {error_count} failed")
    print("=" * 60)
    
    if error_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
