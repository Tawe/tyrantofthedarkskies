"""Firebase data layer abstraction."""

from .client import FirebaseClient
from firebase_admin import firestore
from typing import Dict, List, Optional, Any
import json

class FirebaseDataLayer:
    """Abstraction layer for Firebase operations."""
    
    def __init__(self):
        self.client = FirebaseClient()
        self.db = self.client.db
    
    # Player operations
    def load_player(self, player_name: str) -> Optional[Dict]:
        """Load player data from Firestore by player name."""
        doc_ref = self.db.collection('players').document(player_name)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def load_player_by_email(self, email: str) -> Optional[Dict]:
        """Load player data from Firestore by email."""
        # Query players collection for matching email
        players_ref = self.db.collection('players')
        query = players_ref.where(filter=firestore.FieldFilter('email', '==', email)).limit(1)
        docs = query.stream()
        for doc in docs:
            return doc.to_dict()
        return None
    
    def load_player_by_uid(self, uid: str) -> Optional[Dict]:
        """Load player data from Firestore by Firebase UID."""
        # Query players collection for matching firebase_uid
        players_ref = self.db.collection('players')
        query = players_ref.where(filter=firestore.FieldFilter('firebase_uid', '==', uid)).limit(1)
        docs = query.stream()
        for doc in docs:
            return doc.to_dict()
        return None
    
    def save_player(self, player_name: str, player_data: Dict):
        """Save player data to Firestore."""
        doc_ref = self.db.collection('players').document(player_name)
        # Create a copy to avoid modifying the original
        save_data = player_data.copy()
        save_data['last_updated'] = firestore.SERVER_TIMESTAMP
        doc_ref.set(save_data, merge=True)
    
    def delete_player(self, player_name: str):
        """Delete player from Firestore."""
        self.db.collection('players').document(player_name).delete()
    
    # World data operations
    def load_rooms(self) -> Dict[str, Dict]:
        """Load all rooms from Firestore."""
        rooms = {}
        docs = self.db.collection('world').document('rooms').collection('data').stream()
        for doc in docs:
            room_data = doc.to_dict()
            if room_data and 'room_id' in room_data:
                rooms[room_data['room_id']] = room_data
        return rooms
    
    def save_room(self, room_id: str, room_data: Dict):
        """Save a room to Firestore."""
        # Ensure parent document exists
        self.db.collection('world').document('rooms').set({'type': 'rooms'}, merge=True)
        # Save the room
        self.db.collection('world').document('rooms').collection('data').document(room_id).set(room_data)
    
    def load_npcs(self) -> Dict[str, Dict]:
        """Load all NPCs from Firestore."""
        npcs = {}
        docs = self.db.collection('world').document('npcs').collection('data').stream()
        for doc in docs:
            npc_data = doc.to_dict()
            if npc_data and 'npc_id' in npc_data:
                npcs[npc_data['npc_id']] = npc_data
        return npcs
    
    def save_npc(self, npc_id: str, npc_data: Dict):
        """Save an NPC to Firestore."""
        # Ensure parent document exists
        self.db.collection('world').document('npcs').set({'type': 'npcs'}, merge=True)
        # Save the NPC
        self.db.collection('world').document('npcs').collection('data').document(npc_id).set(npc_data)
    
    def load_items(self) -> Dict[str, Dict]:
        """Load all items from Firestore."""
        items = {}
        docs = self.db.collection('world').document('items').collection('data').stream()
        for doc in docs:
            item_data = doc.to_dict()
            if item_data and 'item_id' in item_data:
                items[item_data['item_id']] = item_data
        return items
    
    def save_item(self, item_id: str, item_data: Dict):
        """Save an item to Firestore."""
        # Ensure parent document exists
        self.db.collection('world').document('items').set({'type': 'items'}, merge=True)
        # Save the item
        self.db.collection('world').document('items').collection('data').document(item_id).set(item_data)
    
    def load_shop_items(self) -> Dict[str, Dict]:
        """Load all shop items from Firestore."""
        shop_items = {}
        docs = self.db.collection('world').document('shop_items').collection('data').stream()
        for doc in docs:
            item_data = doc.to_dict()
            if item_data and 'item_id' in item_data:
                shop_items[item_data['item_id']] = item_data
        return shop_items
    
    def save_shop_item(self, item_id: str, item_data: Dict):
        """Save a shop item to Firestore."""
        # Ensure parent document exists
        self.db.collection('world').document('shop_items').set({'type': 'shop_items'}, merge=True)
        # Save the shop item
        self.db.collection('world').document('shop_items').collection('data').document(item_id).set(item_data)
    
    # Config operations
    def load_config(self, config_name: str) -> Optional[Dict]:
        """Load a config document."""
        doc_ref = self.db.collection('config').document(config_name)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def save_config(self, config_name: str, config_data: Dict):
        """Save a config document."""
        self.db.collection('config').document(config_name).set(config_data)
    
    # Game data operations (static data)
    def load_game_data(self, data_type: str) -> Dict[str, Dict]:
        """Load static game data (maneuvers, races, etc.)."""
        data = {}
        docs = self.db.collection('game_data').document(data_type).collection('data').stream()
        for doc in docs:
            item_data = doc.to_dict()
            if not item_data:
                continue
            # Use appropriate ID field based on data type
            id_field = f"{data_type.rstrip('s')}_id"  # maneuver_id, race_id, etc.
            # Handle special cases
            if data_type == 'weapons' or data_type == 'weapon_modifiers':
                id_field = 'id'
            if id_field in item_data:
                data[item_data[id_field]] = item_data
            elif 'id' in item_data:
                data[item_data['id']] = item_data
        return data
    
    def save_game_data(self, data_type: str, item_id: str, item_data: Dict):
        """Save static game data item."""
        # Ensure parent document exists
        self.db.collection('game_data').document(data_type).set({'type': data_type}, merge=True)
        # Save the item
        self.db.collection('game_data').document(data_type).collection('data').document(item_id).set(item_data)
    
    # Batch operations
    def batch_save_rooms(self, rooms: Dict[str, Dict]):
        """Save multiple rooms in a batch."""
        # Ensure parent document exists
        self.db.collection('world').document('rooms').set({'type': 'rooms'}, merge=True)
        
        # Firestore batch limit is 500 operations
        rooms_ref = self.db.collection('world').document('rooms').collection('data')
        count = 0
        batch = self.db.batch()
        
        for room_id, room_data in rooms.items():
            # Clean the data - remove any None values or non-serializable types
            clean_data = self._clean_data(room_data)
            doc_ref = rooms_ref.document(room_id)
            batch.set(doc_ref, clean_data)
            count += 1
            # Commit every 500 operations
            if count % 500 == 0:
                try:
                    batch.commit()
                    print(f"    Committed batch of 500 rooms (total: {count})")
                except Exception as e:
                    print(f"    Error committing batch: {e}")
                    raise
                batch = self.db.batch()
        
        # Commit remaining operations
        if count > 0 and count % 500 != 0:
            try:
                batch.commit()
                print(f"    Committed final batch of {count % 500} rooms (total: {count})")
            except Exception as e:
                print(f"    Error committing final batch: {e}")
                raise
    
    def _clean_data(self, data: Dict) -> Dict:
        """Clean data to ensure it's Firestore-compatible."""
        clean = {}
        for key, value in data.items():
            # Skip None values
            if value is None:
                continue
            # Handle nested dicts
            if isinstance(value, dict):
                clean[key] = self._clean_data(value)
            # Handle lists
            elif isinstance(value, list):
                clean[key] = [self._clean_data(item) if isinstance(item, dict) else item for item in value]
            # Handle basic types
            elif isinstance(value, (str, int, float, bool)):
                clean[key] = value
            # Skip other types that aren't serializable
            else:
                clean[key] = str(value)
        return clean
    
    def batch_save_npcs(self, npcs: Dict[str, Dict]):
        """Save multiple NPCs in a batch."""
        # Ensure parent document exists
        self.db.collection('world').document('npcs').set({'type': 'npcs'}, merge=True)
        
        # Firestore batch limit is 500 operations
        npcs_ref = self.db.collection('world').document('npcs').collection('data')
        count = 0
        batch = self.db.batch()
        
        for npc_id, npc_data in npcs.items():
            # Clean the data - remove any None values or non-serializable types
            clean_data = self._clean_data(npc_data)
            doc_ref = npcs_ref.document(npc_id)
            batch.set(doc_ref, clean_data)
            count += 1
            # Commit every 500 operations
            if count % 500 == 0:
                try:
                    batch.commit()
                    print(f"    Committed batch of 500 NPCs (total: {count})")
                except Exception as e:
                    print(f"    Error committing batch: {e}")
                    raise
                batch = self.db.batch()
        
        # Commit remaining operations
        if count > 0 and count % 500 != 0:
            try:
                batch.commit()
                print(f"    Committed final batch of {count % 500} NPCs (total: {count})")
            except Exception as e:
                print(f"    Error committing final batch: {e}")
                raise
    
    def batch_save_items(self, items: Dict[str, Dict]):
        """Save multiple items in a batch."""
        # Ensure parent document exists
        self.db.collection('world').document('items').set({'type': 'items'}, merge=True)
        
        # Firestore batch limit is 500 operations
        items_ref = self.db.collection('world').document('items').collection('data')
        count = 0
        batch = self.db.batch()
        
        for item_id, item_data in items.items():
            # Clean the data - remove any None values or non-serializable types
            clean_data = self._clean_data(item_data)
            doc_ref = items_ref.document(item_id)
            batch.set(doc_ref, clean_data)
            count += 1
            # Commit every 500 operations
            if count % 500 == 0:
                batch.commit()
                batch = self.db.batch()
        
        # Commit remaining operations
        if count > 0 and count % 500 != 0:
            batch.commit()
    
    def batch_save_shop_items(self, shop_items: Dict[str, Dict]):
        """Save multiple shop items in a batch."""
        # Ensure parent document exists
        self.db.collection('world').document('shop_items').set({'type': 'shop_items'}, merge=True)
        
        # Firestore batch limit is 500 operations
        shop_items_ref = self.db.collection('world').document('shop_items').collection('data')
        count = 0
        batch = self.db.batch()
        
        for item_id, item_data in shop_items.items():
            # Clean the data - remove any None values or non-serializable types
            clean_data = self._clean_data(item_data)
            doc_ref = shop_items_ref.document(item_id)
            batch.set(doc_ref, clean_data)
            count += 1
            # Commit every 500 operations
            if count % 500 == 0:
                batch.commit()
                batch = self.db.batch()
        
        # Commit remaining operations
        if count > 0 and count % 500 != 0:
            batch.commit()
