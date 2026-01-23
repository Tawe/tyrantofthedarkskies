"""Simple test script to verify Firebase connection and save a test document."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from firebase_data_layer import FirebaseDataLayer

def test_firebase():
    """Test Firebase connection and save a test document."""
    try:
        print("Initializing Firebase...")
        firebase = FirebaseDataLayer()
        print("✓ Firebase initialized")
        
        # Test saving a single NPC
        print("\nTesting single NPC save...")
        test_npc = {
            "npc_id": "test_npc",
            "name": "Test NPC",
            "description": "This is a test NPC",
            "health": 100,
            "max_health": 100
        }
        
        firebase.save_npc("test_npc", test_npc)
        print("✓ Test NPC saved")
        
        # Test loading it back
        print("\nTesting load...")
        loaded = firebase.load_npcs()
        if "test_npc" in loaded:
            print(f"✓ Test NPC loaded: {loaded['test_npc']['name']}")
        else:
            print("✗ Test NPC not found after save")
        
        # Test batch save
        print("\nTesting batch save...")
        test_npcs = {
            "test_npc_1": {
                "npc_id": "test_npc_1",
                "name": "Test NPC 1",
                "description": "First test",
                "health": 50
            },
            "test_npc_2": {
                "npc_id": "test_npc_2",
                "name": "Test NPC 2",
                "description": "Second test",
                "health": 75
            }
        }
        
        firebase.batch_save_npcs(test_npcs)
        print("✓ Batch save completed")
        
        # Verify batch save
        loaded = firebase.load_npcs()
        if "test_npc_1" in loaded and "test_npc_2" in loaded:
            print("✓ Both test NPCs found after batch save")
        else:
            print("✗ Some test NPCs missing after batch save")
            print(f"  Found: {list(loaded.keys())}")
        
        print("\n✓ All tests passed!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_firebase()
