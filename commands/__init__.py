"""Command handlers for the MUD server.

This package contains all command handlers organized by category:
- movement: look, move, go
- inventory: inventory, get, drop, use, equip, unequip
- combat: attack, join, disengage, use_maneuver
- social: say, who, talk
- shop: buy, sell, repair, list, shop
- info: stats, skills, maneuvers, quests, time
- admin: Admin-only commands
"""

from .movement import look_command, move_command
from .inventory import inventory_command, get_command, drop_command, use_command, equip_command, unequip_command
from .combat import attack_command, join_combat_command, disengage_command, use_maneuver_command
from .social import say_command, who_command, talk_command
from .shop import buy_command, sell_command, repair_command, shop_list_command
from .info import stats_command, skills_command, maneuvers_command, quests_command, quest_command, time_command, set_time_command, help_command, inspect_command
from .admin import create_room_command, edit_room_command, delete_room_command, list_rooms_command, goto_command, create_weapon_command, list_weapons_command

__all__ = [
    # Movement
    'look_command', 'move_command',
    # Inventory
    'inventory_command', 'get_command', 'drop_command', 'use_command', 'equip_command', 'unequip_command',
    # Combat
    'attack_command', 'join_combat_command', 'disengage_command', 'use_maneuver_command',
    # Social
    'say_command', 'who_command', 'talk_command',
    # Shop
    'buy_command', 'sell_command', 'repair_command', 'shop_list_command',
    # Info
    'stats_command', 'skills_command', 'maneuvers_command', 'quests_command', 'quest_command', 
    'time_command', 'set_time_command', 'help_command', 'inspect_command',
    # Admin
    'create_room_command', 'edit_room_command', 'delete_room_command', 'list_rooms_command', 
    'goto_command', 'create_weapon_command', 'list_weapons_command',
]
