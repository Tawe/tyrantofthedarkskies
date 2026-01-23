#!/usr/bin/env python3

import json
import os
import sys

class RoomEditor:
    def __init__(self):
        # Use contributions/rooms/ directory for individual files
        self.rooms_dir = "contributions/rooms"
        self.fallback_file = "mud_data/rooms.json"
        self.rooms = {}
        self.load_rooms()
        
    def load_rooms(self):
        """Load rooms from individual files or consolidated file"""
        try:
            # Try loading from contributions/rooms/ first
            if os.path.exists(self.rooms_dir):
                for filename in os.listdir(self.rooms_dir):
                    if filename.endswith('.json') and filename != 'README.md':
                        filepath = os.path.join(self.rooms_dir, filename)
                        try:
                            with open(filepath, 'r') as f:
                                room_data = json.load(f)
                                room_id = room_data.get('room_id')
                                if room_id:
                                    self.rooms[room_id] = room_data
                        except Exception as e:
                            print(f"Error loading {filename}: {e}")
                if self.rooms:
                    print(f"Loaded {len(self.rooms)} rooms from {self.rooms_dir}/")
                    return
            
            # Fallback to consolidated file
            if os.path.exists(self.fallback_file):
                with open(self.fallback_file, 'r') as f:
                    data = json.load(f)
                    rooms_list = data.get("rooms", data) if isinstance(data, dict) else data
                    for room_data in rooms_list:
                        room_id = room_data.get("room_id")
                        if room_id:
                            self.rooms[room_id] = room_data
                print(f"Loaded {len(self.rooms)} rooms from {self.fallback_file}")
            else:
                print(f"Warning: No rooms found. Creating new structure.")
                self.rooms = {}
        except Exception as e:
            print(f"Error loading rooms: {e}")
            
    def save_rooms(self):
        """Save rooms to individual files in contributions/rooms/"""
        try:
            # Ensure directory exists
            os.makedirs(self.rooms_dir, exist_ok=True)
            
            # Save each room as individual file
            for room_id, room_data in self.rooms.items():
                filename = f"{room_id}.json"
                filepath = os.path.join(self.rooms_dir, filename)
                with open(filepath, 'w') as f:
                    json.dump(room_data, f, indent=2, ensure_ascii=False)
            
            print(f"Saved {len(self.rooms)} rooms to {self.rooms_dir}/")
        except Exception as e:
            print(f"Error saving rooms: {e}")
            
    def list_rooms(self):
        """List all rooms"""
        if not self.rooms:
            print("No rooms found.")
            return
            
        print("\n=== Room List ===")
        for room_id, room in sorted(self.rooms.items()):
            print(f"\n{room_id}: {room['name']}")
            print(f"  Description: {room['description'][:80]}...")
            if room['exits']:
                exits = ", ".join([f"{dir}->{target}" for dir, target in room['exits'].items()])
                print(f"  Exits: {exits}")
            if room.get('flags'):
                print(f"  Flags: {', '.join(room['flags'])}")
            if room.get('items'):
                print(f"  Items: {', '.join(room['items'])}")
            if room.get('npcs'):
                print(f"  NPCs: {', '.join(room['npcs'])}")
                
    def create_room(self, room_id, name):
        """Create a new room"""
        if room_id in self.rooms:
            print(f"Room '{room_id}' already exists.")
            return False
            
        new_room = {
            "room_id": room_id,
            "name": name,
            "description": "A newly created room. Description pending.",
            "exits": {},
            "items": [],
            "npcs": [],
            "flags": []
        }
        
        self.rooms[room_id] = new_room
        print(f"Room '{room_id}' created successfully!")
        return True
        
    def edit_room(self, room_id, field, value):
        """Edit a room property"""
        if room_id not in self.rooms:
            print(f"Room '{room_id}' not found.")
            return False
            
        room = self.rooms[room_id]
        
        if field == "name":
            room[field] = value
            print(f"Room name updated to: {value}")
        elif field == "description":
            room[field] = value
            print("Room description updated.")
        elif field == "add_exit":
            parts = value.split(" ", 1)
            if len(parts) == 2:
                direction, target = parts
                room["exits"][direction] = target
                print(f"Exit '{direction}' to '{target}' added.")
            else:
                print("Usage: add_exit <direction> <target_room>")
                return False
        elif field == "remove_exit":
            if value in room["exits"]:
                del room["exits"][value]
                print(f"Exit '{value}' removed.")
            else:
                print(f"Exit '{value}' does not exist.")
                return False
        elif field == "add_flag":
            if value not in room.get("flags", []):
                room.setdefault("flags", []).append(value)
                print(f"Flag '{value}' added.")
            else:
                print(f"Flag '{value}' already exists.")
        elif field == "remove_flag":
            if value in room.get("flags", []):
                room["flags"].remove(value)
                print(f"Flag '{value}' removed.")
            else:
                print(f"Flag '{value}' does not exist.")
        elif field == "add_item":
            room.setdefault("items", []).append(value)
            print(f"Item '{value}' added to room.")
        elif field == "remove_item":
            if value in room.get("items", []):
                room["items"].remove(value)
                print(f"Item '{value}' removed from room.")
            else:
                print(f"Item '{value}' not found in room.")
        elif field == "add_npc":
            room.setdefault("npcs", []).append(value)
            print(f"NPC '{value}' added to room.")
        elif field == "remove_npc":
            if value in room.get("npcs", []):
                room["npcs"].remove(value)
                print(f"NPC '{value}' removed from room.")
            else:
                print(f"NPC '{value}' not found in room.")
        else:
            print(f"Unknown field: {field}")
            return False
            
        return True
        
    def delete_room(self, room_id):
        """Delete a room"""
        if room_id not in self.rooms:
            print(f"Room '{room_id}' not found.")
            return False
            
        if room_id == "start":
            print("Cannot delete the starting room.")
            return False
            
        del self.rooms[room_id]
        
        # Remove all exits to this room
        for room in self.rooms.values():
            exits_to_remove = [dir for dir, target in room["exits"].items() if target == room_id]
            for exit_dir in exits_to_remove:
                del room["exits"][exit_dir]
                
        print(f"Room '{room_id}' deleted and all exits to it removed.")
        return True
        
    def show_room(self, room_id):
        """Show detailed information about a specific room"""
        if room_id not in self.rooms:
            print(f"Room '{room_id}' not found.")
            return
            
        room = self.rooms[room_id]
        print(f"\n=== Room Details: {room_id} ===")
        print(f"Name: {room['name']}")
        print(f"Description: {room['description']}")
        
        if room['exits']:
            print("Exits:")
            for direction, target in room['exits'].items():
                print(f"  {direction} -> {target}")
        else:
            print("Exits: None")
            
        if room.get('flags'):
            print(f"Flags: {', '.join(room['flags'])}")
        else:
            print("Flags: None")
            
        if room.get('items'):
            print(f"Items: {', '.join(room['items'])}")
        else:
            print("Items: None")
            
        if room.get('npcs'):
            print(f"NPCs: {', '.join(room['npcs'])}")
        else:
            print("NPCs: None")
            
    def validate_rooms(self):
        """Validate room connections and report issues"""
        print("\n=== Room Validation ===")
        issues = []
        
        for room_id, room in self.rooms.items():
            # Check for invalid exits
            for direction, target in room.get('exits', {}).items():
                if target not in self.rooms:
                    issues.append(f"Room '{room_id}' has exit '{direction}' to non-existent room '{target}'")
                    
        if issues:
            print("Validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("All room connections are valid!")
            
    def interactive_mode(self):
        """Run the editor in interactive mode"""
        print("=== Room Editor Interactive Mode ===")
        print("Available commands:")
        print("  list - List all rooms")
        print("  show <room_id> - Show room details")
        print("  create <room_id> <name> - Create new room")
        print("  edit <room_id> <field> <value> - Edit room")
        print("  delete <room_id> - Delete room")
        print("  validate - Validate room connections")
        print("  save - Save changes")
        print("  quit - Exit editor")
        print("\nEdit fields: name, description, add_exit <dir> <target>, remove_exit <dir>")
        print("              add_flag <flag>, remove_flag <flag>")
        print("              add_item <item>, remove_item <item>")
        print("              add_npc <npc>, remove_npc <npc>")
        print()
        
        while True:
            try:
                command = input("room_editor> ").strip()
                if not command:
                    continue
                    
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                if cmd == "list":
                    self.list_rooms()
                elif cmd == "show":
                    if args:
                        self.show_room(args[0])
                    else:
                        print("Usage: show <room_id>")
                elif cmd == "create":
                    if len(args) >= 2:
                        self.create_room(args[0], " ".join(args[1:]))
                    else:
                        print("Usage: create <room_id> <name>")
                elif cmd == "edit":
                    if len(args) >= 3:
                        if args[1] in ["add_exit", "remove_exit", "add_flag", "remove_flag", "add_item", "remove_item", "add_npc", "remove_npc"]:
                            value = " ".join(args[2:])
                        else:
                            value = " ".join(args[2:])
                        self.edit_room(args[0], args[1], value)
                    else:
                        print("Usage: edit <room_id> <field> <value>")
                elif cmd == "delete":
                    if args:
                        self.delete_room(args[0])
                    else:
                        print("Usage: delete <room_id>")
                elif cmd == "validate":
                    self.validate_rooms()
                elif cmd == "save":
                    self.save_rooms()
                elif cmd in ["quit", "exit"]:
                    break
                else:
                    print("Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit.")
            except Exception as e:
                print(f"Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 room_editor.py <command> [args...]")
        print("\nCommands:")
        print("  list - List all rooms")
        print("  show <room_id> - Show room details")
        print("  create <room_id> <name> - Create new room")
        print("  edit <room_id> <field> <value> - Edit room")
        print("  delete <room_id> - Delete room")
        print("  validate - Validate room connections")
        print("  interactive - Enter interactive mode")
        print("\nEdit fields: name, description, add_exit <dir> <target>, remove_exit <dir>")
        print("              add_flag <flag>, remove_flag <flag>")
        print("              add_item <item>, remove_item <item>")
        print("              add_npc <npc>, remove_npc <npc>")
        return
        
    editor = RoomEditor()
    command = sys.argv[1].lower()
    
    if command == "list":
        editor.list_rooms()
    elif command == "show":
        if len(sys.argv) >= 3:
            editor.show_room(sys.argv[2])
        else:
            print("Usage: python3 room_editor.py show <room_id>")
    elif command == "create":
        if len(sys.argv) >= 4:
            editor.create_room(sys.argv[2], " ".join(sys.argv[3:]))
            editor.save_rooms()
        else:
            print("Usage: python3 room_editor.py create <room_id> <name>")
    elif command == "edit":
        if len(sys.argv) >= 5:
            if sys.argv[3] in ["add_exit", "remove_exit", "add_flag", "remove_flag", "add_item", "remove_item", "add_npc", "remove_npc"]:
                value = " ".join(sys.argv[4:])
            else:
                value = " ".join(sys.argv[4:])
            if editor.edit_room(sys.argv[2], sys.argv[3], value):
                editor.save_rooms()
        else:
            print("Usage: python3 room_editor.py edit <room_id> <field> <value>")
    elif command == "delete":
        if len(sys.argv) >= 3:
            if editor.delete_room(sys.argv[2]):
                editor.save_rooms()
        else:
            print("Usage: python3 room_editor.py delete <room_id>")
    elif command == "validate":
        editor.validate_rooms()
    elif command == "interactive":
        editor.interactive_mode()
        editor.save_rooms()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()