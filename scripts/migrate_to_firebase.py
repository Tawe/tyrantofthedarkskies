"""Script to migrate JSON data to Firebase."""

import json
import os
import sys

# Add parent directory to path to import firebase_data_layer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase_data_layer import FirebaseDataLayer

def migrate_json_to_firebase():
    """Migrate all JSON files to Firebase."""
    try:
        firebase = FirebaseDataLayer()
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        print("Make sure firebase-service-account.json exists in the project root.")
        return
    
    data_dir = "mud_data"
    
    print("Starting migration to Firebase...")
    print("=" * 60)
    
    # Migrate rooms
    print("\nMigrating rooms...")
    rooms_dict = {}
    
    # Try contributions folder first
    contributions_rooms_dir = "contributions/rooms"
    if os.path.exists(contributions_rooms_dir):
        try:
            for filename in os.listdir(contributions_rooms_dir):
                if filename.endswith('.json') and filename != 'README.md':
                    filepath = os.path.join(contributions_rooms_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        room_data = json.load(f)
                        if 'room_id' in room_data:
                            rooms_dict[room_data['room_id']] = room_data
            if rooms_dict:
                print(f"  Found {len(rooms_dict)} rooms in contributions/rooms/")
        except Exception as e:
            print(f"  ✗ Error loading from contributions/rooms/: {e}")
    
    # Fallback to consolidated file
    if not rooms_dict:
        rooms_file = os.path.join(data_dir, "rooms.json")
        if os.path.exists(rooms_file):
            try:
                with open(rooms_file, 'r') as f:
                    rooms_data = json.load(f)
                    # Handle both list and dict formats
                    if isinstance(rooms_data, list):
                        rooms_dict = {room['room_id']: room for room in rooms_data}
                    elif isinstance(rooms_data, dict) and 'rooms' in rooms_data:
                        rooms_dict = {room['room_id']: room for room in rooms_data['rooms']}
                    else:
                        rooms_dict = rooms_data
            except Exception as e:
                print(f"  ✗ Error loading from {rooms_file}: {e}")
    
    # Save to Firebase
    if rooms_dict:
        try:
            print(f"  Saving {len(rooms_dict)} rooms to Firebase...")
            firebase.batch_save_rooms(rooms_dict)
            print(f"  ✓ Successfully migrated {len(rooms_dict)} rooms to Firebase")
        except Exception as e:
            print(f"  ✗ Error migrating rooms to Firebase: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  ⚠ No rooms found to migrate")
    
    # Migrate NPCs
    print("\nMigrating NPCs...")
    npcs_dict = {}
    
    # Try contributions folder first
    contributions_npcs_dir = "contributions/npcs"
    if os.path.exists(contributions_npcs_dir):
        try:
            for filename in os.listdir(contributions_npcs_dir):
                if filename.endswith('.json') and filename != 'README.md':
                    filepath = os.path.join(contributions_npcs_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        npc_data = json.load(f)
                        if 'npc_id' in npc_data:
                            npcs_dict[npc_data['npc_id']] = npc_data
            if npcs_dict:
                print(f"  Found {len(npcs_dict)} NPCs in contributions/npcs/")
        except Exception as e:
            print(f"  ✗ Error loading from contributions/npcs/: {e}")
    
    # Fallback to consolidated file
    if not npcs_dict:
        npcs_file = os.path.join(data_dir, "npcs.json")
        if os.path.exists(npcs_file):
            try:
                with open(npcs_file, 'r') as f:
                    npcs_data = json.load(f)
                    # Handle both list and dict formats
                    if isinstance(npcs_data, list):
                        npcs_dict = {npc['npc_id']: npc for npc in npcs_data}
                    else:
                        npcs_dict = {npc['npc_id']: npc for npc in npcs_data.values()} if isinstance(npcs_data, dict) else {}
            except Exception as e:
                print(f"  ✗ Error loading from {npcs_file}: {e}")
    
    # Save to Firebase
    if npcs_dict:
        try:
            print(f"  Saving {len(npcs_dict)} NPCs to Firebase...")
            firebase.batch_save_npcs(npcs_dict)
            print(f"  ✓ Successfully migrated {len(npcs_dict)} NPCs to Firebase")
        except Exception as e:
            print(f"  ✗ Error migrating NPCs to Firebase: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  ⚠ No NPCs found to migrate")
    
    # Migrate items
    print("\nMigrating items...")
    items_dict = {}
    
    # Try contributions folder first (check all subfolders)
    contributions_items_dir = "contributions/items"
    if os.path.exists(contributions_items_dir):
        try:
            subfolders = ["weapons", "armor", "objects"]
            for subfolder in subfolders:
                subfolder_path = os.path.join(contributions_items_dir, subfolder)
                if os.path.exists(subfolder_path):
                    for filename in os.listdir(subfolder_path):
                        if filename.endswith('.json'):
                            filepath = os.path.join(subfolder_path, filename)
                            with open(filepath, 'r', encoding='utf-8') as f:
                                item_data = json.load(f)
                                if 'item_id' in item_data:
                                    items_dict[item_data['item_id']] = item_data
            if items_dict:
                print(f"  Found {len(items_dict)} items in contributions/items/")
        except Exception as e:
            print(f"  ✗ Error loading from contributions/items/: {e}")
    
    # Fallback to consolidated file
    if not items_dict:
        items_file = os.path.join(data_dir, "items.json")
        if os.path.exists(items_file):
            try:
                with open(items_file, 'r') as f:
                    items_data = json.load(f)
                    if isinstance(items_data, list):
                        items_dict = {item['item_id']: item for item in items_data}
                    elif isinstance(items_data, dict):
                        items_dict = items_data
            except Exception as e:
                print(f"  ✗ Error loading from {items_file}: {e}")
    
    # Save to Firebase
    if items_dict:
        try:
            print(f"  Saving {len(items_dict)} items to Firebase...")
            firebase.batch_save_items(items_dict)
            print(f"  ✓ Successfully migrated {len(items_dict)} items to Firebase")
        except Exception as e:
            print(f"  ✗ Error migrating items to Firebase: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  ⚠ No items found to migrate")
    
    # Migrate shop items
    print("\nMigrating shop items...")
    shop_items_dict = {}
    
    # Try contributions folder first
    contributions_shop_items_dir = "contributions/shop_items"
    if os.path.exists(contributions_shop_items_dir):
        try:
            for filename in os.listdir(contributions_shop_items_dir):
                if filename.endswith('.json') and filename != 'README.md':
                    filepath = os.path.join(contributions_shop_items_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        item_data = json.load(f)
                        if 'item_id' in item_data:
                            shop_items_dict[item_data['item_id']] = item_data
            if shop_items_dict:
                print(f"  Found {len(shop_items_dict)} shop items in contributions/shop_items/")
        except Exception as e:
            print(f"  ✗ Error loading from contributions/shop_items/: {e}")
    
    # Fallback to consolidated file
    if not shop_items_dict:
        shop_items_file = os.path.join(data_dir, "shop_items.json")
        if os.path.exists(shop_items_file):
            try:
                with open(shop_items_file, 'r') as f:
                    shop_items_data = json.load(f)
                    if isinstance(shop_items_data, list):
                        shop_items_dict = {item['item_id']: item for item in shop_items_data}
                    elif isinstance(shop_items_data, dict):
                        shop_items_dict = shop_items_data
            except Exception as e:
                print(f"  ✗ Error loading from {shop_items_file}: {e}")
    
    # Save to Firebase
    if shop_items_dict:
        try:
            print(f"  Saving {len(shop_items_dict)} shop items to Firebase...")
            firebase.batch_save_shop_items(shop_items_dict)
            print(f"  ✓ Successfully migrated {len(shop_items_dict)} shop items to Firebase")
        except Exception as e:
            print(f"  ✗ Error migrating shop items to Firebase: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"  ⚠ No shop items found to migrate")
    
    # Migrate players
    print("\nMigrating players...")
    if os.path.exists(data_dir):
        player_files = [f for f in os.listdir(data_dir) if f.startswith('player_') and f.endswith('.json')]
        if player_files:
            for player_file in player_files:
                try:
                    player_name = player_file.replace('player_', '').replace('.json', '')
                    with open(os.path.join(data_dir, player_file), 'r') as f:
                        player_data = json.load(f)
                        firebase.save_player(player_name, player_data)
                        print(f"  ✓ Migrated player: {player_name}")
                except Exception as e:
                    print(f"  ✗ Error migrating player {player_file}: {e}")
        else:
            print("  ⚠ No player files found")
    else:
        print(f"  ⚠ {data_dir} directory not found")
    
    # Migrate config files
    print("\nMigrating config files...")
    config_files = {
        'admin_config': 'admin_config.json',
        'world_time': 'world_time.json',
        'npc_schedules': 'npc_schedules.json',
        'store_hours': 'store_hours.json'
    }
    
    for config_name, filename in config_files.items():
        config_file = os.path.join(data_dir, filename)
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    firebase.save_config(config_name, config_data)
                    print(f"  ✓ Migrated {config_name}")
            except Exception as e:
                print(f"  ✗ Error migrating {config_name}: {e}")
        else:
            print(f"  ⚠ {config_file} not found, skipping {config_name}")
    
    # Migrate game data files (from contributions or root)
    print("\nMigrating game data files...")
    game_data_mapping = {
        'maneuvers': ('contributions/maneuvers', 'maneuver_id', 'maneuvers.json'),
        'planets': ('contributions/planets', 'planet_id', 'planets.json'),
        'races': ('contributions/races', 'race_id', 'races.json'),
        'starsigns': ('contributions/starsigns', 'starsign_id', 'starsigns.json'),
        'weapons': ('contributions/weapons', 'id', 'weapons.json'),
        'weapon_modifiers': ('contributions/weapon_modifiers', 'id', 'weapon_modifiers.json')
    }
    
    for data_type, (contrib_dir, id_field, root_filename) in game_data_mapping.items():
        items = []
        
        # Try contributions folder first
        if os.path.exists(contrib_dir):
            try:
                for filename in os.listdir(contrib_dir):
                    if filename.endswith('.json') and filename != 'README.md':
                        filepath = os.path.join(contrib_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            item_data = json.load(f)
                            items.append(item_data)
                if items:
                    print(f"  Found {len(items)} {data_type} in {contrib_dir}/")
            except Exception as e:
                print(f"  ✗ Error loading from {contrib_dir}/: {e}")
        
        # Fallback to root-level file
        if not items and os.path.exists(root_filename):
            try:
                with open(root_filename, 'r') as f:
                    data = json.load(f)
                    # Handle different JSON structures
                    if isinstance(data, dict) and data_type in data:
                        items = data[data_type]
                    elif isinstance(data, list):
                        items = data
                    elif isinstance(data, dict):
                        # If it's a dict of items, convert to list
                        items = list(data.values())
                    else:
                        items = [data]
            except Exception as e:
                print(f"  ✗ Error loading from {root_filename}: {e}")
        
        # Save to Firebase
        if items:
            try:
                count = 0
                for item in items:
                    # Determine ID field
                    if id_field == 'id':
                        item_id = item.get('id', str(hash(str(item))))
                    else:
                        item_id = item.get(id_field, item.get('id', str(hash(str(item)))))
                    firebase.save_game_data(data_type, item_id, item)
                    count += 1
                print(f"  ✓ Migrated {count} {data_type}")
            except Exception as e:
                print(f"  ✗ Error migrating {data_type} to Firebase: {e}")
        else:
            print(f"  ⚠ No {data_type} found to migrate")
    
    print("\n" + "=" * 60)
    print("Migration complete!")
    print("\nNext steps:")
    print("1. Verify data in Firebase Console")
    print("2. Test the server with Firebase enabled")
    print("3. Keep JSON backups for at least 1 week")

if __name__ == "__main__":
    migrate_json_to_firebase()
