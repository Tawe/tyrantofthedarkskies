"""Admin-only commands for world management."""

import os
import json

def create_room_command(game, player, args):
    """Create a new room (admin command)."""
    if not args:
        game.send_to_player(player, "Usage: create_room <room_id> <room_name>")
        return
        
    if len(args) < 2:
        game.send_to_player(player, "Usage: create_room <room_id> <room_name>")
        return
        
    room_id = args[0].lower()
    room_name = " ".join(args[1:])
    
    # Validate room_id
    if not room_id.replace('_', '').isalnum():
        game.send_to_player(player, "Room ID must contain only letters, numbers, and underscores.")
        return
        
    if room_id in game.rooms:
        game.send_to_player(player, f"Room '{room_id}' already exists.")
        return
    
    # Create room - import Room class
    from mud_server import Room
    room = Room(room_id, room_name, "A newly created room. Description pending.")
    game.rooms[room_id] = room
    game.save_rooms_to_json()
    game.send_to_player(player, f"Room '{room_id}' created successfully!")


def edit_room_command(game, player, args):
    """Edit room properties (admin command)."""
    if not args:
        game.send_to_player(player, "Usage: edit_room <room_id> <field> <value>")
        game.send_to_player(player, "Fields: name, description, add_exit, remove_exit, add_flag, remove_flag")
        return
        
    if len(args) < 3 and args[1] not in ["add_exit", "remove_exit", "add_flag", "remove_flag"]:
        game.send_to_player(player, "Usage: edit_room <room_id> <field> <value>")
        return
        
    room_id = args[0].lower()
    field = args[1].lower()
    
    if room_id not in game.rooms:
        game.send_to_player(player, f"Room '{room_id}' does not exist.")
        return
        
    room = game.rooms[room_id]
    
    if field == "name":
        room.name = " ".join(args[2:])
        game.send_to_player(player, f"Room name updated to: {room.name}")
    elif field == "description":
        room.description = " ".join(args[2:])
        game.send_to_player(player, f"Room description updated.")
    elif field == "add_exit" and len(args) >= 4:
        direction = args[2].lower()
        target_room = args[3].lower()
        room.exits[direction] = target_room
        game.send_to_player(player, f"Exit '{direction}' to '{target_room}' added.")
    elif field == "remove_exit":
        direction = args[2].lower()
        if direction in room.exits:
            del room.exits[direction]
            game.send_to_player(player, f"Exit '{direction}' removed.")
        else:
            game.send_to_player(player, f"Exit '{direction}' does not exist.")
    elif field == "add_flag" and len(args) >= 3:
        flag = args[2].lower()
        if flag not in room.flags:
            room.flags.append(flag)
            game.send_to_player(player, f"Flag '{flag}' added.")
        else:
            game.send_to_player(player, f"Flag '{flag}' already exists.")
    elif field == "remove_flag" and len(args) >= 3:
        flag = args[2].lower()
        if flag in room.flags:
            room.flags.remove(flag)
            game.send_to_player(player, f"Flag '{flag}' removed.")
        else:
            game.send_to_player(player, f"Flag '{flag}' does not exist.")
    else:
        game.send_to_player(player, "Invalid field or missing arguments.")
        return
        
    game.save_rooms_to_json()


def delete_room_command(game, player, args):
    """Delete a room (admin command)."""
    if not args:
        game.send_to_player(player, "Usage: delete_room <room_id>")
        return
        
    room_id = args[0].lower()
    
    if room_id not in game.rooms:
        game.send_to_player(player, f"Room '{room_id}' does not exist.")
        return
        
    if room_id == "black_anchor_common":
        game.send_to_player(player, "Cannot delete the starting room (The Black Anchor - Common Room).")
        return
        
    del game.rooms[room_id]
    
    for room in game.rooms.values():
        exits_to_remove = [dir for dir, target in room.exits.items() if target == room_id]
        for exit_dir in exits_to_remove:
            del room.exits[exit_dir]
            
    game.save_rooms_to_json()
    game.send_to_player(player, f"Room '{room_id}' deleted and all exits to it removed.")


def list_rooms_command(game, player, args):
    """List all rooms (admin command)."""
    room_list = "=== Room List ===\n"
    for room_id, room in game.rooms.items():
        room_list += f"{room_id}: {room.name}\n"
        if room.exits:
            exits = ", ".join([f"{dir}->{target}" for dir, target in room.exits.items()])
            room_list += f"  Exits: {exits}\n"
        if room.flags:
            room_list += f"  Flags: {', '.join(room.flags)}\n"
        room_list += "\n"
        
    game.send_to_player(player, room_list.strip())


def goto_command(game, player, args):
    """Teleport to a room (admin command)."""
    if not args:
        game.send_to_player(player, "Usage: goto <room_id>")
        return
        
    room_id = args[0].lower()
    
    if room_id not in game.rooms:
        game.send_to_player(player, f"Room '{room_id}' does not exist.")
        return
        
    old_room_id = player.room_id
    
    if old_room_id in game.rooms:
        game.rooms[old_room_id].players.discard(player.name)
        
    player.room_id = room_id
    game.rooms[room_id].players.add(player.name)
    
    # Import look_command to avoid circular dependency
    from .movement import look_command
    look_command(game, player, [])
    game.broadcast_to_room(room_id, f"{player.name} appears suddenly.", player.name)


def create_weapon_command(game, player, args):
    """Create a weapon item from a template (admin command)"""
    if len(args) < 1:
        game.send_to_player(player, "Usage: create_weapon <template_id> [modifier_id] [item_id]")
        return
    
    template_id = args[0].lower()
    modifier_id = args[1].lower() if len(args) > 1 else None
    item_id = args[2].lower() if len(args) > 2 else None
    
    # Create weapon item
    weapon_item = game.create_weapon_item(template_id, modifier_id, item_id)
    
    if not weapon_item:
        game.send_to_player(player, f"Weapon template '{template_id}' not found.")
        return
    
    # Add to player's inventory
    player.inventory.append(weapon_item.item_id)
    game.items[weapon_item.item_id] = weapon_item
    
    # Save items - check if method exists
    if hasattr(game, 'save_items_to_json'):
        game.save_items_to_json()
    else:
        # Fallback: save world data
        game.save_world_data()
    
    game.send_to_player(player, f"Created {weapon_item.name} and added to your inventory!")
    if game.logger:
        game.logger.log_admin_action(player.name, "CREATE_WEAPON", f"Template: {template_id}, Modifier: {modifier_id}")


def list_weapons_command(game, player, args):
    """List available weapon templates (admin command)"""
    if not game.weapons:
        game.send_to_player(player, "No weapon templates loaded.")
        return
    
    output = f"\n{game.format_header('Available Weapon Templates')}\n"
    for weapon_id, weapon in game.weapons.items():
        output += f"\n{game.format_header(weapon['name'])} ({weapon_id})\n"
        output += f"  Category: {weapon['category']} | Class: {weapon['class']}\n"
        output += f"  Damage: {weapon['damage_min']}-{weapon['damage_max']} ({weapon['damage_type']})\n"
        output += f"  Hands: {weapon['hands']} | Range: {weapon['range']}\n"
        output += f"  Crit: {int(weapon['crit_chance'] * 100)}% | Speed: {weapon['speed_cost']}\n"
        output += f"  Durability: {weapon['durability']}\n"
    
    game.send_to_player(player, output)
