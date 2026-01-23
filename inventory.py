"""Inventory and item management module."""

import json
import os

class Item:
    def __init__(self, item_id, name, description, item_type="item"):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.item_type = item_type  # weapon, armor, consumable, item
        self.value = 0
        self.stats = {}
        
    def to_dict(self):
        return {
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type,
            "value": self.value,
            "stats": self.stats
        }
    
    def from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Inventory:
    """Handles inventory and item management."""
    
    def __init__(self, formatter, data_dir="mud_data"):
        self.formatter = formatter
        self.data_dir = data_dir
        self.items = {}
    
    def load_items_from_json(self):
        """Load items from items.json"""
        try:
            if os.path.exists(f"{self.data_dir}/items.json"):
                with open(f"{self.data_dir}/items.json", 'r') as f:
                    items_data = json.load(f)
                    for item_data in items_data:
                        item = Item(item_data["item_id"], item_data["name"], item_data["description"], item_data.get("item_type", "item"))
                        item.from_dict(item_data)
                        self.items[item.item_id] = item
        except Exception as e:
            print(f"Error loading items from JSON: {e}")
    
    def get_item(self, item_id):
        """Get item by ID"""
        return self.items.get(item_id)
    
    def inventory_command(self, player):
        """Display player inventory"""
        if not player.inventory:
            self.formatter.send_to_player(player, "You are not carrying anything.")
            return
            
        output = self.formatter.format_header("You are carrying:") + "\n"
        for item_id in player.inventory:
            item = self.items.get(item_id)
            if item:
                item_name = self.formatter.format_item(item.name)
                output += f"- {item_name}: {item.description}\n"
                
        self.formatter.send_to_player(player, output.strip())
    
    def get_command(self, player, args, get_room_func, broadcast_func):
        """Handle get/take command"""
        if not args:
            self.formatter.send_to_player(player, "Get what?")
            return
            
        item_name = " ".join(args).lower()
        room = get_room_func(player.room_id)
        
        if not room:
            self.formatter.send_to_player(player, "You are in an unknown location.")
            return
        
        for item_id in room.items[:]:
            item = self.items.get(item_id)
            if item and item_name in item.name.lower():
                room.items.remove(item_id)
                player.inventory.append(item_id)
                item_display = self.formatter.format_item(item.name)
                self.formatter.send_to_player(player, self.formatter.format_success(f"You pick up {item_display}."))
                broadcast_func(player.room_id, f"{player.name} picks up {item_display}.", player.name)
                return
                
        self.formatter.send_to_player(player, "You don't see that here.")
    
    def drop_command(self, player, args, get_room_func, broadcast_func):
        """Handle drop command"""
        if not args:
            self.formatter.send_to_player(player, "Drop what?")
            return
            
        item_name = " ".join(args).lower()
        room = get_room_func(player.room_id)
        
        if not room:
            self.formatter.send_to_player(player, "You are in an unknown location.")
            return
        
        for item_id in player.inventory[:]:
            item = self.items.get(item_id)
            if item and item_name in item.name.lower():
                player.inventory.remove(item_id)
                room.items.append(item_id)
                item_display = self.formatter.format_item(item.name)
                self.formatter.send_to_player(player, self.formatter.format_success(f"You drop {item_display}."))
                broadcast_func(player.room_id, f"{player.name} drops {item_display}.", player.name)
                return
                
        self.formatter.send_to_player(player, "You don't have that.")
    
    def use_command(self, player, args):
        """Handle use command"""
        if not args:
            self.formatter.send_to_player(player, "Use what?")
            return
            
        item_name = " ".join(args).lower()
        
        for item_id in player.inventory:
            item = self.items.get(item_id)
            if item and item_name in item.name.lower():
                if item.item_type == "consumable":
                    # Handle consumable items (potions, etc.)
                    if "heal" in item.stats:
                        heal_amount = item.stats["heal"]
                        player.health = min(player.max_health, player.health + heal_amount)
                        self.formatter.send_to_player(player, self.formatter.format_success(f"You use {item.name} and restore {heal_amount} health."))
                        player.inventory.remove(item_id)
                        return
                    elif "mana" in item.stats:
                        mana_amount = item.stats["mana"]
                        player.mana = min(player.max_mana, player.mana + mana_amount)
                        self.formatter.send_to_player(player, self.formatter.format_success(f"You use {item.name} and restore {mana_amount} mana."))
                        player.inventory.remove(item_id)
                        return
                    else:
                        self.formatter.send_to_player(player, f"You can't use {item.name} right now.")
                        return
                else:
                    self.formatter.send_to_player(player, f"You can't use {item.name}.")
                    return
                    
        self.formatter.send_to_player(player, "You don't have that.")
