#!/usr/bin/env python3
"""Quick script to sync a single room to Firebase."""

import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase.data_layer import FirebaseDataLayer

def sync_room(room_id):
    """Sync a single room to Firebase."""
    room_file = f"contributions/rooms/{room_id}.json"
    
    if not os.path.exists(room_file):
        print(f"Room file not found: {room_file}")
        return False
    
    try:
        # Initialize Firebase
        firebase = FirebaseDataLayer()
        print(f"✅ Firebase initialized")
        
        # Load room data
        with open(room_file, 'r', encoding='utf-8') as f:
            room_data = json.load(f)
        
        # Save to Firebase
        firebase.save_room(room_id, room_data)
        print(f"✅ Synced room '{room_id}' to Firebase")
        print(f"   NPCs: {room_data.get('npcs', [])}")
        print(f"   Combat tags: {room_data.get('combat_tags', [])}")
        return True
        
    except Exception as e:
        print(f"❌ Error syncing room: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        room_id = sys.argv[1]
    else:
        room_id = "kelp_plains"
    
    sync_room(room_id)
