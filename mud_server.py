import threading
import json
import os
import time
import random
import re
import http
import concurrent.futures
from datetime import datetime
from collections import defaultdict
import logging
import asyncio
import queue
import traceback

# Import Player from models package
try:
    from models.player import Player
except ImportError:
    # If import fails, Player class must be defined below
    Player = None

# WebSocket support
try:
    import websockets
    # WebSocketServerProtocol is deprecated but may still be needed for type hints
    # The actual websocket object from websockets.serve() works without explicit typing
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("Warning: websockets library not available. WebSocket support disabled.")

# Firebase integration (required for auth)
FIREBASE_IMPORT_ERROR = None
try:
    # Try new package structure first
    from firebase.data_layer import FirebaseDataLayer
    from firebase.auth import FirebaseAuth
    USE_FIREBASE = True
except ImportError:
    # Fallback to root imports for backward compatibility
    try:
        from firebase_data_layer import FirebaseDataLayer
        from firebase_auth import FirebaseAuth
        USE_FIREBASE = True
    except Exception as e:
        USE_FIREBASE = False
        FIREBASE_IMPORT_ERROR = e
        print(f"Warning: Firebase modules not importable: {e}")

# Command handlers
try:
    from commands import (
        look_command, move_command,
        inventory_command, get_command, drop_command, use_command, equip_command, unequip_command,
        attack_command, join_combat_command, disengage_command, use_maneuver_command,
        say_command, who_command, talk_command,
        buy_command, sell_command, repair_command, shop_list_command,
        stats_command, skills_command, maneuvers_command, quests_command, quest_command,
        time_command, set_time_command, help_command, inspect_command,
        create_room_command, edit_room_command, delete_room_command, list_rooms_command,
        goto_command, create_weapon_command, list_weapons_command
    )
    COMMANDS_AVAILABLE = True
except ImportError as e:
    COMMANDS_AVAILABLE = False
    print(f"Warning: Command handlers not available: {e}")
    # Fallback: commands will use methods defined in MudGame class

class WebSocketConnection:
    """Wrapper to make WebSocket connections work like socket connections"""
    def __init__(self, websocket, address, send_queue, loop=None):
        self.websocket = websocket
        self.address = address
        self.send_queue = send_queue  # Queue for messages to send
        self.loop = loop  # Event loop for thread-safe queueing
        self._closed = False
        self._timeout = None
    
    def send(self, data):
        """Queue data to send through WebSocket"""
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='replace')
        if not self._closed and self.send_queue is not None:
            try:
                # asyncio.Queue isn't thread-safe; commands may run in a worker thread.
                # Use the loop to enqueue safely when available.
                if self.loop is not None:
                    self.loop.call_soon_threadsafe(self.send_queue.put_nowait, data)
                else:
                    self.send_queue.put_nowait(data)
            except Exception as e:
                print(f"Error queuing WebSocket message: {e}")
                self._closed = True
    
    def close(self):
        """Close WebSocket connection"""
        self._closed = True
    
    @property
    def closed(self):
        """Check if WebSocket connection is closed."""
        return self._closed

# Player class is now imported from models.player
# If import failed above, Player will be None and we need to define it here
if Player is None:
    raise ImportError("Failed to import Player from models.player. Please ensure models/player.py exists.")

class Room:
    def __init__(self, room_id, name, description):
        self.room_id = room_id
        self.name = name
        self.description = description
        self.exits = {}
        self.items = []
        self.npcs = []
        self.players = set()
        self.flags = []
        self.combat_tags = []  # open, cramped, slick, obscured, elevated
        
    def to_dict(self):
        return {
            "room_id": self.room_id,
            "name": self.name,
            "description": self.description,
            "exits": self.exits,
            "items": self.items,
            "npcs": self.npcs,
            "flags": self.flags,
            "combat_tags": self.combat_tags
        }
    
    def from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class NPC:
    def __init__(self, npc_id, name, description):
        self.npc_id = npc_id
        self.name = name
        self.description = description
        
        # Core stats (PC parity)
        self.health = 50
        self.max_health = 50
        self.mana = 25
        self.max_mana = 25
        self.stamina = 50
        self.max_stamina = 50
        
        # Attributes (PC parity)
        self.attributes = {
            "physical": 10,
            "mental": 10,
            "spiritual": 10,
            "social": 10
        }
        
        # Skills (PC parity)
        self.skills = {}
        
        # Combat system
        self.combat_role = None  # Brute, Minion, Boss, Artillery, Healer, Controller
        self.tier = "Low"  # Low, Mid, High, Epic
        self.level = 1  # Fixed level based on tier
        self.exp_value = 0  # EXP granted on defeat
        
        # Maneuvers
        self.known_maneuvers = []
        self.active_maneuvers = []
        
        # Equipment
        self.equipped = {}
        
        # Combat state
        self.is_hostile = False
        self.combat_state = "Observing"  # Observing, Engaged, Supporting, Disengaging, Exposed, Pinned, Staggered
        self.combat_target = None
        self.initiative = 0
        
        # Loot
        self.loot_table = []
        
        # Outlooks & relationships
        self.outlooks = {}  # {player_name: outlook_value}
        self.faction_outlooks = {}  # {faction: outlook_value}
        
        # Legacy fields
        self.dialogue = []
        self.inventory = []
    
    def get_tier(self):
        """Get tier based on level"""
        if self.level <= 5:
            return "Low"
        elif self.level <= 10:
            return "Mid"
        elif self.level <= 15:
            return "High"
        else:
            return "Epic"
    
    def get_attribute_bonus(self, attribute):
        """Calculate attribute bonus (same as Player)"""
        if attribute not in self.attributes:
            return 0
        return (self.attributes[attribute] - 5) // 2
    
    def roll_skill_check(self, skill_name):
        """Roll skill check (same as Player)"""
        if skill_name not in self.skills:
            base_skill = 1
        else:
            base_skill = self.skills[skill_name]
        
        # Get effective skill (simplified - would need full skill system)
        effective_skill = base_skill
        roll = random.randint(1, 100)
        
        if roll <= effective_skill // 10:  # Critical (1/10th of skill)
            return {"result": "critical", "roll": roll, "skill": effective_skill}
        elif roll <= effective_skill:
            return {"result": "success", "roll": roll, "skill": effective_skill}
        else:
            return {"result": "failure", "roll": roll, "skill": effective_skill}
        
    def to_dict(self):
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "description": self.description,
            "health": self.health,
            "max_health": self.max_health,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "stamina": self.stamina,
            "max_stamina": self.max_stamina,
            "attributes": self.attributes,
            "skills": self.skills,
            "combat_role": self.combat_role,
            "tier": self.tier,
            "level": self.level,
            "exp_value": self.exp_value,
            "known_maneuvers": self.known_maneuvers,
            "active_maneuvers": self.active_maneuvers,
            "equipped": self.equipped,
            "is_hostile": self.is_hostile,
            "combat_state": self.combat_state,
            "loot_table": self.loot_table,
            "outlooks": self.outlooks,
            "faction_outlooks": self.faction_outlooks,
            "dialogue": self.dialogue,
            "inventory": self.inventory
        }
        
        # Add merchant fields if present
        if hasattr(self, 'shop_inventory'):
            result["shop_inventory"] = self.shop_inventory
        if hasattr(self, 'keywords'):
            result["keywords"] = self.keywords
        if hasattr(self, 'is_merchant'):
            result["is_merchant"] = self.is_merchant
        if hasattr(self, 'faction'):
            result["faction"] = self.faction
    
    def from_dict(self, data):
        for key, value in data.items():
            # Always set the attribute, even if it doesn't exist yet (for new fields like shop_inventory, keywords, etc.)
            setattr(self, key, value)
        
        # Ensure tier matches level
        self.tier = self.get_tier()

class Item:
    def __init__(self, item_id, name, description, item_type="item"):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.item_type = item_type  # weapon, armor, consumable, item
        self.value = 0
        self.stats = {}
        
        # Weapon-specific properties
        self.weapon_template_id = None  # Reference to weapons.json template
        self.weapon_modifier_id = None  # Reference to weapon_modifiers.json
        self.current_durability = None  # Current durability (None = full)
        
        # Weapon stats (from template + modifier)
        self.category = None  # Melee, Ranged
        self.weapon_class = None  # Sword, Dagger, Bow, etc.
        self.hands = 1  # 1 or 2
        self.range = 0  # 0 for melee, >0 for ranged
        self.damage_min = 0
        self.damage_max = 0
        self.damage_type = None  # slashing, piercing, bludgeoning
        self.crit_chance = 0.0
        self.speed_cost = 1.0
        self.max_durability = 50
        
        # Armor-specific properties
        self.armor_type = None  # light, medium, heavy
        self.damage_reduction = {}  # {damage_type: DR_amount} e.g., {"slashing": 2, "piercing": 1, "bludgeoning": 3}
        self.armor_slots = []  # body, head, arms, legs, etc.
        
    def is_armor(self):
        """Check if this item is armor"""
        return self.item_type == "armor" or self.armor_type is not None
    
    def get_effective_damage(self):
        """Get effective damage range (min, max)"""
        return (self.damage_min, self.damage_max)
    
    def get_effective_crit_chance(self):
        """Get effective critical hit chance"""
        return self.crit_chance
    
    def get_effective_speed_cost(self):
        """Get effective speed cost"""
        return self.speed_cost
    
    def get_current_durability(self):
        """Get current durability (defaults to max if not set)"""
        if self.current_durability is None:
            return self.max_durability
        return self.current_durability
    
    def reduce_durability(self, amount=1):
        """Reduce durability, return True if broken"""
        if self.current_durability is None:
            self.current_durability = self.max_durability
        self.current_durability = max(0, self.current_durability - amount)
        return self.current_durability <= 0
    
    def is_weapon(self):
        """Check if this item is a weapon"""
        return self.item_type == "weapon" or self.category in ["Melee", "Ranged"]
        
    def to_dict(self):
        result = {
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type,
            "value": self.value,
            "stats": self.stats
        }
        
        # Include weapon properties if it's a weapon
        if self.is_weapon():
            result["weapon_template_id"] = self.weapon_template_id
            result["weapon_modifier_id"] = self.weapon_modifier_id
            result["current_durability"] = self.current_durability
            result["category"] = self.category
            result["weapon_class"] = self.weapon_class
            result["hands"] = self.hands
            result["range"] = self.range
            result["damage_min"] = self.damage_min
            result["damage_max"] = self.damage_max
            result["damage_type"] = self.damage_type
            result["crit_chance"] = self.crit_chance
            result["speed_cost"] = self.speed_cost
            result["max_durability"] = self.max_durability
        
        # Include armor properties if it's armor
        if self.is_armor():
            result["armor_type"] = self.armor_type
            result["damage_reduction"] = self.damage_reduction
            result["armor_slots"] = self.armor_slots
        
        return result
    
    def from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

class MudGame:
    def __init__(self):
        self.players = {}
        self.rooms = {}
        self.npcs = {}
        self.items = {}
        self.maneuvers = {}
        self.planets = {}
        self.races = {}
        self.starsigns = {}
        self.weapons = {}  # Weapon templates
        self.weapon_modifiers = {}  # Weapon modifiers
        self.player_lock = threading.Lock()
        self.world_lock = threading.Lock()
        self.player_login_time = {}  # player_name -> time when added (to detect duplicate vs reconnect)
        self.websocket_port = int(os.getenv('MUD_WEBSOCKET_PORT', 5557))  # WebSocket port
        # Bind address for the WebSocket server.
        # - On Fly: bind to 0.0.0.0 so the proxy can reach us.
        # - Locally: bind to :: (IPv6 any) so both localhost/::1 and 127.0.0.1 work.
        if os.getenv('MUD_BIND_ADDRESS'):
            self.bind_address = os.getenv('MUD_BIND_ADDRESS')
        elif os.getenv('FLY_APP_NAME'):
            self.bind_address = '0.0.0.0'
        else:
            self.bind_address = '::'
        
        # Rate limiting
        self.rate_limiter = defaultdict(list)
        self.max_commands_per_second = 10
        
        # Connection limits
        self.max_connections = 50
        self.active_connections = 0
        self.connection_lock = threading.Lock()

        # WebSocket command execution:
        # Keep game logic off the asyncio event loop to avoid "works once then reload can't connect"
        # symptoms caused by blocking synchronous work (Firebase, file IO, etc).
        # Use a single worker to preserve ordering and reduce race conditions.
        self.ws_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        # Logging (initialize before admin config to allow logging)
        try:
            try:
                from utils.logger import SecurityLogger
            except ImportError:
                from logger import SecurityLogger
            self.logger = SecurityLogger()
        except ImportError:
            # Fallback if logger module not available
            self.logger = None
            print("Warning: SecurityLogger not available. Logging disabled.")
        
        # Initialize Firebase (required for authentication)
        if USE_FIREBASE:
            try:
                self.firebase = FirebaseDataLayer()
                self.firebase_auth = FirebaseAuth()
                self.use_firebase = True
                print("Firebase initialized successfully.")
            except Exception as e:
                print(f"ERROR: Firebase initialization failed: {e}")
                print("Firebase is required for authentication. Server cannot start without it.")
                raise
        else:
            print("ERROR: Firebase is required but not available.")
            if FIREBASE_IMPORT_ERROR is not None:
                print(f"Root cause: {FIREBASE_IMPORT_ERROR}")
            print("Fix: ensure your venv is active, then run: pip install -r requirements.txt")
            raise ImportError("Firebase is required for authentication") from FIREBASE_IMPORT_ERROR
        
        # Admin configuration (loaded from Firebase)
        self.admin_config = self.load_admin_config()
        
        # Connection timeout (seconds)
        self.connection_timeout = 300  # 5 minutes
        
        # Combat system
        try:
            from systems.combat_system import CombatManager
            self.combat_manager = CombatManager(
                self,
                self.get_room,
                self.broadcast_to_room,
                self.items  # Pass items dict for weapon lookups
            )
        except ImportError:
            # Fallback to root import for backward compatibility
            try:
                from combat_system import CombatManager
                self.combat_manager = CombatManager(
                    self,
                    self.get_room,
                    self.broadcast_to_room,
                    self.items
                )
            except ImportError:
                self.combat_manager = None
                print("Warning: CombatManager not available. Combat features disabled.")
        
        # Exploration tracking (for EXP rewards)
        self.explored_rooms = defaultdict(set)  # {player_name: set of room_ids}
        
        # Quest system
        try:
            from systems.quest_system import QuestManager
            self.quest_manager = QuestManager()
        except ImportError:
            # Fallback to root import for backward compatibility
            try:
                from quest_system import QuestManager
                self.quest_manager = QuestManager()
            except ImportError:
                self.quest_manager = None
                print("Warning: QuestManager not available. Quest features disabled.")
        
        # Time system
        try:
            from systems.time_system import WorldTime, NPCScheduler, StoreHours
            self.world_time = WorldTime()
            self.npc_scheduler = NPCScheduler(self.world_time)
            self.store_hours = StoreHours(self.world_time)
            # Load saved world time if available
            self.load_world_time()
        except ImportError:
            # Fallback to root import for backward compatibility
            try:
                from time_system import WorldTime, NPCScheduler, StoreHours
                self.world_time = WorldTime()
                self.npc_scheduler = NPCScheduler(self.world_time)
                self.store_hours = StoreHours(self.world_time)
                self.load_world_time()
            except ImportError:
                self.world_time = None
                self.npc_scheduler = None
                self.store_hours = None
                print("Warning: Time system not available. Time features disabled.")
        
        # ANSI color codes for terminal highlighting
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m',
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'orange': '\033[38;5;208m',
            'gray': '\033[90m',
            'purple': '\033[38;5;141m',
            'brown': '\033[38;5;130m'
        }
        
        self.load_world_data()
        self.load_maneuvers()
        self.load_planets()
        self.load_races()
        self.load_starsigns()
        self.load_weapons()
        self.load_weapon_modifiers()
        self.load_npc_schedules()
        self.load_store_hours()
        self.create_default_world()
        
    def format_brackets(self, text, color='cyan'):
        """Format text with colored brackets"""
        color_code = self.colors.get(color, self.colors['cyan'])  # Default to cyan if color not found
        return f"{color_code}[{self.colors['reset']}{text}{color_code}]{self.colors['reset']}"
        
    def format_item(self, text):
        """Format item names with highlighting"""
        return f"{self.colors['yellow']}{text}{self.colors['reset']}"
        
    def format_npc(self, text):
        """Format NPC names with highlighting"""
        return f"{self.colors['magenta']}{text}{self.colors['reset']}"
        
    def format_exit(self, direction):
        """Format exit directions with brackets"""
        return self.format_brackets(direction.capitalize(), 'green')
        
    def format_command(self, text):
        """Format commands in help text"""
        return self.format_brackets(text, 'blue')
    
    def format_header(self, text):
        """Format headers with bold"""
        return f"{self.colors['bold']}{text}{self.colors['reset']}"
        
    def show_starsign_selection(self, player):
        """Show available starsigns for selection"""
        self.send_to_player(player, f"""
{self.format_header('Choose Your Starsign:')}
Your starsign represents fate at birth. Star Signs are permanent, always active, and focused on fate, 
temperament, and narrative flavor. Each provides +2 to one attribute, -1 to another, and a Fated Mark.

""")

        for starsign_id, starsign in self.starsigns.items():
            if 'color' in starsign:
                starsign_display = f"{self.format_brackets(starsign_id.upper(), starsign['color'])}: {starsign['name']}"
            else:
                starsign_display = f"[{starsign_id.upper()}]: {starsign['name']}"
            self.send_to_player(player, starsign_display)
            self.send_to_player(player, f"  Theme: {starsign['theme']}")
            
            # Show lore/description
            if "description" in starsign:
                self.send_to_player(player, f"  {starsign['description']}")
            
            # Show attribute modifiers
            if "attribute_modifiers" in starsign:
                mods = starsign["attribute_modifiers"]
                mod_list = []
                for attr, value in mods.items():
                    if value > 0:
                        mod_list.append(f"+{value} {attr.capitalize()}")
                    elif value < 0:
                        mod_list.append(f"{value} {attr.capitalize()}")
                if mod_list:
                    self.send_to_player(player, f"  Attributes: {', '.join(mod_list)}")
            
            # Show fated mark
            if "fated_mark" in starsign:
                fated_mark = starsign["fated_mark"]
                if "name" in fated_mark:
                    self.send_to_player(player, f"  {self.format_header('Fated Mark:')} {fated_mark['name']}")
                if "description" in fated_mark:
                    self.send_to_player(player, f"    {fated_mark['description']}")
            
            self.send_to_player(player, "")  # Blank line between starsigns
        
        self.send_to_player(player, f"\nType {self.format_command('starsign <name>')} to choose your starsign.")
        player.creation_state = "choosing_starsign"
    
    def show_planet_selection(self, player):
        """Show available planets for selection"""
        self.send_to_player(player, f"""
{self.format_header('Choose Your Planet:')}
Your planet represents cosmic guardianship and destiny. Planets are permanent and shape your character's 
style of play from level 1 onward. Each planet grants one starting maneuver, provides a passive effect 
that scales by tier, and offers attribute bonuses and starting skills.

""")

        for planet_id, planet in self.planets.items():
            if 'color' in planet:
                planet_display = f"{self.format_brackets(planet_id.upper(), planet['color'])}: {planet['name']}"
            else:
                planet_display = f"[{planet_id.upper()}]: {planet['name']}"
            self.send_to_player(player, planet_display)
            self.send_to_player(player, f"  Theme: {planet['theme']}")
            
            # Show cosmic role (lore)
            if "cosmic_role" in planet:
                self.send_to_player(player, f"  Cosmic Role: {planet['cosmic_role']}")
            
            # Show description (lore)
            if "description" in planet:
                self.send_to_player(player, f"  {planet['description']}")
            
            # Show attribute bonuses
            if "attribute_bonuses" in planet:
                bonuses = planet["attribute_bonuses"]
                bonus_list = []
                for attr, value in bonuses.items():
                    if value > 0:
                        bonus_list.append(f"+{value} {attr.capitalize()}")
                if bonus_list:
                    self.send_to_player(player, f"  Attribute Bonuses: {', '.join(bonus_list)}")
            
            # Show passive effect with description
            if "passive_effect" in planet:
                self.send_to_player(player, f"  {self.format_header('Passive Effect:')} {planet['passive_effect']}")
                if "passive_description" in planet:
                    self.send_to_player(player, f"    {planet['passive_description']}")
            
            # Show gift maneuver
            if "gift_maneuver" in planet:
                self.send_to_player(player, f"  Gift Maneuver: {planet['gift_maneuver']}")
            
            self.send_to_player(player, "")  # Blank line between planets
        
        self.send_to_player(player, f"\nType {self.format_command('planet <name>')} to choose your planet.")
        player.creation_state = "choosing_planet"
        
    def format_success(self, text):
        """Format success messages"""
        return f"{self.colors['green']}{text}{self.colors['reset']}"
        
    def format_error(self, text):
        """Format error messages"""
        return f"{self.colors['red']}{text}{self.colors['reset']}"
        
    def send_to_player(self, player, message):
        """Send formatted message to player"""
        try:
            # Check if it's a WebSocket connection
            if isinstance(player.connection, WebSocketConnection):
                # WebSocket - strip ANSI codes and colorize brackets with HTML
                message_clean = self.strip_ansi(message)
                message_clean = self.colorize_brackets(message_clean, is_websocket=True)
                player.connection.send(message_clean + '\n')
            else:
                # Regular socket connection - colorize brackets with ANSI and encode to bytes
                message = self.colorize_brackets(message, is_websocket=False)
                player.connection.send(message.encode() + b'\n\r')
        except:
            player.is_logged_in = False
            
    def colorize_brackets(self, text, is_websocket=False):
        """Automatically color code text between square brackets (only if not already colored)"""
        if is_websocket:
            # For WebSocket: convert to HTML spans
            # Skip if already wrapped in HTML span
            def replace_brackets(match):
                content = match.group(1)
                # Check if already has HTML tags (from previous formatting)
                if '<span' in content or '</span>' in content:
                    return match.group(0)  # Don't double-wrap
                return f'<span style="color: #00ffff;">[{content}]</span>'
            return re.sub(r'\[([^\]]+)\]', replace_brackets, text)
        else:
            # For telnet: use ANSI cyan color
            # Skip if already has ANSI color codes (from format_brackets, etc.)
            def replace_brackets(match):
                content = match.group(1)
                # Check if content already has ANSI codes (likely from format_brackets)
                if '\x1b[' in content:
                    return match.group(0)  # Don't double-colorize
                return f"{self.colors['cyan']}[{self.colors['reset']}{content}{self.colors['cyan']}]{self.colors['reset']}"
            return re.sub(r'\[([^\]]+)\]', replace_brackets, text)
    
    def strip_ansi(self, text):
        """Remove ANSI codes for length calculations and WebSocket clients"""
        # Remove all ANSI escape sequences
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        text = ansi_escape.sub('', text)
        # Also remove other common ANSI codes
        text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        return text
        
    # setup_data_directory removed - using Firebase only
            
    def load_world_data(self):
        self.load_rooms_from_json()
        self.load_npcs_from_json()
        self.load_items_from_json()
        
    def load_rooms_from_json(self):
        """Load rooms from Firebase, contributions, or JSON files."""
        try:
            # Try Firebase first
            if self.use_firebase and self.firebase:
                try:
                    rooms_data = self.firebase.load_rooms()
                    if rooms_data:
                        for room_id, room_data in rooms_data.items():
                            room = Room(room_data["room_id"], room_data["name"], room_data["description"])
                            exits_data = room_data.get("exits", {})
                            room.exits = {}
                            for direction, exit_value in exits_data.items():
                                room.exits[direction] = exit_value
                            room.items = room_data.get("items", [])
                            room.npcs = room_data.get("npcs", [])
                            room.flags = room_data.get("flags", [])
                            room.combat_tags = room_data.get("combat_tags", [])
                            self.rooms[room.room_id] = room
                        print(f"Loaded {len(self.rooms)} rooms from Firebase")
                        return
                except Exception as e:
                    print(f"Error loading rooms from Firebase: {e}, falling back to files")
            
            # Try loading from individual contribution files
            contributions_dir = "contributions/rooms"
            if os.path.exists(contributions_dir):
                count = 0
                for filename in os.listdir(contributions_dir):
                    if filename.endswith('.json') and filename != 'README.md':
                        filepath = os.path.join(contributions_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                room_data = json.load(f)
                                room = Room(room_data["room_id"], room_data["name"], room_data["description"])
                                # Load exits - support both simple string format and dict format with doors
                                exits_data = room_data.get("exits", {})
                                room.exits = {}
                                for direction, exit_value in exits_data.items():
                                    # If it's already a dict (with door/obstacle info), use it as-is
                                    # If it's a string (simple target), keep it as-is for backward compatibility
                                    room.exits[direction] = exit_value
                                room.items = room_data.get("items", [])
                                room.npcs = room_data.get("npcs", [])
                                room.flags = room_data.get("flags", [])
                                room.combat_tags = room_data.get("combat_tags", [])
                                self.rooms[room.room_id] = room
                                count += 1
                        except Exception as e:
                            print(f"Error loading room file {filename}: {e}")
                
                if count > 0:
                    print(f"Loaded {count} rooms from contributions/rooms/")
                    return
            
            # No rooms found from Firebase or contributions
            print("No rooms found, using default rooms")
        except Exception as e:
            print(f"Error loading rooms from JSON: {e}")
            
    def load_npcs_from_json(self):
        """Load NPCs from Firebase, contributions, or JSON files."""
        try:
            # Try Firebase first
            if self.use_firebase and self.firebase:
                try:
                    npcs_data = self.firebase.load_npcs()
                    if npcs_data:
                        for npc_id, npc_data in npcs_data.items():
                            npc = NPC(npc_data["npc_id"], npc_data["name"], npc_data["description"])
                            npc.from_dict(npc_data)
                            if hasattr(npc, 'level') and npc.level:
                                npc.tier = npc.get_tier()
                            self.npcs[npc.npc_id] = npc
                        print(f"Loaded {len(self.npcs)} NPCs from Firebase")
                        return
                except Exception as e:
                    print(f"Error loading NPCs from Firebase: {e}, falling back to files")
            
            # Try loading from individual contribution files first
            contributions_dir = "contributions/npcs"
            if os.path.exists(contributions_dir):
                count = 0
                for filename in os.listdir(contributions_dir):
                    if filename.endswith('.json') and filename != 'README.md':
                        filepath = os.path.join(contributions_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                npc_data = json.load(f)
                                npc = NPC(npc_data["npc_id"], npc_data["name"], npc_data["description"])
                                npc.from_dict(npc_data)
                                
                                # Set tier based on level if not already set
                                if hasattr(npc, 'level') and npc.level:
                                    npc.tier = npc.get_tier()
                                
                                # Initialize default values if missing
                                if not hasattr(npc, 'attributes') or not npc.attributes:
                                    npc.attributes = {
                                        "physical": 10,
                                        "mental": 10,
                                        "spiritual": 10,
                                        "social": 10
                                    }
                                if not hasattr(npc, 'skills') or not npc.skills:
                                    npc.skills = {}
                                if not hasattr(npc, 'loot_table'):
                                    npc.loot_table = []
                                if not hasattr(npc, 'exp_value'):
                                    npc.exp_value = 0
                                
                                # Ensure merchant fields are set if present in JSON
                                if "shop_inventory" in npc_data:
                                    npc.shop_inventory = npc_data["shop_inventory"]
                                if "keywords" in npc_data:
                                    npc.keywords = npc_data["keywords"]
                                if "is_merchant" in npc_data:
                                    npc.is_merchant = npc_data["is_merchant"]
                                if "faction" in npc_data:
                                    npc.faction = npc_data["faction"]
                                
                                self.npcs[npc.npc_id] = npc
                                
                                # If NPC has combat_role but missing stats, generate them
                                if hasattr(npc, 'combat_role') and npc.combat_role and npc.combat_role != "None":
                                    if not hasattr(npc, 'attributes') or not npc.attributes or all(v == 10 for v in npc.attributes.values()):
                                        try:
                                            from utils.npc_generator import NPCGenerator
                                            # Generate stats based on role and tier
                                            stats = NPCGenerator.generate_npc_stats(npc.combat_role, npc.tier, npc.level)
                                            npc.attributes = stats["attributes"]
                                            npc.max_health = stats["max_health"]
                                            npc.health = stats["max_health"]
                                            npc.exp_value = stats["exp_value"]
                                            
                                            # Generate skills
                                            npc.skills = NPCGenerator.generate_npc_skills(npc.combat_role, npc.tier, npc.level)
                                            
                                            # Set mana/stamina
                                            npc.max_mana = npc.attributes["spiritual"] * 5
                                            npc.mana = npc.max_mana
                                            npc.max_stamina = npc.attributes["physical"] * 10
                                            npc.stamina = npc.max_stamina
                                        except ImportError:
                                            pass  # NPC generator not available
                                count += 1
                        except Exception as e:
                            print(f"Error loading NPC file {filename}: {e}")
                
                if count > 0:
                    print(f"Loaded {count} NPCs from contributions/npcs/")
                    return
            
            # No NPCs found from Firebase or contributions
            print("No NPCs found")
        except Exception as e:
            print(f"Error loading NPCs from JSON: {e}")
            
    def load_items_from_json(self):
        """Load items from individual files in contributions/items/ subfolders or fallback to consolidated file."""
        try:
            # Try loading from individual contribution files first
            contributions_dir = "contributions/items"
            if os.path.exists(contributions_dir):
                count = 0
                # Check subfolders: weapons, armor, objects
                subfolders = ["weapons", "armor", "objects"]
                for subfolder in subfolders:
                    subfolder_path = os.path.join(contributions_dir, subfolder)
                    if os.path.exists(subfolder_path):
                        for filename in os.listdir(subfolder_path):
                            if filename.endswith('.json') and filename != 'README.md':
                                filepath = os.path.join(subfolder_path, filename)
                                try:
                                    with open(filepath, 'r', encoding='utf-8') as f:
                                        item_data = json.load(f)
                                        item = Item(item_data["item_id"], item_data["name"], item_data["description"], item_data.get("item_type", "item"))
                                        item.from_dict(item_data)
                                        
                                        # If item is a weapon but missing weapon stats, try to load from template
                                        if item.item_type == "weapon" and item.weapon_template_id and item.weapon_template_id in self.weapons:
                                            template = self.weapons[item.weapon_template_id]
                                            # Apply template if stats are missing
                                            if not hasattr(item, 'damage_min') or item.damage_min == 0:
                                                item.category = template.get("category")
                                                item.weapon_class = template.get("class")
                                                item.hands = template.get("hands", 1)
                                                item.range = template.get("range", 0)
                                                item.damage_min = template.get("damage_min", 0)
                                                item.damage_max = template.get("damage_max", 0)
                                                item.damage_type = template.get("damage_type")
                                                item.crit_chance = template.get("crit_chance", 0.0)
                                                item.speed_cost = template.get("speed_cost", 1.0)
                                                item.max_durability = template.get("durability", 50)
                                                if item.current_durability is None:
                                                    item.current_durability = item.max_durability
                                        
                                        self.items[item.item_id] = item
                                        count += 1
                                except Exception as e:
                                    print(f"Error loading item file {filename}: {e}")
                
                if count > 0:
                    print(f"Loaded {count} items from contributions/items/")
                    return
            
            # Try Firebase as fallback for items
            if self.use_firebase and self.firebase:
                try:
                    items_data = self.firebase.load_items()
                    if items_data:
                        for item_id, item_data in items_data.items():
                            item = Item(item_data["item_id"], item_data["name"], item_data["description"], item_data.get("item_type", "item"))
                            item.from_dict(item_data)
                            
                            # If item is a weapon but missing weapon stats, try to load from template
                            if item.item_type == "weapon" and item.weapon_template_id and item.weapon_template_id in self.weapons:
                                template = self.weapons[item.weapon_template_id]
                                if not hasattr(item, 'damage_min') or item.damage_min == 0:
                                    item.category = template.get("category")
                                    item.weapon_class = template.get("class")
                                    item.hands = template.get("hands", 1)
                                    item.range = template.get("range", 0)
                                    item.damage_min = template.get("damage_min", 0)
                                    item.damage_max = template.get("damage_max", 0)
                                    item.damage_type = template.get("damage_type")
                                    item.crit_chance = template.get("crit_chance", 0.0)
                                    item.speed_cost = template.get("speed_cost", 1.0)
                                    item.max_durability = template.get("durability", 50)
                                    if item.current_durability is None:
                                        item.current_durability = item.max_durability
                            
                            self.items[item.item_id] = item
                        print(f"Loaded {len(self.items)} items from Firebase")
                        return
                except Exception as e:
                    print(f"Error loading items from Firebase: {e}")
            
            # No items found
            print("No items found")
        except Exception as e:
            print(f"Error loading items from JSON: {e}")
    
    def load_shop_items(self):
        """Load shop items from individual files in contributions/shop_items/ or fallback to consolidated file."""
        shop_items_data = {}
        
        # Try loading from individual contribution files first
        contributions_dir = "contributions/shop_items"
        if os.path.exists(contributions_dir):
            for filename in os.listdir(contributions_dir):
                if filename.endswith('.json') and filename != 'README.md':
                    filepath = os.path.join(contributions_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            item_data = json.load(f)
                            item_id = item_data.get("item_id")
                            if item_id:
                                shop_items_data[item_id] = item_data
                    except Exception as e:
                        print(f"Error loading shop item file {filename}: {e}")
            
            if shop_items_data:
                return shop_items_data
        
        # Try Firebase as fallback
        if not shop_items_data and self.use_firebase and self.firebase:
            try:
                shop_items_data = self.firebase.load_shop_items()
                if shop_items_data:
                    print(f"Loaded {len(shop_items_data)} shop items from Firebase")
            except Exception as e:
                print(f"Error loading shop items from Firebase: {e}")
        
        return shop_items_data
            
    def save_rooms_to_json(self):
        try:
            with self.world_lock:
                rooms_data = {
                    "rooms": [room.to_dict() for room in self.rooms.values()]
                }
                with open("rooms.json", 'w') as f:
                    json.dump(rooms_data, f, indent=2)
                print(f"Saved {len(self.rooms)} rooms to rooms.json")
        except Exception as e:
            print(f"Error saving rooms to JSON: {e}")
            
    def load_maneuvers(self):
        """Load maneuvers from individual files in contributions/maneuvers/ or fallback to consolidated file."""
        try:
            # Try loading from individual contribution files first
            contributions_dir = "contributions/maneuvers"
            if os.path.exists(contributions_dir):
                count = 0
                for filename in os.listdir(contributions_dir):
                    if filename.endswith('.json') and filename != 'README.md':
                        filepath = os.path.join(contributions_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                maneuver_data = json.load(f)
                                maneuver_id = maneuver_data.get('maneuver_id')
                                if maneuver_id:
                                    self.maneuvers[maneuver_id] = maneuver_data
                                    count += 1
                        except Exception as e:
                            print(f"Error loading maneuver file {filename}: {e}")
                
                if count > 0:
                    print(f"Loaded {count} maneuvers from contributions/maneuvers/")
                    return
            
            # Fallback to consolidated file
            if os.path.exists("maneuvers.json"):
                with open("maneuvers.json", 'r') as f:
                    data = json.load(f)
                    for maneuver_data in data["maneuvers"]:
                        self.maneuvers[maneuver_data["maneuver_id"]] = maneuver_data
                print(f"Loaded {len(self.maneuvers)} maneuvers from maneuvers.json")
        except Exception as e:
            print(f"Error loading maneuvers: {e}")
            
    def load_planets(self):
        """Load planets from individual files in contributions/planets/ or fallback to consolidated file."""
        try:
            # Try loading from individual contribution files first
            contributions_dir = "contributions/planets"
            if os.path.exists(contributions_dir):
                count = 0
                for filename in os.listdir(contributions_dir):
                    if filename.endswith('.json') and filename != 'README.md':
                        filepath = os.path.join(contributions_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                planet_data = json.load(f)
                                planet_id = planet_data.get('planet_id')
                                if planet_id:
                                    self.planets[planet_id] = planet_data
                                    count += 1
                        except Exception as e:
                            print(f"Error loading planet file {filename}: {e}")
                
                if count > 0:
                    print(f"Loaded {count} planets from contributions/planets/")
                    return
            
            # Fallback to consolidated file
            if os.path.exists("planets.json"):
                with open("planets.json", 'r') as f:
                    data = json.load(f)
                    for planet_data in data["planets"]:
                        self.planets[planet_data["planet_id"]] = planet_data
                print(f"Loaded {len(self.planets)} planets from planets.json")
        except Exception as e:
            print(f"Error loading planets: {e}")
            
    def load_races(self):
        """Load races from individual files in contributions/races/ or fallback to consolidated file."""
        try:
            # Try loading from individual contribution files first
            contributions_dir = "contributions/races"
            if os.path.exists(contributions_dir):
                count = 0
                for filename in os.listdir(contributions_dir):
                    if filename.endswith('.json') and filename != 'README.md':
                        filepath = os.path.join(contributions_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                race_data = json.load(f)
                                race_id = race_data.get('race_id')
                                if race_id:
                                    self.races[race_id] = race_data
                                    count += 1
                        except Exception as e:
                            print(f"Error loading race file {filename}: {e}")
                
                if count > 0:
                    print(f"Loaded {count} races from contributions/races/")
                    return
            
            # Fallback to consolidated file
            if os.path.exists("races.json"):
                with open("races.json", 'r') as f:
                    data = json.load(f)
                    for race_data in data["races"]:
                        self.races[race_data["race_id"]] = race_data
                print(f"Loaded {len(self.races)} races from races.json")
        except Exception as e:
            print(f"Error loading races: {e}")
            
    def load_starsigns(self):
        """Load starsigns from individual files in contributions/starsigns/ or fallback to consolidated file."""
        try:
            # Try loading from individual contribution files first
            contributions_dir = "contributions/starsigns"
            if os.path.exists(contributions_dir):
                count = 0
                for filename in os.listdir(contributions_dir):
                    if filename.endswith('.json') and filename != 'README.md':
                        filepath = os.path.join(contributions_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                starsign_data = json.load(f)
                                starsign_id = starsign_data.get('starsign_id')
                                if starsign_id:
                                    self.starsigns[starsign_id] = starsign_data
                                    count += 1
                        except Exception as e:
                            print(f"Error loading starsign file {filename}: {e}")
                
                if count > 0:
                    print(f"Loaded {count} starsigns from contributions/starsigns/")
                    return
            
            # Fallback to consolidated file
            if os.path.exists("starsigns.json"):
                with open("starsigns.json", 'r') as f:
                    data = json.load(f)
                    for starsign_data in data["starsigns"]:
                        self.starsigns[starsign_data["starsign_id"]] = starsign_data
                print(f"Loaded {len(self.starsigns)} starsigns from starsigns.json")
        except Exception as e:
            print(f"Error loading starsigns: {e}")
    
    def load_weapons(self):
        """Load weapon templates from individual files in contributions/weapons/ or fallback to consolidated file."""
        try:
            # Try loading from individual contribution files first
            contributions_dir = "contributions/weapons"
            if os.path.exists(contributions_dir):
                count = 0
                for filename in os.listdir(contributions_dir):
                    if filename.endswith('.json') and filename != 'README.md':
                        filepath = os.path.join(contributions_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                weapon_data = json.load(f)
                                weapon_id = weapon_data.get('id')
                                if weapon_id:
                                    self.weapons[weapon_id] = weapon_data
                                    count += 1
                        except Exception as e:
                            print(f"Error loading weapon file {filename}: {e}")
                
                if count > 0:
                    print(f"Loaded {count} weapon templates from contributions/weapons/")
                    return
            
            # Fallback to consolidated file
            if os.path.exists("weapons.json"):
                with open("weapons.json", 'r') as f:
                    data = json.load(f)
                    for weapon_data in data.get("weapons", []):
                        self.weapons[weapon_data["id"]] = weapon_data
                print(f"Loaded {len(self.weapons)} weapon templates from weapons.json")
        except Exception as e:
            print(f"Error loading weapons: {e}")
    
    def load_weapon_modifiers(self):
        """Load weapon modifiers from individual files in contributions/weapon_modifiers/ or fallback to consolidated file."""
        try:
            # Try loading from individual contribution files first
            contributions_dir = "contributions/weapon_modifiers"
            if os.path.exists(contributions_dir):
                count = 0
                for filename in os.listdir(contributions_dir):
                    if filename.endswith('.json') and filename != 'README.md':
                        filepath = os.path.join(contributions_dir, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                modifier_data = json.load(f)
                                modifier_id = modifier_data.get('id')
                                if modifier_id:
                                    self.weapon_modifiers[modifier_id] = modifier_data
                                    count += 1
                        except Exception as e:
                            print(f"Error loading weapon modifier file {filename}: {e}")
                
                if count > 0:
                    print(f"Loaded {count} weapon modifiers from contributions/weapon_modifiers/")
                    return
            
            # Fallback to consolidated file
            if os.path.exists("weapon_modifiers.json"):
                with open("weapon_modifiers.json", 'r') as f:
                    data = json.load(f)
                    for modifier_data in data.get("modifiers", []):
                        self.weapon_modifiers[modifier_data["id"]] = modifier_data
                print(f"Loaded {len(self.weapon_modifiers)} weapon modifiers from weapon_modifiers.json")
        except Exception as e:
            print(f"Error loading weapon modifiers: {e}")
    
    def load_world_time(self):
        """Load saved world time from Firebase"""
        try:
            if not self.world_time:
                return
            
            # Load from Firebase only
            if self.use_firebase and self.firebase:
                try:
                    config_data = self.firebase.load_config('world_time')
                    if config_data and "world_seconds" in config_data:
                        self.world_time.set_world_seconds(config_data["world_seconds"])
                        print(f"Loaded world time from Firebase: Day {self.world_time.get_day_number()}, {self.world_time.get_hour():02d}:{self.world_time.get_minute():02d}")
                    else:
                        print("No saved world time found in Firebase, using default")
                except Exception as e:
                    print(f"Error loading world time from Firebase: {e}")
            else:
                print("Warning: Firebase not available, cannot load world time")
        except Exception as e:
            print(f"Error loading world time: {e}")
    
    def save_world_time(self):
        """Save world time to Firebase"""
        try:
            if not self.world_time:
                return
            
            data = {
                "world_seconds": self.world_time.get_world_seconds()
            }
            
            # Save to Firebase only
            if self.use_firebase and self.firebase:
                try:
                    self.firebase.save_config('world_time', data)
                except Exception as e:
                    print(f"Error saving world time to Firebase: {e}")
            else:
                print("Warning: Firebase not available, cannot save world time")
        except Exception as e:
            print(f"Error saving world time: {e}")
    
    def load_npc_schedules(self):
        """Load NPC schedules from Firebase"""
        try:
            if not self.npc_scheduler:
                return
            
            # Load from Firebase only
            if self.use_firebase and self.firebase:
                try:
                    config_data = self.firebase.load_config('npc_schedules')
                    if config_data:
                        schedules = config_data.get('schedules', {})
                        for npc_id, schedule_blocks in schedules.items():
                            self.npc_scheduler.add_npc_schedule(npc_id, schedule_blocks)
                        print(f"Loaded schedules for {len(schedules)} NPCs from Firebase")
                    else:
                        print("No NPC schedules found in Firebase")
                except Exception as e:
                    print(f"Error loading NPC schedules from Firebase: {e}")
            else:
                print("Warning: Firebase not available, cannot load NPC schedules")
        except Exception as e:
            print(f"Error loading NPC schedules: {e}")
    
    def load_store_hours(self):
        """Load store hours from Firebase"""
        try:
            if not self.store_hours:
                return
            
            # Load from Firebase only
            if self.use_firebase and self.firebase:
                try:
                    config_data = self.firebase.load_config('store_hours')
                    if config_data:
                        stores = config_data.get('stores', {})
                        for store_id, hours_data in stores.items():
                            self.store_hours.set_store_hours(
                                store_id,
                                hours_data.get("open_time", "08:00"),
                                hours_data.get("close_time", "18:00"),
                                hours_data.get("closed_days", []),
                                hours_data.get("festival_days", [])
                            )
                        print(f"Loaded hours for {len(stores)} stores from Firebase")
                    else:
                        print("No store hours found in Firebase")
                except Exception as e:
                    print(f"Error loading store hours from Firebase: {e}")
            else:
                print("Warning: Firebase not available, cannot load store hours")
        except Exception as e:
            print(f"Error loading store hours: {e}")
    
    def create_weapon_item(self, weapon_template_id, modifier_id=None, item_id=None):
        """Create an Item from a weapon template, optionally applying a modifier"""
        if weapon_template_id not in self.weapons:
            return None
        
        template = self.weapons[weapon_template_id]
        
        # Create item ID if not provided
        if item_id is None:
            if modifier_id:
                item_id = f"{modifier_id}_{weapon_template_id}"
            else:
                item_id = weapon_template_id
        
        # Create base item
        item = Item(item_id, template["name"], template.get("description", ""), "weapon")
        item.weapon_template_id = weapon_template_id
        
        # Apply template stats
        item.category = template["category"]
        item.weapon_class = template["class"]
        item.hands = template["hands"]
        item.range = template["range"]
        item.damage_min = template["damage_min"]
        item.damage_max = template["damage_max"]
        item.damage_type = template["damage_type"]
        item.crit_chance = template["crit_chance"]
        item.speed_cost = template["speed_cost"]
        item.max_durability = template["durability"]
        item.current_durability = template["durability"]
        
        # Apply modifier if provided
        if modifier_id and modifier_id in self.weapon_modifiers:
            modifier = self.weapon_modifiers[modifier_id]
            item.weapon_modifier_id = modifier_id
            
            # Update name
            item.name = f"{modifier['name']} {template['name']}"
            
            # Apply damage bonus
            item.damage_min = max(1, item.damage_min + modifier.get("damage_bonus", 0))
            item.damage_max = max(item.damage_min, item.damage_max + modifier.get("damage_bonus", 0))
            
            # Apply crit bonus
            item.crit_chance = min(1.0, item.crit_chance + modifier.get("crit_bonus", 0))
            
            # Apply speed multiplier
            item.speed_cost = item.speed_cost * modifier.get("speed_multiplier", 1.0)
            
            # Apply durability bonus
            item.max_durability = max(1, item.max_durability + modifier.get("durability_bonus", 0))
            item.current_durability = item.max_durability
            
            # Apply damage type override if present
            if "damage_type_override" in modifier:
                item.damage_type = modifier["damage_type_override"]
        
        return item
            
    def save_world_data(self):
        """Save world state including time"""
        self.save_world_time()
        try:
            # Save to Firebase only
            if self.use_firebase and self.firebase:
                with self.world_lock:
                    # Save rooms to Firebase
                    rooms_dict = {room.room_id: room.to_dict() for room in self.rooms.values()}
                    self.firebase.batch_save_rooms(rooms_dict)
                    print(f"Saved {len(self.rooms)} rooms to Firebase")
                    
                    # Save NPCs to Firebase
                    npcs_dict = {npc.npc_id: npc.to_dict() for npc in self.npcs.values()}
                    self.firebase.batch_save_npcs(npcs_dict)
                    print(f"Saved {len(self.npcs)} NPCs to Firebase")
                    
                    # Save items to Firebase
                    items_dict = {item.item_id: item.to_dict() for item in self.items.values()}
                    self.firebase.batch_save_items(items_dict)
                    print(f"Saved {len(self.items)} items to Firebase")
            else:
                print("Warning: Firebase not available, cannot save world data")
        except Exception as e:
            print(f"Error saving world data: {e}")
            
    def sanitize_player_name(self, name):
        """Sanitize player name to prevent path traversal attacks"""
        # Remove all non-alphanumeric except underscore and hyphen
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', str(name))
        # Limit length
        sanitized = sanitized[:20]
        # Ensure it's not empty
        if not sanitized:
            raise ValueError("Invalid player name")
        return sanitized
    
    def check_rate_limit(self, player_name):
        """Check if player has exceeded rate limit"""
        now = time.time()
        player_commands = self.rate_limiter[player_name]
        # Remove old commands outside 1 second window
        player_commands[:] = [t for t in player_commands if now - t < 1.0]
        
        if len(player_commands) >= self.max_commands_per_second:
            return False
        player_commands.append(now)
        return True
    
    def validate_command(self, command):
        """Validate command input for security"""
        if not command:
            return False
        if len(command) > 512:  # Limit command length
            return False
        # Check for potentially dangerous patterns
        dangerous_patterns = ['../', '..\\', '<script', 'javascript:', 'eval(']
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False
        return True
    
    
    def load_admin_config(self):
        """Load admin configuration from Firebase"""
        default_config = {
            "admins": {
                "admin": {"permissions": ["all"]},
                "god": {"permissions": ["all"]},
                "builder": {"permissions": ["rooms", "items"]}
            }
        }
        
        try:
            # Try Firebase first
            if self.use_firebase and self.firebase:
                try:
                    config = self.firebase.load_config('admin_config')
                    if config:
                        return config
                except Exception as e:
                    print(f"Error loading admin config from Firebase: {e}")
            
            # Return default if Firebase not available or config doesn't exist
            # Save default to Firebase if Firebase is available
            if self.use_firebase and self.firebase:
                try:
                    self.firebase.save_config('admin_config', default_config)
                except Exception as e:
                    print(f"Error saving default admin config to Firebase: {e}")
            
            return default_config
        except Exception as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_error("CONFIG_LOAD_ERROR", str(e))
            else:
                print(f"Error loading admin config: {e}")
            return default_config
    
    def save_admin_config(self, config=None):
        """Save admin configuration to Firebase"""
        if config is None:
            config = self.admin_config
        try:
            if self.use_firebase and self.firebase:
                self.firebase.save_config('admin_config', config)
            else:
                print("Warning: Firebase not available, cannot save admin config")
        except Exception as e:
            if hasattr(self, 'logger') and self.logger:
                self.logger.log_error("CONFIG_SAVE_ERROR", str(e))
            else:
                print(f"Error saving admin config: {e}")
    
    def validate_json_structure(self, data, expected_keys=None):
        """Validate JSON structure to prevent malicious data"""
        if not isinstance(data, dict):
            return False
        if expected_keys:
            for key in expected_keys:
                if key not in data:
                    return False
        # Check for reasonable data sizes
        json_str = json.dumps(data)
        if len(json_str) > 1000000:  # 1MB limit
            return False
        return True
    
    def save_player_data(self, player):
        """Save player data to Firebase"""
        try:
            with self.player_lock:
                player_data = player.to_dict()
                
                # Save to Firebase only
                if self.use_firebase and self.firebase:
                    try:
                        self.firebase.save_player(player.name, player_data)
                    except Exception as e:
                        print(f"Error saving player to Firebase: {e}")
                        raise
                else:
                    print("Error: Firebase not available, cannot save player data")
                    raise RuntimeError("Firebase not available")
        except Exception as e:
            print(f"Error saving player data: {e}")
            
    def load_player_data(self, player_name):
        """Load player data from Firebase"""
        try:
            # Load from Firebase only
            if self.use_firebase and self.firebase:
                try:
                    player_data = self.firebase.load_player(player_name)
                    if player_data:
                        # Validate JSON structure
                        expected_keys = ['name', 'room_id', 'health', 'level']
                        if self.validate_json_structure(player_data, expected_keys):
                            return player_data
                        else:
                            if self.logger:
                                self.logger.log_security_event("INVALID_JSON", player_name, "Malformed player data from Firebase")
                            return None
                    return None
                except Exception as e:
                    print(f"Error loading player from Firebase: {e}")
                    return None
            else:
                print("Error: Firebase not available, cannot load player data")
                return None
                
                with open(filename, 'r') as f:
                    player_data = json.load(f)
                    
                    # Validate JSON structure
                    expected_keys = ['name', 'room_id', 'health', 'level']
                    if not self.validate_json_structure(player_data, expected_keys):
                        if self.logger:
                            self.logger.log_security_event("INVALID_JSON", player_name, "Malformed player data")
                        return None
                    
                    return player_data
        except (json.JSONDecodeError, ValueError) as e:
            if self.logger:
                self.logger.log_error("PLAYER_LOAD_ERROR", str(e))
            print(f"Error loading player data: {e}")
        except Exception as e:
            if self.logger:
                self.logger.log_error("PLAYER_LOAD_ERROR", str(e))
            print(f"Error loading player data: {e}")
        return None
        
    def create_default_world(self):
        """Create default world items if none exist (deprecated - use contributions instead)."""
        # This method is kept for backwards compatibility but is no longer used
        # World content is now loaded from contributions/ directory
        pass
            
        if "goblin" not in self.npcs:
            goblin = NPC("goblin", "Goblin", "A nasty looking goblin with sharp teeth.")
            goblin.is_hostile = True
            goblin.health = 30
            goblin.max_health = 30
            goblin.inventory = ["potion", "gold"]
            self.npcs["goblin"] = goblin
            
        if "gold" not in self.items:
            gold = Item("gold", "Gold Coins", "Shiny gold coins.", "item")
            gold.value = 1
            self.items["gold"] = gold
            
        self.save_world_data()
        
    def add_player(self, player):
        with self.player_lock:
            self.players[player.name] = player
            self.player_login_time[player.name] = time.time()

    def remove_player(self, player_name):
        # Get player data while holding lock (quick operation)
        player_to_save = None
        with self.player_lock:
            if player_name in self.players:
                player_to_save = self.players[player_name]
                del self.players[player_name]
            if player_name in self.player_login_time:
                del self.player_login_time[player_name]
        
        # Call Firebase OUTSIDE the lock (can block, but lock is released)
        if player_to_save is not None:
            self.save_player_data(player_to_save)
                
    def get_room(self, room_id):
        return self.rooms.get(room_id)
        
    def get_player(self, player_name):
        return self.players.get(player_name)
        
    def broadcast_to_room(self, room_id, message, exclude_player=None):
        room = self.get_room(room_id)
        if room:
            for player_name in room.players:
                if player_name != exclude_player:
                    player = self.get_player(player_name)
                    if player and player.is_logged_in:
                        self.send_to_player_raw(player, message)
                        
    def send_to_player_raw(self, player, message):
        try:
            # Check if it's a WebSocket connection
            if isinstance(player.connection, WebSocketConnection):
                # WebSocket - strip ANSI codes and colorize brackets with HTML
                message_clean = self.strip_ansi(message)
                message_clean = self.colorize_brackets(message_clean, is_websocket=True)
                player.connection.send(message_clean)
            else:
                # Regular socket connection - colorize brackets with ANSI and encode to bytes
                message = self.colorize_brackets(message, is_websocket=False)
                player.connection.send(message.encode() + b'\n\r')
        except:
            player.is_logged_in = False
    
    def get_exit_target(self, exit_data):
        """Extract target room ID from exit data (handles both string and dict formats)"""
        if isinstance(exit_data, str):
            return exit_data
        elif isinstance(exit_data, dict):
            return exit_data.get("target")
        return None
    
    def get_exit_door(self, exit_data):
        """Get door/obstacle info from exit data"""
        if isinstance(exit_data, dict):
            return exit_data.get("door") or exit_data.get("obstacle")
        return None
            
    def look_command(self, player, args):
        room = self.get_room(player.room_id)
        if not room:
            self.send_to_player(player, self.format_error("You are in an unknown location."))
            return
        
        # Handle "look <npc>" command
        if args:
            npc_name = " ".join(args).lower()
            
            # Check for scheduled NPCs
            present_npc_ids = set(room.npcs)
            if self.npc_scheduler:
                scheduled_npcs = self.npc_scheduler.get_present_npcs(room.room_id)
                present_npc_ids.update(scheduled_npcs)
            
            # Try to find NPC
            npc = None
            for npc_id in present_npc_ids:
                n = self.npcs.get(npc_id)
                if n and npc_name in n.name.lower():
                    npc = n
                    break
            
            if npc:
                self.look_npc(player, npc)
                return
            
            # Handle "look <direction>" command
            direction = args[0].lower()
            self.look_direction(player, room, direction)
            return
            
        output = f"\n{self.format_header(room.name)}\n{room.description}\n"
        
        if room.exits:
            exits = []
            for direction in room.exits.keys():
                exits.append(self.format_exit(direction))
            output += f"\nExits: {' '.join(exits)}"
            
        other_players = [p for p in room.players if p != player.name]
        if other_players:
            player_list = ", ".join(other_players)
            output += f"\nPlayers here: {player_list}"
            
        # Check for scheduled NPCs (lazy presence)
        present_npc_ids = set(room.npcs)  # Start with static NPCs
        if self.npc_scheduler:
            # Check if NPCs can change schedule (not in combat, transaction, etc.)
            def can_change_schedule(npc_id):
                npc = self.npcs.get(npc_id)
                if not npc:
                    return True
                # Check if NPC is in combat
                if self.combat_manager:
                    combat = self.combat_manager.get_combat_state(room.room_id)
                    if combat and combat.is_active:
                        if npc_id in [name for name in combat.combatants.keys()]:
                            return False  # In combat, defer schedule change
                # Note: Additional checks for transactions, dialogue, etc. can be added here
                return True
            
            scheduled_npcs = self.npc_scheduler.get_present_npcs(room.room_id, can_change_schedule)
            present_npc_ids.update(scheduled_npcs)
        
        if present_npc_ids:
            npcs_here = []
            for npc_id in present_npc_ids:
                npc = self.npcs.get(npc_id)
                if npc:
                    npcs_here.append(self.format_npc(npc.name))
            if npcs_here:
                output += f"\nNPCs here: {', '.join(npcs_here)}"
            
        if room.items:
            items_here = []
            for item_id in room.items:
                item = self.items.get(item_id)
                if item:
                    items_here.append(self.format_item(item.name))
            output += f"\nItems here: {', '.join(items_here)}"
            
        # Show room flags if present
        if room.flags:
            flags_text = ", ".join(room.flags)
            output += f"\nRoom flags: {self.format_brackets(flags_text, 'orange')}"
        
        # Show combat tags if present
        if room.combat_tags:
            tags_text = ", ".join(room.combat_tags)
            output += f"\nCombat environment: {self.format_brackets(tags_text, 'yellow')}"
        
        # Show combat status if active
        if self.combat_manager:
            combat = self.combat_manager.get_combat_state(player.room_id)
            if combat and combat.is_active:
                output += f"\n{self.format_header('COMBAT IN PROGRESS')}"
                combatants = list(combat.combatants.keys())
                output += f"Combatants: {', '.join(combatants)}"
                if player.name not in combatants:
                    output += f"\nYou are observing. Use {self.format_command('join combat')} to participate."
            
        self.send_to_player(player, output)
    
    def look_npc(self, player, npc):
        """Look at an NPC to see detailed information"""
        output = f"\n{self.format_header(npc.name)}\n"
        output += f"{npc.description}\n\n"
        
        # Show status
        if hasattr(npc, 'health') and hasattr(npc, 'max_health'):
            health_pct = (npc.health / npc.max_health * 100) if npc.max_health > 0 else 0
            if health_pct < 25:
                status = "critically wounded"
            elif health_pct < 50:
                status = "wounded"
            elif health_pct < 75:
                status = "injured"
            else:
                status = "healthy"
            output += f"Status: {status} ({npc.health}/{npc.max_health} health)\n"
        
        # Show if merchant
        if hasattr(npc, 'is_merchant') and npc.is_merchant:
            output += f"Role: {self.format_brackets('Merchant', 'yellow')}\n"
            if self.store_hours:
                room = self.get_room(player.room_id)
                if room and room.room_id in self.store_hours.store_hours:
                    store_status = self.store_hours.get_store_status(room.room_id)
                    status_color = "green" if store_status == "Open" else "yellow"
                    output += f"Shop: {self.format_brackets(store_status, status_color)}\n"
        
        # Show outlook if player has interacted
        if hasattr(npc, 'outlooks') and player.name in npc.outlooks:
            outlook = npc.outlooks[player.name]
            if outlook <= -50:
                outlook_desc = "Hostile"
            elif outlook <= -20:
                outlook_desc = "Unfriendly"
            elif outlook < 0:
                outlook_desc = "Slightly negative"
            elif outlook == 0:
                outlook_desc = "Neutral"
            elif outlook < 30:
                outlook_desc = "Friendly"
            else:
                outlook_desc = "Trusted"
            output += f"Outlook toward you: {outlook_desc} ({outlook})\n"
        
        # Show equipped items if any
        if hasattr(npc, 'equipped') and npc.equipped:
            equipped_items = []
            for slot, item_id in npc.equipped.items():
                item = self.items.get(item_id)
                if item:
                    equipped_items.append(f"{slot}: {item.name}")
            if equipped_items:
                output += f"Equipped: {', '.join(equipped_items)}\n"
        
        # Show dialogue hint
        if hasattr(npc, 'dialogue') and npc.dialogue:
            output += f"\n{self.format_header('Greeting:')}\n"
            output += f"{npc.dialogue[0]}\n"
        
        # Show available keywords if merchant
        if hasattr(npc, 'is_merchant') and npc.is_merchant:
            output += f"\n{self.format_header('Available Actions:')}\n"
            output += f"Use {self.format_command('talk jalia buy')} or {self.format_command('talk jalia shop')} to see items for sale\n"
            output += f"Use {self.format_command('talk jalia sell')} to sell items\n"
            output += f"Use {self.format_command('talk jalia repair')} or {self.format_command('talk jalia repairs')} for repair services\n"
            output += f"Use {self.format_command('list')} or {self.format_command('shop')} to browse inventory\n"
        
        self.send_to_player(player, output)
    
    def look_direction(self, player, room, direction):
        """Look in a specific direction, respecting doors and obstacles"""
        # Normalize direction (handle abbreviations)
        direction_map = {
            'n': 'north', 's': 'south', 'e': 'east', 'w': 'west',
            'ne': 'northeast', 'nw': 'northwest', 'se': 'southeast', 'sw': 'southwest',
            'u': 'up', 'd': 'down', 'in': 'in', 'out': 'out'
        }
        direction = direction_map.get(direction, direction)
        
        # Check if exit exists
        if direction not in room.exits:
            available = ", ".join([self.format_exit(d) for d in room.exits.keys()])
            self.send_to_player(player, self.format_error(f"You cannot look {self.format_brackets(direction)}. Available directions: {available}"))
            return
        
        exit_data = room.exits[direction]
        target_room_id = self.get_exit_target(exit_data)
        door_info = self.get_exit_door(exit_data)
        
        # Check if there's a door or obstacle blocking the view
        if door_info:
            if isinstance(door_info, str):
                # Simple string description
                self.send_to_player(player, f"You look {self.format_exit(direction)}, but {door_info} blocks your view.")
            elif isinstance(door_info, dict):
                # Detailed door/obstacle info
                door_desc = door_info.get("description", "something blocks your view")
                door_name = door_info.get("name", "A door")
                self.send_to_player(player, f"You look {self.format_exit(direction)}, but {door_name} blocks your view. {door_desc}")
            else:
                self.send_to_player(player, f"You look {self.format_exit(direction)}, but something blocks your view.")
            return
        
        # No door/obstacle - show the adjacent room
        if not target_room_id:
            self.send_to_player(player, self.format_error("That direction leads to an unknown place."))
            return
        
        target_room = self.get_room(target_room_id)
        if not target_room:
            self.send_to_player(player, self.format_error("That direction leads to an unknown place."))
            return
        
        # Show what can be seen in that direction
        output = f"\n{self.format_header(f'Looking {self.format_exit(direction)}')}\n"
        output += f"You can see: {self.format_header(target_room.name)}\n"
        output += f"{target_room.description}\n"
        
        # Show visible players/NPCs in the adjacent room
        if target_room.players:
            visible_players = [p for p in target_room.players if p != player.name]
            if visible_players:
                output += f"\nYou can see {', '.join(visible_players)} there.\n"
        
        if target_room.npcs:
            npcs_visible = []
            for npc_id in target_room.npcs:
                npc = self.npcs.get(npc_id)
                if npc:
                    npcs_visible.append(self.format_npc(npc.name))
            if npcs_visible:
                output += f"You can see {', '.join(npcs_visible)} there.\n"
        
        self.send_to_player(player, output)
        
    def move_command(self, player, direction):
        room = self.get_room(player.room_id)
        if not room:
            self.send_to_player(player, self.format_error("You are in an unknown location."))
            return
            
        if direction not in room.exits:
            available_exits = ", ".join([self.format_exit(d) for d in room.exits.keys()])
            self.send_to_player(player, self.format_error(f"You cannot go {self.format_brackets(direction)}. Available exits: {available_exits}"))
            return
            
        old_room_id = player.room_id
        # Handle both string and dict exit formats
        exit_data = room.exits[direction]
        new_room_id = self.get_exit_target(exit_data)
        new_room = self.get_room(new_room_id)
        
        if not new_room:
            self.send_to_player(player, self.format_error("That direction leads to an unknown place."))
            return
        
        # Check if target room is a shop that's currently closed
        if self.store_hours and new_room_id in self.store_hours.store_hours:
            if not self.store_hours.is_store_open(new_room_id):
                status = self.store_hours.get_store_status(new_room_id)
                self.send_to_player(player, self.format_error(f"The shop is {status.lower()}. You cannot enter while it's closed."))
                return
            
        room.players.discard(player.name)
        new_room.players.add(player.name)
        player.room_id = new_room_id
        
        # Exploration EXP reward (first time visiting a room)
        if new_room_id not in self.explored_rooms[player.name]:
            self.explored_rooms[player.name].add(new_room_id)
            exp_gain = 10  # Base exploration EXP
            player.experience += exp_gain
            self.send_to_player(player, self.format_success(f"You discover a new area! +{exp_gain} EXP"))
            
            # Update quest progress (explore room)
            if self.quest_manager:
                completed = self.quest_manager.update_quest_progress(
                    player.name, "explore_room", new_room_id, 1
                )
                for quest in completed:
                    player.experience += quest.exp_reward
                    self.send_to_player(player, f"{self.format_header('Quest Complete!')}")
                    self.send_to_player(player, f"Quest: {quest.name}")
                    self.send_to_player(player, f"You gain {quest.exp_reward} EXP from quest completion!")
            
            self.check_level_up(player)
        
        self.broadcast_to_room(old_room_id, f"{player.name} leaves {direction}.", player.name)
        self.send_to_player(player, self.format_success(f"You move {self.format_exit(direction)}."))
        if COMMANDS_AVAILABLE:
            look_command(self, player, [])
        else:
            self.look_command(player, [])
        self.broadcast_to_room(new_room_id, f"{player.name} arrives.", player.name)
        
    def say_command(self, player, args):
        if not args:
            self.send_to_player(player, "Say what?")
            return
            
        message = " ".join(args)
        self.broadcast_to_room(player.room_id, f"{player.name} says: {message}")
        
    def inventory_command(self, player, args):
        if not player.inventory:
            self.send_to_player(player, "You are not carrying anything.")
            return
            
        output = self.format_header("You are carrying:") + "\n"
        for item_id in player.inventory:
            item = self.items.get(item_id)
            if item:
                item_name = self.format_item(item.name)
                equipped_mark = ""
                # Check if item is equipped
                for slot, eq_item_id in player.equipped.items():
                    if eq_item_id == item_id:
                        equipped_mark = f" [{self.format_brackets('EQUIPPED', 'green')}]"
                        break
                
                output += f"- {item_name}{equipped_mark}: {item.description}"
                
                # Show weapon stats if it's a weapon
                if item.is_weapon():
                    damage_min, damage_max = item.get_effective_damage()
                    output += f"\n  Damage: {damage_min}-{damage_max} ({item.damage_type}), Crit: {int(item.get_effective_crit_chance() * 100)}%, Durability: {item.get_current_durability()}/{item.max_durability}"
                
                output += "\n"
                
        self.send_to_player(player, output.strip())
        
    def get_command(self, player, args):
        if not args:
            self.send_to_player(player, "Get what?")
            return
            
        item_name = " ".join(args).lower()
        room = self.get_room(player.room_id)
        
        if not room:
            self.send_to_player(player, "You are in an unknown location.")
            return
        
        for item_id in room.items[:]:
            item = self.items.get(item_id)
            if item and item_name in item.name.lower():
                room.items.remove(item_id)
                player.inventory.append(item_id)
                item_display = self.format_item(item.name)
                self.send_to_player(player, self.format_success(f"You pick up {item_display}."))
                self.broadcast_to_room(player.room_id, f"{player.name} picks up {item_display}.", player.name)
                return
                
        self.send_to_player(player, "You don't see that here.")
        
    def drop_command(self, player, args):
        if not args:
            self.send_to_player(player, "Drop what?")
            return
            
        item_name = " ".join(args).lower()
        room = self.get_room(player.room_id)
        
        if not room:
            self.send_to_player(player, "You are in an unknown location.")
            return
        
        for item_id in player.inventory[:]:
            item = self.items.get(item_id)
            if item and item_name in item.name.lower():
                player.inventory.remove(item_id)
                room.items.append(item_id)
                item_display = self.format_item(item.name)
                self.send_to_player(player, self.format_success(f"You drop {item_display}."))
                self.broadcast_to_room(player.room_id, f"{player.name} drops {item_display}.", player.name)
                return
                
        self.send_to_player(player, "You don't have that.")
        
    def help_command(self, player, args):
        help_text = f"""
{self.format_header('=== TYRANT OF THE DARK SKIES - COMMAND HELP ===')}

"""
        
        # Show character creation commands if player is in creation
        if hasattr(player, 'creation_state') and player.creation_state != "complete":
            help_text += f"""
{self.format_header('Character Creation Commands:')}
{self.format_command('race')} <name> - Choose your race
{self.format_command('assign')} <attribute> - Assign free attribute points (humans only)
{self.format_command('planet')} <name> - Choose your planet
{self.format_command('starsign')} <name> - Choose your starsign
{self.format_command('maneuver')} <name> - Choose your starting maneuver

"""
        
        help_text += f"""
{self.format_header('Movement & Exploration:')}
{self.format_command('look')} or {self.format_command('l')} - Look around the current room
{self.format_command('look')} <direction> - Look in a specific direction (e.g., 'look north')
{self.format_command('move')} or {self.format_command('go')} <direction> - Move in a direction (north, south, east, west, etc.)
{self.format_command('say')} <message> - Say something to others in the room
{self.format_command('who')} - See who is currently online

{self.format_header('Inventory & Items:')}
{self.format_command('inventory')} or {self.format_command('i')} - Check your inventory
{self.format_command('get')} or {self.format_command('take')} <item> - Pick up an item from the room
{self.format_command('drop')} <item> - Drop an item from your inventory
{self.format_command('use')} <item> - Use a consumable item (potions, etc.)
{self.format_command('equip')} <item> or {self.format_command('equip')} <slot> <item> - Equip a weapon or armor
{self.format_command('unequip')} <slot> - Unequip an item
{self.format_command('wield')} <weapon> - Equip a weapon (alias)
{self.format_command('inspect')} <item> - Inspect an item for detailed stats
{self.format_command('time')} - Check the current in-game time
{self.format_command('talk')} <npc> <keyword> - Talk to an NPC using keywords
{self.format_command('list')} or {self.format_command('shop')} - List items for sale
{self.format_command('buy')} <item> - Buy an item from a merchant
{self.format_command('sell')} <item> - Sell an item to a merchant
{self.format_command('repair')} <item> - Repair a weapon or armor

{self.format_header('Combat:')}
{self.format_command('attack')} <target> - Attack a hostile creature
{self.format_command('join combat')} [target] - Join an active combat
{self.format_command('disengage')} - Attempt to leave combat
{self.format_command('use maneuver')} <name> - Use a maneuver

{self.format_header('Character Information:')}
{self.format_command('stats')} - View your character sheet (attributes, resources, race, planet, starsign)
{self.format_command('skills')} - View all your skills and effective skill levels
{self.format_command('maneuvers')} - View your known maneuvers and available ones to learn
{self.format_command('quests')} - View your active quests
{self.format_command('quest')} <command> - Manage quests (list, accept, complete)

{self.format_header('System:')}
{self.format_command('help')} or {self.format_command('?')} - Show this help message
{self.format_command('quit')} - Leave the game

"""
        
        # Show admin commands if player is admin
        if self.is_admin(player):
            help_text += f"""
{self.format_header('Admin Commands:')}
{self.format_command('create_room')} <room_id> <name> - Create a new room
{self.format_command('edit_room')} <room_id> <field> <value> - Edit room properties
{self.format_command('delete_room')} <room_id> - Delete a room
{self.format_command('list_rooms')} - List all rooms
{self.format_command('goto')} <room_id> - Teleport to a room
{self.format_command('weapons')} - List available weapon templates
{self.format_command('create_weapon')} <template> [modifier] [item_id] - Create a weapon item
{self.format_command('setoutlook')} <npc> <player> <value> - Set NPC outlook
{self.format_command('set_time')} <day> <hour> [minute] - Set world time

"""
        
        help_text += f"""
{self.format_header('Game System Notes:')}
- Skills use a unified {self.format_command('d100')} check system
- Effective skill = base skill + attribute bonuses + difficulty modifiers
- Skills advance through successful use (higher skills are harder to advance)
- Maneuvers are special abilities learned from masters throughout the world
- Your planet, race, and starsign affect your starting attributes and abilities
- Type {self.format_command('look')} to see available exits and items in each room
"""
        
        # Send help text using send_to_player_raw to preserve newlines
        # (send_to_player adds extra newline which we don't want here)
        self.send_to_player_raw(player, help_text)
        
    def who_command(self, player, args):
        """Show online players. Only shows names, never IP addresses or other sensitive data."""
        with self.player_lock:
            online_players = [name for name, p in self.players.items() if p.is_logged_in]
            if online_players:
                self.send_to_player(player, f"Players online: {', '.join(online_players)}")
            else:
                self.send_to_player(player, "No other players are online.")
                
    def attack_command(self, player, args):
        if not args:
            self.send_to_player(player, "Attack whom?")
            return
            
        target_name = " ".join(args).lower()
        room = self.get_room(player.room_id)
        
        if not room:
            return
        
        # Check for player target first (PvP)
        target_player = None
        for pname, p in self.players.items():
            if pname != player.name and pname.lower() == target_name and p.room_id == player.room_id:
                target_player = p
                break
        
        # Check for NPC target
        target_npc = None
        for npc_id in room.npcs:
            npc = self.npcs.get(npc_id)
            if npc and target_name in npc.name.lower():
                # Check hostility - use outlook system if available
                if hasattr(npc, 'outlooks') and player.name in npc.outlooks:
                    outlook = npc.outlooks[player.name]
                    if outlook < -50:  # Hostile threshold
                        target_npc = npc
                        break
                elif npc.is_hostile:
                    target_npc = npc
                    break
                
        if not target_npc and not target_player:
            self.send_to_player(player, "You don't see that target here or it's not hostile.")
            return
        
        # Use combat system if available, otherwise use simple combat
        if self.combat_manager and (target_npc or target_player):
            target = target_npc if target_npc else target_player
            target_display = target_npc.name if target_npc else target_player.name
            
            # Start or join combat
            combat = self.combat_manager.get_combat_state(player.room_id)
            if not combat or not combat.is_active:
                # Start new combat
                self.combat_manager.start_combat(player.room_id, player.name, player, target_display, target)
            elif player.name not in combat.combatants:
                # Join existing combat
                self.combat_manager.join_combat(player.room_id, player.name, player, target_display)
            
            # Process attack through combat system
            result = self.combat_manager.process_turn(player.room_id, player.name, "attack", {"target": target_display})
            if result:
                if result.get("success"):
                    damage = result.get("damage", 0)
                    if damage > 0:
                        if result.get("critical"):
                            self.send_to_player(player, f"You critically strike {target_display} for {damage} damage!")
                        else:
                            self.send_to_player(player, f"You attack {target_display} for {damage} damage!")
                    else:
                        self.send_to_player(player, f"You attack {target_display} but miss!")
                    
                    # Handle defeat and EXP
                    if target_npc and hasattr(target_npc, 'health') and target_npc.health <= 0:
                        # Award EXP
                        if hasattr(target_npc, 'exp_value') and target_npc.exp_value > 0:
                            exp_gain = target_npc.exp_value
                        else:
                            tier_multiplier = {"Low": 1, "Mid": 2, "High": 3, "Epic": 5}.get(target_npc.get_tier(), 1)
                            exp_gain = 25 + (target_npc.max_health // 2) * tier_multiplier
                        
                        player.experience += exp_gain
                        self.send_to_player(player, f"You gain {exp_gain} experience points!")
                        
                        # Handle loot
                        if hasattr(target_npc, 'loot_table') and target_npc.loot_table:
                            for loot_entry in target_npc.loot_table:
                                if isinstance(loot_entry, dict):
                                    chance = loot_entry.get("chance", 100)
                                    if random.randint(1, 100) <= chance:
                                        item_id = loot_entry.get("item")
                                        if item_id:
                                            room.items.append(item_id)
                                            item = self.items.get(item_id)
                                            if item:
                                                self.broadcast_to_room(player.room_id, f"{item.name} drops from {target_npc.name}!")
                                elif isinstance(loot_entry, str):
                                    room.items.append(loot_entry)
                                    item = self.items.get(loot_entry)
                                    if item:
                                        self.broadcast_to_room(player.room_id, f"{item.name} drops from {target_npc.name}!")
                        
                        # Remove NPC
                        room.npcs.remove(target_npc.npc_id)
                        self.check_level_up(player)
                else:
                    self.send_to_player(player, result.get("message", "Attack failed"))
            return
        
        # Fallback to simple combat (if combat manager not available)
        if not target_npc:
            self.send_to_player(player, "You can only attack NPCs in simple combat mode.")
            return
            
        # Get equipped weapon
        equipped_weapon = None
        weapon_item = None
        if "weapon" in player.equipped:
            weapon_id = player.equipped["weapon"]
            weapon_item = self.items.get(weapon_id)
            if weapon_item and weapon_item.is_weapon():
                equipped_weapon = weapon_item
        
        # DEFENSE MODEL: Accuracy (Fighting) vs Dodging contest
        # Attacker rolls Accuracy (Fighting skill)
        accuracy_check = player.roll_skill_check("fighting")
        attacker_effective = accuracy_check.get("effective_skill", 50)
        attacker_roll = accuracy_check.get("roll", random.randint(1, 100))
        
        # Defender rolls Dodging
        if hasattr(target_npc, 'roll_skill_check'):
            dodge_check = target_npc.roll_skill_check("dodging")
            defender_effective = dodge_check.get("effective_skill", 50)
            defender_roll = dodge_check.get("roll", random.randint(1, 100))
        else:
            # NPCs without skill system - use default
            defender_effective = 30  # Default NPC dodge
            defender_roll = random.randint(1, 100)
            dodge_check = {"result": "success", "roll": defender_roll}
        
        # Contest: Attacker's roll must beat defender's roll
        hit = False
        is_critical = False
        is_glancing = False
        
        if attacker_roll <= attacker_effective:
            # Attacker's accuracy succeeds
            if attacker_roll < defender_roll or defender_roll > defender_effective:
                # Hit!
                hit = True
                # Check for critical
                if accuracy_check.get("result") == "critical":
                    is_critical = True
                elif equipped_weapon:
                    crit_roll = random.random()
                    if crit_roll <= equipped_weapon.get_effective_crit_chance():
                        is_critical = True
                
                # Check for glancing hit (defender's dodge was close)
                if defender_roll <= defender_effective and defender_roll >= defender_effective * 0.8:
                    is_glancing = True
        
        if hit:
            # Calculate base damage
            if equipped_weapon:
                # Use weapon damage
                damage_min, damage_max = equipped_weapon.get_effective_damage()
                base_damage = random.randint(damage_min, damage_max)
                
                # Add physical attribute bonus
                base_damage += player.get_attribute_bonus("physical")
                
                # Check for critical (weapon crit chance or skill critical)
                is_critical = False
                if accuracy_check.get("result") == "critical":
                    is_critical = True
                elif equipped_weapon:
                    crit_roll = random.random()
                    if crit_roll <= equipped_weapon.get_effective_crit_chance():
                        is_critical = True
                
                if is_critical:
                    damage = base_damage * 2
                    self.send_to_player(player, f"You critically strike {target_npc.name} for {damage} damage with your {equipped_weapon.name}!")
                elif is_glancing:
                    damage = max(1, base_damage // 2)
                    self.send_to_player(player, f"You land a glancing blow on {target_npc.name} for {damage} damage with your {equipped_weapon.name}!")
                else:
                    damage = base_damage
                    self.send_to_player(player, f"You attack {target_npc.name} for {damage} damage with your {equipped_weapon.name}!")
                
                # ARMOR MITIGATION: Apply Damage Reduction by damage type
                damage_type = equipped_weapon.damage_type
                if hasattr(target_npc, 'equipped') and "armor" in target_npc.equipped:
                    armor_id = target_npc.equipped.get("armor")
                    armor_item = self.items.get(armor_id) if armor_id else None
                    if armor_item and hasattr(armor_item, 'damage_reduction'):
                        dr = armor_item.damage_reduction.get(damage_type, 0)
                        if dr > 0:
                            old_damage = damage
                            damage = max(1, damage - dr)
                            self.send_to_player(player, f"{target_npc.name}'s armor reduces the damage by {old_damage - damage}!")
                
                # Reduce weapon durability
                if equipped_weapon.reduce_durability(1):
                    self.send_to_player(player, f"Your {equipped_weapon.name} breaks!")
                    # Remove from equipped and inventory
                    if "weapon" in player.equipped:
                        del player.equipped["weapon"]
                    if weapon_id in player.inventory:
                        player.inventory.remove(weapon_id)
            else:
                # Unarmed combat
                base_damage = player.get_attribute_bonus("physical") + 3
                damage_type = "bludgeoning"
                if is_critical:
                    damage = base_damage * 2
                    self.send_to_player(player, f"You critically strike {target_npc.name} for {damage} damage (unarmed)!")
                elif is_glancing:
                    damage = max(1, base_damage // 2)
                    self.send_to_player(player, f"You land a glancing blow on {target_npc.name} for {damage} damage (unarmed)!")
                else:
                    damage = base_damage + random.randint(1, 3)
                    self.send_to_player(player, f"You attack {target_npc.name} for {damage} damage (unarmed)!")
                
                # ARMOR MITIGATION for unarmed
                if hasattr(target_npc, 'equipped') and "armor" in target_npc.equipped:
                    armor_id = target_npc.equipped.get("armor")
                    armor_item = self.items.get(armor_id) if armor_id else None
                    if armor_item and hasattr(armor_item, 'damage_reduction'):
                        dr = armor_item.damage_reduction.get(damage_type, 0)
                        if dr > 0:
                            old_damage = damage
                            damage = max(1, damage - dr)
                            self.send_to_player(player, f"{target_npc.name}'s armor reduces the damage by {old_damage - damage}!")
            
            self.broadcast_to_room(player.room_id, 
                                  f"{player.name} attacks {target_npc.name}!", player.name)
            
            target_npc.health -= damage
            target_npc.health = max(0, target_npc.health)
            
            # Track skill use for advancement
            player.check_skill_advancement("fighting", True)
        else:
            # Miss - defender's dodge succeeded
            self.send_to_player(player, f"You attack {target_npc.name} but they dodge out of the way!")
            self.broadcast_to_room(player.room_id, 
                                  f"{player.name} attacks {target_npc.name} but misses!", player.name)
            player.check_skill_advancement("fighting", False)
        
        if target_npc.health <= 0:
            self.send_to_player(player, f"You have slain {target_npc.name}!")
            self.broadcast_to_room(player.room_id, 
                                  f"{player.name} has slain {target_npc.name}!", player.name)
            
            # Use NPC's exp_value if set, otherwise calculate based on tier/level
            if hasattr(target_npc, 'exp_value') and target_npc.exp_value > 0:
                exp_gain = target_npc.exp_value
            else:
                # Calculate based on tier
                tier_multiplier = {"Low": 1, "Mid": 2, "High": 3, "Epic": 5}.get(target_npc.get_tier(), 1)
                exp_gain = 25 + (target_npc.max_health // 2) * tier_multiplier
            
            player.experience += exp_gain
            self.send_to_player(player, f"You gain {exp_gain} experience points!")
            
            # Update quest progress (defeat creature)
            if self.quest_manager:
                completed = self.quest_manager.update_quest_progress(
                    player.name, "defeat_creature", target_npc.npc_id, 1
                )
                for quest in completed:
                    player.experience += quest.exp_reward
                    self.send_to_player(player, f"{self.format_header('Quest Complete!')}")
                    self.send_to_player(player, f"Quest: {quest.name}")
                    self.send_to_player(player, f"You gain {quest.exp_reward} EXP from quest completion!")
                    self.check_level_up(player)
            
            # Roll loot from loot table if available
            if hasattr(target_npc, 'loot_table') and target_npc.loot_table:
                for loot_entry in target_npc.loot_table:
                    if isinstance(loot_entry, dict):
                        # Weighted loot entry
                        chance = loot_entry.get("chance", 100)
                        if random.randint(1, 100) <= chance:
                            item_id = loot_entry.get("item")
                            if item_id:
                                room.items.append(item_id)
                                item = self.items.get(item_id)
                                if item:
                                    self.broadcast_to_room(player.room_id, f"{item.name} drops from {target_npc.name}!")
                    elif isinstance(loot_entry, str):
                        # Simple item ID
                        room.items.append(loot_entry)
                        item = self.items.get(loot_entry)
                        if item:
                            self.broadcast_to_room(player.room_id, f"{item.name} drops from {target_npc.name}!")
            
            # Legacy inventory drop (for backward compatibility)
            if target_npc.inventory:
                for item_id in target_npc.inventory:
                    room.items.append(item_id)
                    item = self.items.get(item_id)
                    if item:
                        self.broadcast_to_room(player.room_id, 
                                              f"{item.name} drops from {target_npc.name}!")
            
            room.npcs.remove(target_npc.npc_id)
            self.check_level_up(player)
        else:
            # NPC counterattack
            if hasattr(target_npc, 'roll_skill_check'):
                npc_check = target_npc.roll_skill_check("fighting")
            else:
                npc_check = {"result": "success", "roll": random.randint(1, 100)}
            
            if npc_check["result"] in ["success", "critical"]:
                base_damage = target_npc.get_attribute_bonus("physical") + 3
                if npc_check["result"] == "critical":
                    counter_damage = base_damage * 2
                else:
                    counter_damage = base_damage + random.randint(1, 4)
                
                player.health -= counter_damage
                player.health = max(0, player.health)
                self.send_to_player(player, f"{target_npc.name} hits you for {counter_damage} damage!")
                
                if player.health <= 0:
                    player.health = 0
                    self.send_to_player(player, "You have been defeated! You respawn at The Black Anchor - Common Room.")
                    self.broadcast_to_room(player.room_id, 
                                          f"{player.name} has been defeated!", player.name)
                    self.respawn_player(player)
            else:
                self.send_to_player(player, f"{target_npc.name} attacks but misses!")
                
    def respawn_player(self, player):
        old_room = self.get_room(player.room_id)
        if old_room:
            old_room.players.discard(player.name)
            
        player.room_id = "black_anchor_common"
        player.health = player.max_health // 2
        
        new_room = self.get_room(player.room_id)
        if new_room:
            new_room.players.add(player.name)
            
            self.send_to_player(player, "You respawn at The Black Anchor - Common Room with half health.")
        if COMMANDS_AVAILABLE:
            look_command(self, player, [])
        else:
            self.look_command(player, [])
        self.broadcast_to_room(player.room_id, f"{player.name} appears, looking wounded.", player.name)
    
    def join_combat_command(self, player, args):
        """Join an existing combat in the room"""
        room = self.get_room(player.room_id)
        if not room:
            return
        
        if not self.combat_manager:
            self.send_to_player(player, "Combat system not available.")
            return
        
        # Check if there's active combat
        combat = self.combat_manager.get_combat_state(player.room_id)
        if not combat or not combat.is_active:
            self.send_to_player(player, "There is no active combat here.")
            return
        
        # Check if already in combat
        if player.name in combat.combatants:
            self.send_to_player(player, "You are already in combat.")
            return
        
        # Join combat
        target_name = args[1] if len(args) > 1 else None
        self.combat_manager.join_combat(player.room_id, player.name, player, target_name)
        self.send_to_player(player, "You join the combat!")
    
    def disengage_command(self, player, args):
        """Attempt to disengage from combat"""
        if not self.combat_manager:
            self.send_to_player(player, "Combat system not available.")
            return
        
        combat = self.combat_manager.get_combat_state(player.room_id)
        if not combat or not combat.is_active:
            self.send_to_player(player, "You are not in combat.")
            return
        
        if player.name not in combat.combatants:
            self.send_to_player(player, "You are not in combat.")
            return
        
        # Attempt disengage
        if self.combat_manager.leave_combat(player.room_id, player.name):
            self.send_to_player(player, "You disengage from combat.")
        else:
            self.send_to_player(player, "You cannot disengage right now.")
    
    def use_maneuver_command(self, player, args):
        """Use a maneuver in combat or out of combat"""
        if not args:
            self.send_to_player(player, "Use which maneuver? Usage: use maneuver <name>")
            return
        
        maneuver_name = " ".join(args).lower()
        maneuver_id = None
        matched_maneuver = None
        
        # First, check if any of the player's known maneuvers match
        for known_id in player.known_maneuvers:
            if known_id in self.maneuvers:
                maneuver = self.maneuvers[known_id]
                maneuver_display_name = maneuver.get('name', '').lower()
                # Check exact match on display name or ID
                if (maneuver_name == maneuver_display_name or 
                    maneuver_name == known_id.lower() or
                    maneuver_name.replace(' ', '_') == known_id.lower()):
                    maneuver_id = known_id
                    matched_maneuver = maneuver
                    break
                # Check partial match
                elif (maneuver_name in maneuver_display_name or 
                      maneuver_name in known_id.lower()):
                    if not maneuver_id:  # Store first partial match
                        maneuver_id = known_id
                        matched_maneuver = maneuver
        
        # If not found in known maneuvers, search all maneuvers (for better error message)
        if not maneuver_id:
            for mid, maneuver in self.maneuvers.items():
                maneuver_display_name = maneuver.get('name', '').lower()
                if (maneuver_name == maneuver_display_name or 
                    maneuver_name == mid.lower() or
                    maneuver_name.replace(' ', '_') == mid.lower() or
                    maneuver_name in maneuver_display_name or 
                    maneuver_name in mid.lower()):
                    maneuver_id = mid
                    matched_maneuver = maneuver
                    break
        
        if not maneuver_id:
            self.send_to_player(player, f"You don't know a maneuver called '{' '.join(args)}'.")
            self.send_to_player(player, f"Use {self.format_command('maneuvers')} to see your known maneuvers.")
            return
        
        if maneuver_id not in player.known_maneuvers:
            self.send_to_player(player, f"You don't know the maneuver '{matched_maneuver.get('name', maneuver_id)}'.")
            self.send_to_player(player, f"Use {self.format_command('maneuvers')} to see your known maneuvers.")
            return
        
        if maneuver_id not in player.active_maneuvers:
            self.send_to_player(player, f"The maneuver '{matched_maneuver.get('name', maneuver_id)}' is not currently active.")
            self.send_to_player(player, f"Use {self.format_command('maneuvers')} to activate it.")
            return
        
        # Check if in combat
        if self.combat_manager:
            combat = self.combat_manager.get_combat_state(player.room_id)
            if combat and combat.is_active and player.name in combat.combatants:
                # Use in combat (would integrate with turn system)
                self.send_to_player(player, f"You prepare to use {maneuver_name}...")
                # Note: Combat maneuver integration pending
            else:
                # Use out of combat
                self.send_to_player(player, f"You use {maneuver_name}.")
                # Note: Maneuver effects implementation pending
        else:
            self.send_to_player(player, f"You use {maneuver_name}.")
            # Note: Maneuver effects implementation pending
    
    def quests_command(self, player, args):
        """Show player's active quests"""
        if not self.quest_manager:
            self.send_to_player(player, "Quest system not available.")
            return
        
        quests = self.quest_manager.get_player_quests(player.name)
        if not quests:
            self.send_to_player(player, "You have no active quests.")
            return
        
        output = f"\n{self.format_header('Active Quests')}\n"
        for quest in quests:
            if quest.completed:
                output += f"{self.format_success(f'[COMPLETE] {quest.name}')}\n"
            else:
                output += f"{self.format_header(quest.name)}\n"
                output += f"{quest.description}\n"
                
                # Show objectives
                if quest.objectives:
                    output += "Objectives:\n"
                    for objective in quest.objectives:
                        obj_id = objective.get("id")
                        required = objective.get("required", 1)
                        current = quest.progress.get(obj_id, 0)
                        obj_desc = objective.get("description", f"Objective {obj_id}")
                        output += f"  - {obj_desc}: {current}/{required}\n"
                output += "\n"
        
        self.send_to_player(player, output)
    
    def quest_command(self, player, args):
        """Quest management commands"""
        if not self.quest_manager:
            self.send_to_player(player, "Quest system not available.")
            return
        
        if not args:
            self.send_to_player(player, "Usage: quest <list|accept|complete> [quest_id]")
            return
        
        subcmd = args[0].lower()
        
        if subcmd == "list":
            # List available quests (would need quest givers/NPCs)
            self.send_to_player(player, "Available quests feature coming soon.")
        elif subcmd == "accept" and len(args) > 1:
            quest_id = args[1]
            if self.quest_manager.assign_quest(player.name, quest_id):
                self.send_to_player(player, f"Quest '{quest_id}' accepted!")
            else:
                self.send_to_player(player, f"Quest '{quest_id}' not found or already accepted.")
        elif subcmd == "complete":
            # Show completed quests
            quests = self.quest_manager.get_player_quests(player.name)
            completed = [q for q in quests if q.completed]
            if completed:
                output = f"\n{self.format_header('Completed Quests')}\n"
                for quest in completed:
                    output += f"- {quest.name}\n"
                self.send_to_player(player, output)
            else:
                self.send_to_player(player, "You have no completed quests.")
    
    def equip_command(self, player, args):
        """Equip a weapon or armor"""
        if not args:
            self.send_to_player(player, "Equip what? Usage: equip <slot> <item> or equip <item>")
            return
        
        # Parse command: "equip weapon longsword" or "equip longsword"
        if len(args) == 1:
            # Assume weapon slot
            item_name = args[0].lower()
            slot = "weapon"
        elif len(args) >= 2:
            slot = args[0].lower()
            item_name = " ".join(args[1:]).lower()
        else:
            self.send_to_player(player, "Equip what? Usage: equip <slot> <item> or equip <item>")
            return
        
        # Find item in inventory
        item_id = None
        item = None
        for inv_item_id in player.inventory:
            inv_item = self.items.get(inv_item_id)
            if inv_item and item_name in inv_item.name.lower():
                item_id = inv_item_id
                item = inv_item
                break
        
        if not item:
            self.send_to_player(player, f"You don't have '{item_name}' in your inventory.")
            return
        
        # Check if item is appropriate for slot
        if slot == "weapon":
            if not item.is_weapon():
                self.send_to_player(player, f"{item.name} is not a weapon.")
                return
            
            # Check hands requirement
            if item.hands == 2:
                # Two-handed weapon - unequip shield/offhand if equipped
                if "offhand" in player.equipped:
                    old_offhand = player.equipped["offhand"]
                    self.send_to_player(player, f"You unequip your {self.items.get(old_offhand, Item('', '', '')).name} to wield {item.name}.")
                    del player.equipped["offhand"]
            
            # Unequip old weapon if any
            if "weapon" in player.equipped:
                old_weapon_id = player.equipped["weapon"]
                old_weapon = self.items.get(old_weapon_id)
                if old_weapon:
                    self.send_to_player(player, f"You unequip your {old_weapon.name}.")
            
            player.equipped["weapon"] = item_id
            self.send_to_player(player, f"You equip {item.name}.")
            
            # Show weapon stats
            damage_min, damage_max = item.get_effective_damage()
            self.send_to_player(player, f"  Damage: {damage_min}-{damage_max} ({item.damage_type})")
            self.send_to_player(player, f"  Critical: {int(item.get_effective_crit_chance() * 100)}%")
            self.send_to_player(player, f"  Durability: {item.get_current_durability()}/{item.max_durability}")
        else:
            self.send_to_player(player, f"Equipping to '{slot}' slot is not yet implemented.")
    
    def unequip_command(self, player, args):
        """Unequip a weapon or armor"""
        if not args:
            self.send_to_player(player, "Unequip what? Usage: unequip <slot>")
            return
        
        slot = args[0].lower()
        
        if slot not in player.equipped:
            self.send_to_player(player, f"You don't have anything equipped in your {slot} slot.")
            return
        
        item_id = player.equipped[slot]
        item = self.items.get(item_id)
        
        if item:
            del player.equipped[slot]
            self.send_to_player(player, f"You unequip your {item.name}.")
        else:
            del player.equipped[slot]
            self.send_to_player(player, f"You unequip your {slot}.")
    
    def list_weapons_command(self, player, args):
        """List available weapon templates (admin command)"""
        if not self.weapons:
            self.send_to_player(player, "No weapon templates loaded.")
            return
        
        output = f"\n{self.format_header('Available Weapon Templates')}\n"
        for weapon_id, weapon in self.weapons.items():
            output += f"\n{self.format_header(weapon['name'])} ({weapon_id})\n"
            output += f"  Category: {weapon['category']} | Class: {weapon['class']}\n"
            output += f"  Damage: {weapon['damage_min']}-{weapon['damage_max']} ({weapon['damage_type']})\n"
            output += f"  Hands: {weapon['hands']} | Range: {weapon['range']}\n"
            output += f"  Crit: {int(weapon['crit_chance'] * 100)}% | Speed: {weapon['speed_cost']}\n"
            output += f"  Durability: {weapon['durability']}\n"
            if 'description' in weapon:
                output += f"  {weapon['description']}\n"
        
        self.send_to_player(player, output)
    
    def create_weapon_command(self, player, args):
        """Create a weapon item from a template (admin command)"""
        if len(args) < 1:
            self.send_to_player(player, "Usage: create_weapon <template_id> [modifier_id] [item_id]")
            return
        
        template_id = args[0].lower()
        modifier_id = args[1].lower() if len(args) > 1 else None
        item_id = args[2].lower() if len(args) > 2 else None
        
        # Create weapon item
        weapon_item = self.create_weapon_item(template_id, modifier_id, item_id)
        
        if not weapon_item:
            self.send_to_player(player, f"Weapon template '{template_id}' not found.")
            return
        
        # Add to player's inventory
        player.inventory.append(weapon_item.item_id)
        self.items[weapon_item.item_id] = weapon_item
        
        # Save items
        self.save_items_to_json()
        
        self.send_to_player(player, f"Created {weapon_item.name} and added to your inventory!")
        if self.logger:
            self.logger.log_admin_action(player.name, "CREATE_WEAPON", f"Template: {template_id}, Modifier: {modifier_id}")
    
    def inspect_command(self, player, args):
        """Inspect an item to see detailed stats"""
        if not args:
            self.send_to_player(player, "Inspect what? Usage: inspect <item>")
            return
        
        item_name = " ".join(args).lower()
        
        # Check inventory first
        item = None
        for item_id in player.inventory:
            inv_item = self.items.get(item_id)
            if inv_item and item_name in inv_item.name.lower():
                item = inv_item
                break
        
        # Check room if not in inventory
        if not item:
            room = self.get_room(player.room_id)
            if room:
                for item_id in room.items:
                    room_item = self.items.get(item_id)
                    if room_item and item_name in room_item.name.lower():
                        item = room_item
                        break
        
        if not item:
            self.send_to_player(player, f"You don't see '{item_name}' here or in your inventory.")
            return
        
        # Show item details
        output = f"\n{self.format_header(item.name)}\n"
        output += f"{item.description}\n"
        output += f"Type: {item.item_type}\n"
        output += f"Value: {item.value} gold\n"
        
        # Show weapon stats if it's a weapon
        if item.is_weapon():
            output += f"\n{self.format_header('Weapon Stats')}\n"
            output += f"Category: {item.category}\n"
            output += f"Class: {item.weapon_class}\n"
            output += f"Hands: {item.hands}\n"
            output += f"Range: {item.range}\n"
            damage_min, damage_max = item.get_effective_damage()
            output += f"Damage: {damage_min}-{damage_max} ({item.damage_type})\n"
            output += f"Critical Chance: {int(item.get_effective_crit_chance() * 100)}%\n"
            output += f"Speed Cost: {item.speed_cost}\n"
            output += f"Durability: {item.get_current_durability()}/{item.max_durability}\n"
            
            if item.weapon_template_id:
                output += f"Template: {item.weapon_template_id}\n"
            if item.weapon_modifier_id:
                modifier = self.weapon_modifiers.get(item.weapon_modifier_id)
                if modifier:
                    output += f"Modifier: {modifier['name']} - {modifier.get('notes', '')}\n"
        
        self.send_to_player(player, output)
    
    def time_command(self, player, args):
        """Display current world time"""
        if not self.world_time:
            self.send_to_player(player, "Time system is not available.")
            return
        
        include_exact = "exact" in args or "precise" in args
        time_string = self.world_time.get_time_string(include_exact=include_exact)
        self.send_to_player(player, time_string)
    
    def set_time_command(self, player, args):
        """Set world time (admin command)"""
        if not self.world_time:
            self.send_to_player(player, "Time system is not available.")
            return
        
        if len(args) < 1:
            self.send_to_player(player, "Usage: set_time <day> <hour> [minute] or set_time <world_seconds>")
            return
        
        try:
            if len(args) == 1:
                # Set by world_seconds
                world_seconds = int(args[0])
                self.world_time.set_world_seconds(world_seconds)
                self.save_world_time()
                self.send_to_player(player, f"World time set to {world_seconds} seconds (Day {self.world_time.get_day_number()}, {self.world_time.get_hour():02d}:{self.world_time.get_minute():02d})")
            else:
                # Set by day, hour, minute
                day = int(args[0])
                hour = int(args[1])
                minute = int(args[2]) if len(args) > 2 else 0
                
                if not (0 <= hour < 24 and 0 <= minute < 60):
                    self.send_to_player(player, "Invalid time. Hour must be 0-23, minute must be 0-59.")
                    return
                
                world_seconds = day * 86400 + hour * 3600 + minute * 60
                self.world_time.set_world_seconds(world_seconds)
                self.save_world_time()
                self.send_to_player(player, f"World time set to Day {day}, {hour:02d}:{minute:02d}")
            
            if self.logger:
                self.logger.log_admin_action(player.name, "SET_TIME", f"Time: {args}")
        except ValueError:
            self.send_to_player(player, "Invalid time format. Use numbers only.")
    
    def get_npc_outlook(self, npc, player_name):
        """Get NPC's outlook toward a player"""
        if not hasattr(npc, 'outlooks'):
            return 0
        return npc.outlooks.get(player_name, 0)
    
    def get_price_modifier(self, outlook):
        """Get price modifier based on outlook"""
        if outlook <= -50:
            return 1.5  # Hostile: +50%
        elif outlook <= -20:
            return 1.3  # Unfriendly: +30%
        elif outlook < 0:
            return 1.1  # Slightly negative: +10%
        elif outlook == 0:
            return 1.0  # Neutral: base price
        elif outlook < 30:
            return 0.85  # Friendly: -15%
        else:
            return 0.70  # Trusted: -30%
    
    def talk_command(self, player, args):
        """Talk to an NPC using keyword-based dialogue"""
        if not args:
            self.send_to_player(player, "Talk to whom? Usage: talk <npc> <keyword>")
            return
        
        # Find NPC in room
        room = self.get_room(player.room_id)
        if not room:
            self.send_to_player(player, "You are in an unknown location.")
            return
        
        # Check for scheduled NPCs
        present_npc_ids = set(room.npcs)
        if self.npc_scheduler:
            scheduled_npcs = self.npc_scheduler.get_present_npcs(room.room_id)
            present_npc_ids.update(scheduled_npcs)
        
        # Find NPC by name
        npc_name = args[0].lower()
        npc = None
        npc_id = None
        
        for nid in present_npc_ids:
            n = self.npcs.get(nid)
            if n and npc_name in n.name.lower():
                npc = n
                npc_id = nid
                break
        
        if not npc:
            self.send_to_player(player, f"You don't see {npc_name} here.")
            return
        
        # Get keyword (rest of args)
        if len(args) < 2:
            # Show greeting/dialogue
            if hasattr(npc, 'dialogue') and npc.dialogue:
                greeting = npc.dialogue[0] if npc.dialogue else f"{npc.name} looks at you expectantly."
                self.send_to_player(player, f"{npc.name} says: \"{greeting}\"")
            else:
                self.send_to_player(player, f"{npc.name} looks at you expectantly.")
            return
        
        keyword = " ".join(args[1:]).lower().strip()
        
        # Check for keyword response
        # Make sure keywords exist and is a dict
        if not hasattr(npc, 'keywords'):
            npc.keywords = {}
        if not isinstance(npc.keywords, dict):
            npc.keywords = {}
        
        if npc.keywords:
            # First try exact match
            matched_key = None
            if keyword in npc.keywords:
                matched_key = keyword
            else:
                # Try to find keyword in the input (e.g., "i would like to buy" contains "buy")
                # Check each keyword to see if it appears in the input
                # Sort by length (longer first) to match multi-word keys before single words
                sorted_keys = sorted(npc.keywords.keys(), key=len, reverse=True)
                for key in sorted_keys:
                    # Check if the key appears in the keyword string
                    if key in keyword:
                        matched_key = key
                        break
            
            if matched_key:
                response = npc.keywords[matched_key]
                self.send_to_player(player, f"{npc.name} says: \"{response}\"")
                self.broadcast_to_room(player.room_id, f"{player.name} talks with {npc.name}.", player.name)
                
                # Special handling for certain keywords
                if hasattr(npc, 'is_merchant') and npc.is_merchant:
                    if matched_key in ["goods", "buy", "shop"]:
                        self.send_to_player(player, f"\n{self.format_header('Shop Interface')}")
                        self.send_to_player(player, f"Use {self.format_command('list')} or {self.format_command('shop')} to see available items.")
                        self.send_to_player(player, f"Use {self.format_command('buy <item>')} to purchase items.")
                    elif matched_key == "sell":
                        self.send_to_player(player, f"\n{self.format_header('Selling Items')}")
                        self.send_to_player(player, f"Use {self.format_command('sell <item>')} to sell items from your inventory.")
                        self.send_to_player(player, f"I'll give you a fair price based on the item's value and our relationship.")
                    elif matched_key in ["repair", "repairs"]:
                        self.send_to_player(player, f"\n{self.format_header('Repair Service')}")
                        self.send_to_player(player, f"Use {self.format_command('repair <item>')} to repair weapons or armor.")
                        self.send_to_player(player, f"Cost depends on the damage. I can fix most basic gear.")
                
                return
        
        # No keyword match
        self.send_to_player(player, f"{npc.name} doesn't seem to respond to that.")
    
    def shop_list_command(self, player, args):
        """List items available in shop"""
        room = self.get_room(player.room_id)
        if not room:
            self.send_to_player(player, "You are in an unknown location.")
            return
        
        # Find merchant NPC
        present_npc_ids = set(room.npcs)
        if self.npc_scheduler:
            scheduled_npcs = self.npc_scheduler.get_present_npcs(room.room_id)
            present_npc_ids.update(scheduled_npcs)
        
        merchant = None
        for nid in present_npc_ids:
            n = self.npcs.get(nid)
            if n:
                # Check if merchant (either has is_merchant flag or has shop_inventory)
                # Also check if room has "shop" flag as fallback
                is_merchant = getattr(n, 'is_merchant', False)
                shop_inventory = getattr(n, 'shop_inventory', None)
                has_shop_inventory = shop_inventory is not None and len(shop_inventory) > 0
                room_is_shop = room.flags and "shop" in room.flags
                
                if is_merchant or has_shop_inventory or (room_is_shop and n.name.lower() == "jalia"):
                    merchant = n
                    break
        
        if not merchant:
            self.send_to_player(player, "There's no merchant here.")
            return
        
        # Check store hours
        if self.store_hours and room.room_id in self.store_hours.store_hours:
            if not self.store_hours.is_store_open(room.room_id):
                status = self.store_hours.get_store_status(room.room_id)
                self.send_to_player(player, f"The shop is {status.lower()}.")
                return
        
        # Get shop inventory
        shop_inventory = getattr(merchant, 'shop_inventory', [])
        if not shop_inventory:
            self.send_to_player(player, f"{merchant.name} has nothing for sale right now.")
            return
        
        # Get player's outlook with merchant
        outlook = self.get_npc_outlook(merchant, player.name)
        price_mod = self.get_price_modifier(outlook)
        
        header_text = f"{merchant.name}'s Goods"
        output = f"\n{self.format_header(header_text)}\n"
        output += f"Outlook: {outlook} ({'Hostile' if outlook <= -50 else 'Unfriendly' if outlook <= -20 else 'Neutral' if outlook == 0 else 'Friendly' if outlook < 30 else 'Trusted'})\n\n"
        
        # Load shop items (from individual files or consolidated file)
        shop_items_data = self.load_shop_items()
        
        # Group items by category
        weapons = []
        armor = []
        tools = []
        consumables = []
        
        for item_id in shop_inventory:
            item_data = shop_items_data.get(item_id)
            if not item_data:
                # Try to get from regular items
                item = self.items.get(item_id)
                if item:
                    item_data = item.to_dict()
            
            if item_data:
                item_type = item_data.get("item_type", "item")
                base_price = item_data.get("value", 0)
                final_price = int(base_price * price_mod)
                
                item_entry = {
                    "id": item_id,
                    "name": item_data.get("name", item_id),
                    "price": final_price,
                    "base_price": base_price
                }
                
                if item_type == "weapon":
                    weapons.append(item_entry)
                elif item_type == "armor":
                    armor.append(item_entry)
                elif item_type == "consumable":
                    consumables.append(item_entry)
                else:
                    tools.append(item_entry)
        
        if weapons:
            output += f"{self.format_header('Weapons:')}\n"
            for item in weapons:
                price_note = f" (was {item['base_price']})" if price_mod != 1.0 else ""
                output += f"  {item['name']} - {item['price']} coin{price_note}\n"
            output += "\n"
        
        if armor:
            output += f"{self.format_header('Armor & Gear:')}\n"
            for item in armor:
                price_note = f" (was {item['base_price']})" if price_mod != 1.0 else ""
                output += f"  {item['name']} - {item['price']} coin{price_note}\n"
            output += "\n"
        
        if tools:
            output += f"{self.format_header('Tools & Supplies:')}\n"
            for item in tools:
                price_note = f" (was {item['base_price']})" if price_mod != 1.0 else ""
                output += f"  {item['name']} - {item['price']} coin{price_note}\n"
            output += "\n"
        
        if consumables:
            output += f"{self.format_header('Consumables:')}\n"
            for item in consumables:
                price_note = f" (was {item['base_price']})" if price_mod != 1.0 else ""
                output += f"  {item['name']} - {item['price']} coin{price_note}\n"
            output += "\n"
        
        output += f"Use {self.format_command('buy <item>')} to purchase.\n"
        output += f"Use {self.format_command('sell <item>')} to sell your items.\n"
        
        self.send_to_player(player, output)
    
    def buy_command(self, player, args):
        """Buy an item from a merchant"""
        if not args:
            self.send_to_player(player, "Buy what? Usage: buy <item>")
            return
        
        room = self.get_room(player.room_id)
        if not room:
            self.send_to_player(player, "You are in an unknown location.")
            return
        
        # Find merchant NPC
        present_npc_ids = set(room.npcs)
        if self.npc_scheduler:
            scheduled_npcs = self.npc_scheduler.get_present_npcs(room.room_id)
            present_npc_ids.update(scheduled_npcs)
        
        merchant = None
        for nid in present_npc_ids:
            n = self.npcs.get(nid)
            if n:
                # Check if merchant (either has is_merchant flag or has shop_inventory)
                # Also check if room has "shop" flag as fallback
                is_merchant = getattr(n, 'is_merchant', False)
                shop_inventory = getattr(n, 'shop_inventory', None)
                has_shop_inventory = shop_inventory is not None and len(shop_inventory) > 0
                room_is_shop = room.flags and "shop" in room.flags
                
                if is_merchant or has_shop_inventory or (room_is_shop and n.name.lower() == "jalia"):
                    merchant = n
                    break
        
        if not merchant:
            self.send_to_player(player, "There's no merchant here.")
            return
        
        # Check store hours
        if self.store_hours and room.room_id in self.store_hours.store_hours:
            if not self.store_hours.is_store_open(room.room_id):
                status = self.store_hours.get_store_status(room.room_id)
                self.send_to_player(player, f"The shop is {status.lower()}.")
                return
        
        # Check outlook - refuse service if very hostile
        outlook = self.get_npc_outlook(merchant, player.name)
        if outlook <= -50:
            self.send_to_player(player, f"{merchant.name} refuses to serve you. Your reputation here is too low.")
            return
        
        # Find item in shop inventory
        item_name = " ".join(args).lower()
        shop_inventory = getattr(merchant, 'shop_inventory', [])
        
        if not shop_inventory:
            self.send_to_player(player, f"{merchant.name} has nothing for sale right now.")
            return
        
        # Load shop items (from individual files or consolidated file)
        shop_items_data = self.load_shop_items()
        
        item_id = None
        item_data = None
        
        # Try exact match first (item_id)
        if item_name in shop_inventory:
            item_id = item_name
            item_data = shop_items_data.get(item_id)
            if not item_data:
                item = self.items.get(item_id)
                if item:
                    item_data = item.to_dict()
        
        # If no exact match, try name matching
        if not item_id or not item_data:
            for sid in shop_inventory:
                data = shop_items_data.get(sid)
                if not data:
                    item = self.items.get(sid)
                    if item:
                        data = item.to_dict()
                
                if data:
                    item_name_lower = data.get("name", "").lower()
                    # Check if user input matches item name (partial or full)
                    if item_name in item_name_lower or item_name_lower.startswith(item_name):
                        item_id = sid
                        item_data = data
                        break
        
        if not item_id or not item_data:
            # Provide helpful error message
            available_items = []
            for sid in shop_inventory:
                data = shop_items_data.get(sid)
                if not data:
                    item = self.items.get(sid)
                    if item:
                        data = item.to_dict()
                if data:
                    available_items.append(data.get("name", sid))
            
            if available_items:
                self.send_to_player(player, f"{merchant.name} doesn't have '{item_name}'. Available items: {', '.join(available_items)}")
            else:
                self.send_to_player(player, f"{merchant.name} doesn't have that item. Use {self.format_command('list')} or {self.format_command('shop')} to see available items.")
            return
        
        # Calculate price
        base_price = item_data.get("value", 0)
        if base_price == 0:
            # Try to get price from item if value not set
            item_obj = self.items.get(item_id)
            if item_obj:
                base_price = getattr(item_obj, 'value', 0)
        
        if base_price == 0:
            self.send_to_player(player, f"Error: {item_data.get('name', 'Item')} has no price set.")
            return
            
        price_mod = self.get_price_modifier(outlook)
        final_price = int(base_price * price_mod)
        
        # Check if player has enough gold
        if player.gold < final_price:
            self.send_to_player(player, f"You need {final_price} coin to buy {item_data.get('name')}, but you only have {player.gold} coin.")
            return
        
        # Create item
        item = Item(item_data.get("item_id"), item_data.get("name"), item_data.get("description", ""), item_data.get("item_type", "item"))
        item.from_dict(item_data)
        
        # If it's a weapon, create from template
        if item_data.get("weapon_template_id") and self.weapons:
            template_id = item_data.get("weapon_template_id")
            modifier_id = item_data.get("weapon_modifier_id")
            created_item = self.create_weapon_item(template_id, modifier_id, item_id)
            if created_item:
                item = created_item
                item.value = final_price  # Set value to final price
        
        # Add to player inventory
        player.inventory.append(item.item_id)
        self.items[item.item_id] = item
        player.gold -= final_price
        
        # Improve outlook slightly for purchase
        if not hasattr(merchant, 'outlooks'):
            merchant.outlooks = {}
        merchant.outlooks[player.name] = merchant.outlooks.get(player.name, 0) + 1
        
        self.send_to_player(player, f"You buy {item.name} for {final_price} coin from {merchant.name}.")
        self.broadcast_to_room(player.room_id, f"{player.name} buys something from {merchant.name}.", player.name)
        
        # Save world data
        self.save_world_data()
    
    def sell_command(self, player, args):
        """Sell an item to a merchant"""
        if not args:
            self.send_to_player(player, "Sell what? Usage: sell <item>")
            return
        
        room = self.get_room(player.room_id)
        if not room:
            self.send_to_player(player, "You are in an unknown location.")
            return
        
        # Find merchant NPC
        present_npc_ids = set(room.npcs)
        if self.npc_scheduler:
            scheduled_npcs = self.npc_scheduler.get_present_npcs(room.room_id)
            present_npc_ids.update(scheduled_npcs)
        
        merchant = None
        for nid in present_npc_ids:
            n = self.npcs.get(nid)
            if n:
                # Check if merchant (either has is_merchant flag or has shop_inventory)
                # Also check if room has "shop" flag as fallback
                is_merchant = getattr(n, 'is_merchant', False)
                shop_inventory = getattr(n, 'shop_inventory', None)
                has_shop_inventory = shop_inventory is not None and len(shop_inventory) > 0
                room_is_shop = room.flags and "shop" in room.flags
                
                if is_merchant or has_shop_inventory or (room_is_shop and n.name.lower() == "jalia"):
                    merchant = n
                    break
        
        if not merchant:
            self.send_to_player(player, "There's no merchant here.")
            return
        
        # Check store hours
        if self.store_hours and room.room_id in self.store_hours.store_hours:
            if not self.store_hours.is_store_open(room.room_id):
                status = self.store_hours.get_store_status(room.room_id)
                self.send_to_player(player, f"The shop is {status.lower()}.")
                return
        
        # Find item in player inventory
        item_name = " ".join(args).lower()
        item_id = None
        item = None
        
        for iid in player.inventory:
            i = self.items.get(iid)
            if i and item_name in i.name.lower():
                item_id = iid
                item = i
                break
        
        if not item:
            self.send_to_player(player, "You don't have that item.")
            return
        
        # Calculate sell price (typically 50% of base value, modified by outlook)
        base_value = item.value if item.value > 0 else 10
        sell_price = int(base_value * 0.5)  # 50% of value
        
        # Apply outlook modifier
        outlook = self.get_npc_outlook(merchant, player.name)
        if outlook > 30:
            sell_price = int(sell_price * 1.1)  # Trusted: +10% sell price
        elif outlook > 0:
            sell_price = int(sell_price * 1.05)  # Friendly: +5% sell price
        
        # Remove from inventory
        player.inventory.remove(item_id)
        player.gold += sell_price
        
        # Improve outlook slightly
        if not hasattr(merchant, 'outlooks'):
            merchant.outlooks = {}
        merchant.outlooks[player.name] = merchant.outlooks.get(player.name, 0) + 1
        
        self.send_to_player(player, f"You sell {item.name} to {merchant.name} for {sell_price} coin.")
        self.broadcast_to_room(player.room_id, f"{player.name} sells something to {merchant.name}.", player.name)
        
        # Save world data
        self.save_world_data()
    
    def repair_command(self, player, args):
        """Repair a weapon or armor"""
        if not args:
            self.send_to_player(player, "Repair what? Usage: repair <item>")
            return
        
        room = self.get_room(player.room_id)
        if not room:
            self.send_to_player(player, "You are in an unknown location.")
            return
        
        # Find merchant NPC with repair service
        present_npc_ids = set(room.npcs)
        if self.npc_scheduler:
            scheduled_npcs = self.npc_scheduler.get_present_npcs(room.room_id)
            present_npc_ids.update(scheduled_npcs)
        
        merchant = None
        for nid in present_npc_ids:
            n = self.npcs.get(nid)
            if n and hasattr(n, 'is_merchant') and n.is_merchant:
                # Check if they have repair keyword
                if hasattr(n, 'keywords') and n.keywords and "repairs" in n.keywords:
                    merchant = n
                    break
        
        if not merchant:
            self.send_to_player(player, "There's no one here who can repair items.")
            return
        
        # Find item in player inventory
        item_name = " ".join(args).lower()
        item_id = None
        item = None
        
        for iid in player.inventory:
            i = self.items.get(iid)
            if i and item_name in i.name.lower():
                item_id = iid
                item = i
                break
        
        if not item:
            self.send_to_player(player, "You don't have that item.")
            return
        
        # Check if item is repairable (weapon or armor)
        if not (item.is_weapon() or item.is_armor()):
            self.send_to_player(player, f"{item.name} cannot be repaired.")
            return
        
        # Calculate repair cost based on damage
        if item.is_weapon():
            current_dur = item.get_current_durability()
            max_dur = item.max_durability
            damage = max_dur - current_dur
            if damage == 0:
                self.send_to_player(player, f"{item.name} is already at full durability.")
                return
            repair_cost = 10 + (damage * 2)  # 10-25 coin range
        else:  # armor
            # For armor, assume similar durability system
            if hasattr(item, 'current_durability') and item.current_durability:
                current_dur = item.current_durability
                max_dur = getattr(item, 'max_durability', 50)
            else:
                # Assume full if no durability system
                self.send_to_player(player, f"{item.name} doesn't need repair.")
                return
            damage = max_dur - current_dur
            if damage == 0:
                self.send_to_player(player, f"{item.name} is already at full durability.")
                return
            repair_cost = 15 + (damage * 3)  # 15-30 coin range
        
        # Apply outlook modifier
        outlook = self.get_npc_outlook(merchant, player.name)
        price_mod = self.get_price_modifier(outlook)
        final_cost = int(repair_cost * price_mod)
        
        # Check if player has enough gold
        if player.gold < final_cost:
            self.send_to_player(player, f"Repair costs {final_cost} coin, but you only have {player.gold} coin.")
            return
        
        # Perform repair
        if item.is_weapon():
            item.current_durability = item.max_durability
        else:
            item.current_durability = getattr(item, 'max_durability', 50)
        
        player.gold -= final_cost
        
        # Improve outlook slightly
        if not hasattr(merchant, 'outlooks'):
            merchant.outlooks = {}
        merchant.outlooks[player.name] = merchant.outlooks.get(player.name, 0) + 1
        
        self.send_to_player(player, f"{merchant.name} repairs your {item.name} for {final_cost} coin.")
        self.broadcast_to_room(player.room_id, f"{player.name} has {item.name} repaired by {merchant.name}.", player.name)
        
        # Save world data
        self.save_world_data()
    
    def save_items_to_json(self):
        """Save items to Firebase"""
        try:
            if self.use_firebase and self.firebase:
                items_dict = {item.item_id: item.to_dict() for item in self.items.values()}
                self.firebase.batch_save_items(items_dict)
                print(f"Saved {len(self.items)} items to Firebase")
            else:
                print("Warning: Firebase not available, cannot save items")
        except Exception as e:
            print(f"Error saving items: {e}")
        
    def check_level_up(self, player):
        """Check and handle level up with proper milestone rewards"""
        exp_needed = player.level * 100
        if player.experience >= exp_needed:
            old_level = player.level
            player.level += 1
            player.experience -= exp_needed
            
            # Base stat increases
            player.max_health += 10
            player.health = player.max_health
            player.max_mana += 5
            player.mana = player.max_mana
            player.max_stamina += 5
            player.stamina = player.max_stamina
            
            # Update max maneuvers based on tier
            player.max_maneuvers = player.get_max_maneuvers()
            
            self.send_to_player(player, f"\n*** LEVEL UP! You are now level {player.level}! ***")
            self.send_to_player(player, f"Health increased to {player.max_health}")
            self.send_to_player(player, f"Mana increased to {player.max_mana}")
            self.send_to_player(player, f"Stamina increased to {player.max_stamina}")
            
            # Attribute point every 3 levels (3, 6, 9, 12, 15, 18)
            if player.level in [3, 6, 9, 12, 15, 18]:
                player.free_attribute_points += 1
                self.send_to_player(player, f"{self.format_header('Attribute Point Gained!')}")
                self.send_to_player(player, f"You have {player.free_attribute_points} free attribute point(s) to allocate.")
                self.send_to_player(player, f"Use {self.format_command('assign <attribute>')} to add a point to an attribute.")
                self.send_to_player(player, f"Available attributes: physical, mental, spiritual, social")
            
            # Non-Learned maneuver every 5 levels (5, 10, 15, 20)
            if player.level in [5, 10, 15, 20]:
                self.send_to_player(player, f"{self.format_header('Maneuver Gained!')}")
                self.send_to_player(player, f"You have gained a non-Learned maneuver!")
                
                # Find available non-Learned maneuvers
                available_maneuvers = []
                player_tier = player.get_tier()
                
                for maneuver_id, maneuver in self.maneuvers.items():
                    # Check if it's Learned (must be taught)
                    is_learned = maneuver.get("traits", [])
                    if isinstance(is_learned, list) and "Learned" in is_learned:
                        continue
                    
                    # Check tier requirement
                    required_tier = maneuver.get("required_tier", "Lower")
                    tier_order = {"Lower": 0, "Low": 1, "Mid": 2, "High": 3, "Epic": 4}
                    if tier_order.get(required_tier, 0) > tier_order.get(player_tier, 0):
                        continue
                    
                    # Check level requirement
                    required_level = maneuver.get("required_level", 1)
                    if required_level > player.level:
                        continue
                    
                    # Check if already known
                    if maneuver_id in player.known_maneuvers:
                        continue
                    
                    # Check race requirement
                    required_race = maneuver.get("required_race")
                    if required_race and player.race != required_race:
                        continue
                    
                    # Check skill requirements
                    required_skills = maneuver.get("required_skills", {})
                    meets_skills = True
                    for skill, level in required_skills.items():
                        if player.skills.get(skill, 1) < level:
                            meets_skills = False
                            break
                    if not meets_skills:
                        continue
                    
                    available_maneuvers.append((maneuver_id, maneuver))
                
                if available_maneuvers:
                    # Show available options
                    self.send_to_player(player, f"\nAvailable non-Learned maneuvers:")
                    for maneuver_id, maneuver in available_maneuvers[:10]:  # Limit to 10 for display
                        maneuver_name = maneuver.get('name', maneuver_id)
                        self.send_to_player(player, f"  - {maneuver_id}: {maneuver_name}")
                    
                    # Auto-select first available (or could prompt player)
                    if available_maneuvers:
                        selected_id, selected_maneuver = available_maneuvers[0]
                        player.known_maneuvers.append(selected_id)
                        if len(player.active_maneuvers) < player.max_maneuvers:
                            player.active_maneuvers.append(selected_id)
                        maneuver_display_name = selected_maneuver.get("name", selected_id)
                        self.send_to_player(player, f"\n{self.format_success(f'You automatically learn: {maneuver_display_name}')}")
                        self.send_to_player(player, f"Use {self.format_command('maneuvers')} to see all your maneuvers.")
                else:
                    self.send_to_player(player, "No non-Learned maneuvers available at this tier. You'll gain one when you meet the requirements.")
            
            # Tier transition messages
            if old_level < 6 and player.level >= 6:
                self.send_to_player(player, f"{self.format_header('TIER TRANSITION: Mid Tier')}")
                self.send_to_player(player, "You have entered Mid Tier! New regions, masters, and threats await.")
            elif old_level < 11 and player.level >= 11:
                self.send_to_player(player, f"{self.format_header('TIER TRANSITION: High Tier')}")
                self.send_to_player(player, "You have entered High Tier! Mastery and influence await.")
            elif old_level < 16 and player.level >= 16:
                self.send_to_player(player, f"{self.format_header('TIER TRANSITION: Epic Tier')}")
                self.send_to_player(player, "You have entered Epic Tier! Myth and world impact await.")
            
            self.save_player_data(player)
            
    def stats_command(self, player, args):
        # Safely get race name
        if player.race and player.race in self.races:
            race_name = self.races[player.race].get('name', player.race.title())
        else:
            race_name = player.race.title() if player.race else "Unknown"
        
        # Safely get planet name (handle missing/corrupted data)
        if player.planet:
            if player.planet in self.planets:
                planet_name = self.planets[player.planet].get('name', player.planet.title())
            else:
                # Planet ID doesn't exist - might be corrupted data
                planet_name = f"{player.planet.title()} (Invalid)"
        else:
            planet_name = "Unknown"
        
        # Safely get starsign name
        if player.starsign and player.starsign in self.starsigns:
            starsign_name = self.starsigns[player.starsign].get('name', player.starsign.title())
        else:
            starsign_name = player.starsign.title() if player.starsign else "Unknown"
        
        # Get equipped weapon info
        equipped_weapon = None
        if "weapon" in player.equipped:
            weapon_id = player.equipped["weapon"]
            equipped_weapon = self.items.get(weapon_id)
        
        # Get race cultural traits
        race_traits = ""
        if player.race and player.race in self.races and "cultural_traits" in self.races[player.race]:
            race_traits = ", ".join(self.races[player.race]["cultural_traits"])
            
        # Get planet theme
        planet_theme = ""
        if player.planet and player.planet in self.planets and "theme" in self.planets[player.planet]:
            planet_theme = self.planets[player.planet]["theme"]
            
        # Get starsign theme
        starsign_theme = ""
        if player.starsign and player.starsign in self.starsigns and "theme" in self.starsigns[player.starsign]:
            starsign_theme = self.starsigns[player.starsign]["theme"]
            
        # Get fated mark description
        fated_mark_desc = ""
        if player.starsign and player.starsign in self.starsigns and "fated_mark" in self.starsigns[player.starsign]:
            fated_mark = self.starsigns[player.starsign]["fated_mark"]
            if "description" in fated_mark:
                fated_mark_desc = fated_mark["description"]
        
        stats_text = f"""
{self.format_header(player.name + "'s Character Sheet")}
Tier: {player.get_tier()} (Level {player.level})
Experience: {player.experience}/{player.level * 100}
Race: {race_name}
Planet: {planet_name}
Starsign: {starsign_name}

Resources:
  Health: {player.health}/{player.max_health}
  Mana: {player.mana}/{player.max_mana}
  Stamina: {player.stamina}/{player.max_stamina}
  Gold: {player.gold}

Attributes:
  Physical: {player.attributes['physical']} (Bonus: {player.get_attribute_bonus('physical')})
  Mental: {player.attributes['mental']} (Bonus: {player.get_attribute_bonus('mental')})
  Spiritual: {player.attributes['spiritual']} (Bonus: {player.get_attribute_bonus('spiritual')})
  Social: {player.attributes['social']} (Bonus: {player.get_attribute_bonus('social')})

Maneuvers: {len(player.active_maneuvers)}/{player.get_max_maneuvers()} active"""
        
        # Add detailed information
        if race_traits:
            stats_text += f"\nCultural Traits: {race_traits}"
        if planet_theme:
            stats_text += f"\nPlanet Theme: {planet_theme}"
        if starsign_theme:
            stats_text += f"\nStarsign Theme: {starsign_theme}"
        if fated_mark_desc:
            stats_text += f"\n{self.format_header('Fated Mark:')}"
            stats_text += f"{fated_mark_desc}"
            
        self.send_to_player(player, stats_text)
        
    def use_command(self, player, args):
        if not args:
            self.send_to_player(player, "Use what?")
            return
        
        # If first arg is "maneuver", this shouldn't have been called - but handle it gracefully
        if args and args[0].lower() == "maneuver":
            self.use_maneuver_command(player, args[1:])
            return
            
        item_name = " ".join(args).lower()
        
        # Check if it's a maneuver name first
        for maneuver_id, maneuver in self.maneuvers.items():
            if item_name in maneuver.get('name', '').lower() or item_name in maneuver_id.lower():
                self.send_to_player(player, f"To use a maneuver, type: {self.format_command('use maneuver')} {maneuver['name']}")
                if maneuver_id not in player.known_maneuvers:
                    self.send_to_player(player, f"You don't know {maneuver['name']} yet. Maneuvers must be learned from masters throughout the world.")
                return
        
        for item_id in player.inventory[:]:
            item = self.items.get(item_id)
            if item and item_name in item.name.lower():
                if item.item_type == "consumable":
                    if item.item_id == "potion":
                        heal_amount = 30
                        player.health = min(player.max_health, player.health + heal_amount)
                        player.inventory.remove(item_id)
                        self.send_to_player(player, f"You drink the potion and heal {heal_amount} health.")
                        self.broadcast_to_room(player.room_id, 
                                              f"{player.name} drinks a health potion.", player.name)
                        return
                else:
                    self.send_to_player(player, "You can't use that item.")
                    return
                    
        self.send_to_player(player, "You don't have that.")
        
    def is_admin(self, player):
        """Check if player is an admin with valid password"""
        if not player or not hasattr(player, 'name'):
            return False
        
        # Check if player is in admin config
        if player.name not in self.admin_config.get("admins", {}):
            return False
        
        # Admin status is determined by admin_config
        # Firebase custom claims are set on login for verification
        return True
        
    def character_creation_welcome(self, player):
        """Start character creation process for new players"""
        self.send_to_player(player, f"""
{self.format_header('=== CHARACTER CREATION ===')}
Welcome to Tyrant of the Dark Skies!

Type {self.format_command('help')} at any time to see available commands.

First, choose your race (affects attributes and starting skills):

""")
        for race_id, race in self.races.items():
            # Use color-coded brackets for supported terminals, plain text for compatibility
            if 'color' in race:
                race_display = f"{self.format_brackets(race_id.upper(), race['color'])}: {race['description']}"
            else:
                race_display = f"[{race_id.upper()}]: {race['description']}"
            self.send_to_player(player, race_display)
            
        self.send_to_player(player, f"\nType {self.format_command('race <name>')} to choose your race.")
        player.creation_state = "choosing_race"
        
    def handle_race_choice(self, player, race_name):
        """Handle race selection during character creation"""
        race_name = race_name.lower()
        if race_name not in self.races:
            available_races = ", ".join([self.format_brackets(r.upper(), self.races[r]['color']) for r in self.races.keys()])
            self.send_to_player(player, f"Unknown race. Choose from: {available_races}")
            return
            
        player.race = race_name
        race = self.races[race_name]
        
        # Apply racial attribute modifiers
        for attr, modifier in race["attribute_modifiers"].items():
            player.attributes[attr] = 10 + modifier
            
        # Apply free points for humans
        player.free_attribute_points = race.get("free_points", 0)
        
        # Apply racial starting skills
        for skill, value in race["starting_skills"].items():
            if skill in player.skills:
                player.skills[skill] = max(player.skills[skill], value)
        
        # Flow: Race -> (if human, assign points) -> Planet -> Starsign -> Maneuver
        if player.free_attribute_points > 0:
            # Human with free points - need to assign them first
            self.send_to_player(player, f"\n{self.format_header('Assign Attribute Points:')}")
            self.send_to_player(player, f"You have {player.free_attribute_points} free attribute points to assign.")
            self.send_to_player(player, f"Current attributes: {player.attributes}")
            self.send_to_player(player, f"Type {self.format_command('assign <attribute>')} to add a point to an attribute.")
            self.send_to_player(player, f"Available attributes: physical, mental, spiritual, social")
            player.creation_state = "assigning_points"
        else:
            # Non-human or no free points - go straight to planet selection
            self.show_planet_selection(player)
        
    def handle_attribute_assignment(self, player, attribute_name):
        """Handle attribute point assignment during character creation"""
        attribute_name = attribute_name.lower()
        valid_attributes = ["physical", "mental", "spiritual", "social"]
        
        if attribute_name not in valid_attributes:
            self.send_to_player(player, f"Invalid attribute. Choose from: {', '.join(valid_attributes)}")
            return
        
        if player.free_attribute_points <= 0:
            self.send_to_player(player, "You have no free points remaining.")
            return
        
        # Add point to attribute
        player.attributes[attribute_name] += 1
        player.free_attribute_points -= 1
        
        self.send_to_player(player, f"Added 1 point to {attribute_name}. New value: {player.attributes[attribute_name]}")
        self.send_to_player(player, f"Remaining free points: {player.free_attribute_points}")
        
        if player.free_attribute_points > 0:
            self.send_to_player(player, f"Type {self.format_command('assign <attribute>')} to assign another point.")
        else:
            self.send_to_player(player, f"\nAll points assigned! Moving to planet selection...")
            self.show_planet_selection(player)
            player.creation_state = "choosing_planet"
    
    def handle_starsign_choice(self, player, starsign_name):
        """Handle starsign selection during character creation"""
        starsign_name = starsign_name.lower()
        if starsign_name not in self.starsigns:
            available_starsigns = ", ".join([self.format_brackets(s.upper(), self.starsigns[s]['color']) for s in self.starsigns.keys()])
            self.send_to_player(player, f"Unknown starsign. Choose from: {available_starsigns}")
            return
            
        player.starsign = starsign_name
        starsign = self.starsigns[starsign_name]
        
        # Apply starsign attribute modifiers
        for attr, modifier in starsign["attribute_modifiers"].items():
            player.attributes[attr] += modifier
            
        # Store fated mark
        player.fated_mark = starsign.get("fated_mark", {})
        
        self.send_to_player(player, f"\nYou chose {self.format_header(starsign['name'])}!")
        self.send_to_player(player, f"Theme: {starsign['theme']}")
        self.send_to_player(player, f"Attribute modifiers: {starsign['attribute_modifiers']}")
        
        if "fated_mark" in starsign:
            fated_mark_desc = starsign["fated_mark"]["description"]
            self.send_to_player(player, f"\n{self.format_header('Fated Mark:')}")
            self.send_to_player(player, f"{fated_mark_desc}")
        
        # Flow: Starsign -> Maneuver
        self.show_starting_maneuvers(player)
        player.creation_state = "choosing_maneuver"
    
    def handle_planet_choice(self, player, planet_name):
        """Handle planet selection during character creation"""
        planet_name = planet_name.lower()
        if planet_name not in self.planets:
            available_planets = ", ".join([self.format_brackets(p.upper(), self.planets[p].get('color', 'cyan')) for p in self.planets.keys()])
            self.send_to_player(player, f"Unknown planet. Choose from: {available_planets}")
            return
            
        player.planet = planet_name
        planet = self.planets[planet_name]
        
        # Apply planet attribute bonuses
        if "attribute_bonuses" in planet:
            for attr, bonus in planet["attribute_bonuses"].items():
                player.attributes[attr] += bonus
        
        # Apply planet starting skills
        if "starting_skills" in planet:
            for skill, value in planet["starting_skills"].items():
                if skill in player.skills:
                    player.skills[skill] = max(player.skills[skill], value)
                else:
                    player.skills[skill] = value
        
        # Store gift maneuver
        if "gift_maneuver" in planet:
            player.gift_maneuver = planet["gift_maneuver"]
            # Add gift maneuver to known maneuvers
            if player.gift_maneuver not in player.known_maneuvers:
                player.known_maneuvers.append(player.gift_maneuver)
            if player.gift_maneuver not in player.active_maneuvers:
                player.active_maneuvers.append(player.gift_maneuver)
        
        self.send_to_player(player, f"\nYou chose {self.format_header(planet['name'])}!")
        self.send_to_player(player, f"Theme: {planet['theme']}")
        if "attribute_bonuses" in planet:
            self.send_to_player(player, f"Attribute bonuses: {planet['attribute_bonuses']}")
        if "passive_effect" in planet:
            self.send_to_player(player, f"Passive effect: {planet['passive_effect']}")
        if "gift_maneuver" in planet:
            self.send_to_player(player, f"Gift maneuver: {planet['gift_maneuver']}")
        
        # Flow: Planet -> Starsign
        self.show_starsign_selection(player)
        player.creation_state = "choosing_starsign"
        
    def show_starting_maneuvers(self, player):
        """Show available starting maneuvers"""
        self.send_to_player(player, f"\n{self.format_header('Choose Your Starting Maneuver:')}")
        self.send_to_player(player, f"You already have the gift maneuver from your planet: {player.gift_maneuver}")
        self.send_to_player(player, "Choose one additional starting maneuver:")
        
        gift_maneuver = ""
        if player.planet and player.planet in self.planets:
            gift_maneuver = self.planets[player.planet].get("gift_maneuver", "")
        available_count = 0
        
        for maneuver_id, maneuver in self.maneuvers.items():
            # Skip if it's the gift maneuver
            if maneuver_id == gift_maneuver:
                continue
            
            # Only show Lower tier maneuvers
            tier = maneuver.get("tier", "").lower()
            if tier not in ["lower", "low"]:
                continue
            
            # Check required level (must be 1 or not specified for starting maneuvers)
            required_level = maneuver.get("required_level", 1)
            if required_level > 1:
                continue
            
            # Check if it's race-specific
            required_race = maneuver.get("required_race")
            if required_race and player.race != required_race:
                continue
            
            # Check skill requirements (if any)
            can_learn = True
            if "required_skills" in maneuver and maneuver["required_skills"]:
                for skill, required in maneuver["required_skills"].items():
                    if player.skills.get(skill, 0) < required:
                        can_learn = False
                        break
            
            if can_learn:
                available_count += 1
                maneuver_name = maneuver.get('name', maneuver_id)
                maneuver_desc = maneuver.get('description', 'No description')
                
                # Add note if it's race-specific
                race_note = ""
                if required_race:
                    race_note = f" [{required_race.capitalize()} only]"
                
                # Add note if it has skill requirements
                skill_note = ""
                if "required_skills" in maneuver and maneuver["required_skills"]:
                    skill_reqs = ", ".join([f"{s} {r}" for s, r in maneuver["required_skills"].items()])
                    skill_note = f" (Requires: {skill_reqs})"
                
                self.send_to_player(player, f"  {maneuver_id}: {maneuver_name}{race_note}{skill_note}")
                self.send_to_player(player, f"    {maneuver_desc}")
                    
        if available_count == 0:
            self.send_to_player(player, "  No additional maneuvers available. Defaulting to shield_bash.")
            self.send_to_player(player, "  shield_bash: Shield Bash - Bash with shield to stagger")
            available_count = 1
            
        self.send_to_player(player, f"\nType {self.format_command('maneuver <name>')} to choose your starting maneuver.")
        
    def handle_maneuver_choice(self, player, maneuver_name):
        """Handle maneuver selection during character creation"""
        maneuver_name = maneuver_name.lower()
        
        if maneuver_name not in self.maneuvers:
            available_maneuvers = []
            for man_id, maneuver in self.maneuvers.items():
                if maneuver["tier"] == "Lower" and man_id not in player.known_maneuvers:
                    available_maneuvers.append(f"{maneuver['name']} ({man_id})")
            
            if available_maneuvers:
                maneuvers_list = ", ".join(available_maneuvers)
                self.send_to_player(player, f"Available maneuvers: {maneuvers_list}")
            else:
                self.send_to_player(player, "No available maneuvers remaining.")
            return
            
        maneuver = self.maneuvers[maneuver_name]
        
        # Check tier
        if maneuver["tier"] != "Lower":
            self.send_to_player(player, "You can only choose Lower tier maneuvers at character creation.")
            return
            
        # Check skill requirements
        for skill, required in maneuver["required_skills"].items():
            if player.skills.get(skill, 0) < required:
                self.send_to_player(player, f"You need {skill} {required} to learn this maneuver.")
                return
                
        # Check if already known (planet gift)
        if maneuver_name in player.known_maneuvers:
            self.send_to_player(player, "You already know this maneuver from your planet gift.")
            return
            
        player.known_maneuvers.append(maneuver_name)
        player.active_maneuvers.append(maneuver_name)
        
        # Show character summary
        self.send_to_player(player, f"\n{self.format_header('=== CHARACTER COMPLETE ===')}")
        self.send_to_player(player, f"Name: {player.name}")
        race_display = self.races[player.race].get('name', player.race.title()) if player.race and player.race in self.races else "Unknown"
        planet_display = self.planets[player.planet].get('name', player.planet.title()) if player.planet and player.planet in self.planets else "Unknown"
        self.send_to_player(player, f"Race: {race_display}")
        self.send_to_player(player, f"Planet: {planet_display}")
        self.send_to_player(player, f"Tier: Low (Level 1)")
        self.send_to_player(player, f"Active Maneuvers: {', '.join(player.active_maneuvers)}")
        self.send_to_player(player, "\nYour adventure begins!")
        
        player.creation_state = "complete"
        
        # Place character in world
        room = self.get_room(player.room_id)
        if room:
            room.players.add(player.name)
            # Mark starting room as explored
            self.explored_rooms[player.name].add(player.room_id)
            
        self.save_player_data(player)
        self.look_command(player, [])
        
        # Send a new prompt to indicate we're out of creation mode
        try:
            player.connection.send(b"\n> ")
        except:
            pass
        
    def create_room_command(self, player, args):
        # Admin check is now done in process_command with logging
            
        if not args:
            self.send_to_player(player, "Usage: create_room <room_id> <room_name>")
            return
            
        if len(args) < 2:
            self.send_to_player(player, "Usage: create_room <room_id> <room_name>")
            return
            
        room_id = args[0].lower()
        room_name = " ".join(args[1:])
        
        # Validate room_id
        if not room_id.replace('_', '').isalnum():
            self.send_to_player(player, "Room ID must contain only letters, numbers, and underscores.")
            return
            
        if room_id in self.rooms:
            self.send_to_player(player, f"Room '{room_id}' already exists.")
            return
            
        room = Room(room_id, room_name, "A newly created room. Description pending.")
        self.rooms[room_id] = room
        self.save_rooms_to_json()
        self.send_to_player(player, f"Room '{room_id}' created successfully!")
        
    def edit_room_command(self, player, args):
        # Admin check is now done in process_command with logging
            
        if not args:
            self.send_to_player(player, "Usage: edit_room <room_id> <field> <value>")
            self.send_to_player(player, "Fields: name, description, add_exit, remove_exit, add_flag, remove_flag")
            return
            
        if len(args) < 3 and args[1] not in ["add_exit", "remove_exit", "add_flag", "remove_flag"]:
            self.send_to_player(player, "Usage: edit_room <room_id> <field> <value>")
            return
            
        room_id = args[0].lower()
        field = args[1].lower()
        
        if room_id not in self.rooms:
            self.send_to_player(player, f"Room '{room_id}' does not exist.")
            return
            
        room = self.rooms[room_id]
        
        if field == "name":
            room.name = " ".join(args[2:])
            self.send_to_player(player, f"Room name updated to: {room.name}")
        elif field == "description":
            room.description = " ".join(args[2:])
            self.send_to_player(player, f"Room description updated.")
        elif field == "add_exit" and len(args) >= 4:
            direction = args[2].lower()
            target_room = args[3].lower()
            room.exits[direction] = target_room
            self.send_to_player(player, f"Exit '{direction}' to '{target_room}' added.")
        elif field == "remove_exit":
            direction = args[2].lower()
            if direction in room.exits:
                del room.exits[direction]
                self.send_to_player(player, f"Exit '{direction}' removed.")
            else:
                self.send_to_player(player, f"Exit '{direction}' does not exist.")
        elif field == "add_flag" and len(args) >= 3:
            flag = args[2].lower()
            if flag not in room.flags:
                room.flags.append(flag)
                self.send_to_player(player, f"Flag '{flag}' added.")
            else:
                self.send_to_player(player, f"Flag '{flag}' already exists.")
        elif field == "remove_flag" and len(args) >= 3:
            flag = args[2].lower()
            if flag in room.flags:
                room.flags.remove(flag)
                self.send_to_player(player, f"Flag '{flag}' removed.")
            else:
                self.send_to_player(player, f"Flag '{flag}' does not exist.")
        else:
            self.send_to_player(player, "Invalid field or missing arguments.")
            return
            
        self.save_rooms_to_json()
        
    def delete_room_command(self, player, args):
        # Admin check is now done in process_command with logging
            
        if not args:
            self.send_to_player(player, "Usage: delete_room <room_id>")
            return
            
        room_id = args[0].lower()
        
        if room_id not in self.rooms:
            self.send_to_player(player, f"Room '{room_id}' does not exist.")
            return
            
        if room_id == "black_anchor_common":
            self.send_to_player(player, "Cannot delete the starting room (The Black Anchor - Common Room).")
            return
            
        del self.rooms[room_id]
        
        for room in self.rooms.values():
            exits_to_remove = [dir for dir, target in room.exits.items() if target == room_id]
            for exit_dir in exits_to_remove:
                del room.exits[exit_dir]
                
        self.save_rooms_to_json()
        self.send_to_player(player, f"Room '{room_id}' deleted and all exits to it removed.")
        
    def list_rooms_command(self, player, args):
        # Admin check is now done in process_command with logging
            
        room_list = "=== Room List ===\n"
        for room_id, room in self.rooms.items():
            room_list += f"{room_id}: {room.name}\n"
            if room.exits:
                exits = ", ".join([f"{dir}->{target}" for dir, target in room.exits.items()])
                room_list += f"  Exits: {exits}\n"
            if room.flags:
                room_list += f"  Flags: {', '.join(room.flags)}\n"
            room_list += "\n"
            
        self.send_to_player(player, room_list.strip())
        
    def goto_command(self, player, args):
        # Admin check is now done in process_command with logging
            
        if not args:
            self.send_to_player(player, "Usage: goto <room_id>")
            return
            
        room_id = args[0].lower()
        
        if room_id not in self.rooms:
            self.send_to_player(player, f"Room '{room_id}' does not exist.")
            return
            
        old_room_id = player.room_id
        
        if old_room_id in self.rooms:
            self.rooms[old_room_id].players.discard(player.name)
            
        player.room_id = room_id
        self.rooms[room_id].players.add(player.name)
        
        self.send_to_player(player, f"You teleport to: {self.rooms[room_id].name}")
        self.look_command(player, [])
        
    def skills_command(self, player, args):
        """Show player's skills and levels"""
        if player.race and player.race in self.races:
            race_name = self.races[player.race].get('name', player.race.title())
        else:
            race_name = player.race.title() if player.race else "Unknown"
        header_text = f"{player.name}'s Skills"
        skills_text = f"\n{self.format_header(header_text)}\n"
        skills_text += f"Race: {race_name} | Tier: {player.get_tier()} (Level {player.level})\n\n"
        
        # Group skills by category
        categories = {
            "Physical": ["fighting", "dodging", "climbing", "swimming", "throwing"],
            "Mental": ["tracking", "investigating", "remembering", "lockpicking", "brewing"],
            "Spiritual": ["praying", "meditating", "channeling", "warding", "binding"],
            "Social": ["persuading", "intimidating", "deceiving", "leading", "bargaining"],
            "Crafting": ["repairing", "smithing", "taming"]
        }
        
        for category, skill_list in categories.items():
            skills_text += f"{category} Skills:\n"
            for skill in skill_list:
                if skill in player.skills:
                    effective = player.get_effective_skill(skill)
                    skills_text += f"  {skill.capitalize()}: {player.skills[skill]} (Effective: {effective})\n"
            skills_text += "\n"
            
        self.send_to_player(player, skills_text.strip())
        
    def maneuvers_command(self, player, args):
        """Show player's known and active maneuvers"""
        header_text = f"{player.name}'s Maneuvers"
        maneuvers_text = f"\n{self.format_header(header_text)}\n"
        maneuvers_text += f"Active: {len(player.active_maneuvers)}/{player.get_max_maneuvers()}\n\n"
        
        maneuvers_text += self.format_header("Known Maneuvers:") + "\n"
        for maneuver_id in player.known_maneuvers:
            if maneuver_id in self.maneuvers:
                maneuver = self.maneuvers[maneuver_id]
                status = "ACTIVE" if maneuver_id in player.active_maneuvers else "INACTIVE"
                status_formatted = self.format_success(status) if status == "ACTIVE" else self.format_error(status)
                maneuvers_text += f"  {maneuver['name']} {self.format_brackets(status_formatted)}\n"
                maneuvers_text += f"    {maneuver['description']}\n"
                maneuvers_text += f"    Tier: {maneuver['tier']}, Cost: {maneuver['cost']}\n"
                maneuvers_text += f"    Required Skills: {maneuver['required_skills']}\n\n"
                
        # Show available maneuvers to learn
        max_tier = player.get_tier()
        if max_tier == "Low":
            max_level = 5
        elif max_tier == "Mid":
            max_level = 10
        elif max_tier == "High":
            max_level = 15
        else:
            max_level = 99
            
        learnable = []
        for maneuver_id, maneuver in self.maneuvers.items():
            if (maneuver_id not in player.known_maneuvers and 
                maneuver["required_level"] <= player.level and
                maneuver["tier"] != "Epic"):
                
                # Check skill requirements
                can_learn = True
                for skill, required in maneuver["required_skills"].items():
                    if player.skills.get(skill, 0) < required:
                        can_learn = False
                        break
                        
                if can_learn:
                    learnable.append(maneuver)
                    
        if learnable:
            maneuvers_text += "Available to Learn:\n"
            for maneuver in learnable[:5]:  # Show first 5
                maneuvers_text += f"  {maneuver['name']} - {maneuver['description']}\n"
                
        self.send_to_player(player, maneuvers_text.strip())
    
    def process_command(self, player, command):
        if not command.strip():
            return
        
        # Validate command input
        if not self.validate_command(command):
            self.send_to_player(player, self.format_error("Invalid command format."))
            return
        
        # Rate limiting
        if not self.check_rate_limit(player.name):
            self.send_to_player(player, self.format_error("You are sending commands too quickly. Please wait a moment."))
            return
        
        parts = command.strip().split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Handle character creation commands
        # Check if player is in character creation (None or any non-complete state)
        # None means new character that needs to start creation
        creation_state = getattr(player, 'creation_state', None)
        
        # If creation_state is None and this is the first command, start character creation
        if creation_state is None:
            # Check if player has completed any creation steps (has race, etc.)
            # If they have attributes/race set, they're an old character - set to complete
            if hasattr(player, 'race') and player.race:
                # Existing character without creation_state - set to complete for backwards compatibility
                player.creation_state = "complete"
                creation_state = "complete"
            else:
                # New character - start character creation
                self.character_creation_welcome(player)
                return
        
        # Handle character creation commands
        if creation_state is not None and creation_state != "complete":
            # Allow help command during creation
            if cmd in ["help", "?"]:
                self.help_command(player, args)
                return
            
            if cmd == "race" and args and player.creation_state == "choosing_race":
                self.handle_race_choice(player, args[0])
            elif cmd == "assign" and args and player.creation_state == "assigning_points":
                self.handle_attribute_assignment(player, args[0])
            elif cmd == "planet" and args and player.creation_state == "choosing_planet":
                self.handle_planet_choice(player, args[0])
            elif cmd == "starsign" and args and player.creation_state == "choosing_starsign":
                self.handle_starsign_choice(player, args[0])
            elif cmd == "maneuver" and args and player.creation_state == "choosing_maneuver":
                self.handle_maneuver_choice(player, args[0])
            # Allow direct input for creation steps (e.g., just "earth" instead of "planet earth")
            elif player.creation_state == "choosing_planet" and not args:
                # User typed just the planet name
                self.handle_planet_choice(player, cmd)
            elif player.creation_state == "choosing_race" and not args:
                # User typed just the race name
                self.handle_race_choice(player, cmd)
            elif player.creation_state == "choosing_starsign" and not args:
                # User typed just the starsign name
                self.handle_starsign_choice(player, cmd)
            elif player.creation_state == "choosing_maneuver" and not args:
                # User typed just the maneuver name
                self.handle_maneuver_choice(player, cmd)
            else:
                self.send_to_player(player, self.format_error("Invalid creation command. Please follow the prompts. Type 'help' to see available commands."))
            return
        
        # Regular game commands - use extracted command handlers if available
        command_handled = False
        if COMMANDS_AVAILABLE:
            if cmd in ["look", "l"]:
                look_command(self, player, args)
                command_handled = True
            elif cmd in ["move", "go"]:
                if args:
                    move_command(self, player, args[0].lower())
                else:
                    self.send_to_player(player, "Go where?")
                command_handled = True
            elif cmd == "say":
                say_command(self, player, args)
                command_handled = True
            elif cmd in ["inventory", "i"]:
                inventory_command(self, player, args)
                command_handled = True
            elif cmd in ["get", "take"]:
                get_command(self, player, args)
                command_handled = True
            elif cmd == "drop":
                drop_command(self, player, args)
                command_handled = True
            elif cmd == "use" and args and len(args) > 0 and args[0].lower() == "maneuver":
                use_maneuver_command(self, player, args[1:])
                command_handled = True
            elif cmd == "use":
                use_command(self, player, args)
                command_handled = True
            elif cmd == "attack":
                attack_command(self, player, args)
                command_handled = True
            elif cmd == "stats":
                stats_command(self, player, args)
                command_handled = True
            elif cmd == "skills":
                skills_command(self, player, args)
                command_handled = True
            elif cmd == "maneuvers":
                maneuvers_command(self, player, args)
                command_handled = True
            elif cmd in ["help", "?"]:
                help_command(self, player, args)
                command_handled = True
            elif cmd == "who":
                who_command(self, player, args)
                command_handled = True
            elif cmd == "join" and args and args[0] == "combat":
                join_combat_command(self, player, args)
                command_handled = True
            elif cmd == "disengage":
                disengage_command(self, player, args)
                command_handled = True
            elif cmd == "quests":
                quests_command(self, player, args)
                command_handled = True
            elif cmd == "quest" and args:
                quest_command(self, player, args)
                command_handled = True
            elif cmd == "equip" and args:
                equip_command(self, player, args)
                command_handled = True
            elif cmd == "unequip" and args:
                unequip_command(self, player, args)
                command_handled = True
            elif cmd == "wield" and args:
                # Alias for equip weapon
                equip_command(self, player, ["weapon"] + args)
                command_handled = True
            elif cmd == "weapons" and self.is_admin(player):
                list_weapons_command(self, player, args)
                command_handled = True
            elif cmd == "create_weapon" and args and self.is_admin(player):
                create_weapon_command(self, player, args)
                command_handled = True
            elif cmd == "inspect" and args:
                inspect_command(self, player, args)
                command_handled = True
            elif cmd == "time":
                time_command(self, player, args)
                command_handled = True
            elif cmd == "set_time" and args and self.is_admin(player):
                set_time_command(self, player, args)
                command_handled = True
            elif cmd == "talk" and args:
                talk_command(self, player, args)
                command_handled = True
            elif cmd == "buy" and args:
                buy_command(self, player, args)
                command_handled = True
            elif cmd == "sell" and args:
                sell_command(self, player, args)
                command_handled = True
            elif cmd == "list" or (cmd == "shop" and not args):
                shop_list_command(self, player, args)
                command_handled = True
            elif cmd == "repair" and args:
                repair_command(self, player, args)
                command_handled = True
        else:
            # Fallback to methods (backward compatibility)
            if cmd in ["look", "l"]:
                self.look_command(player, args)
                command_handled = True
            elif cmd in ["move", "go"]:
                if args:
                    self.move_command(player, args[0].lower())
                else:
                    self.send_to_player(player, "Go where?")
                command_handled = True
            elif cmd == "say":
                self.say_command(player, args)
                command_handled = True
            elif cmd in ["inventory", "i"]:
                self.inventory_command(player, args)
                command_handled = True
            elif cmd in ["get", "take"]:
                self.get_command(player, args)
                command_handled = True
            elif cmd == "drop":
                self.drop_command(player, args)
                command_handled = True
            elif cmd == "use":
                # Check if it's "use maneuver" first
                if args and len(args) > 0 and args[0].lower() == "maneuver":
                    self.use_maneuver_command(player, args[1:])
                else:
                    self.use_command(player, args)
                command_handled = True
            elif cmd == "attack":
                self.attack_command(player, args)
                command_handled = True
            elif cmd == "stats":
                self.stats_command(player, args)
                command_handled = True
            elif cmd == "skills":
                self.skills_command(player, args)
                command_handled = True
            elif cmd == "maneuvers":
                self.maneuvers_command(player, args)
                command_handled = True
            elif cmd in ["help", "?"]:
                self.help_command(player, args)
                command_handled = True
            elif cmd == "who":
                self.who_command(player, args)
                command_handled = True
            elif cmd == "join" and args and args[0] == "combat":
                self.join_combat_command(player, args)
                command_handled = True
            elif cmd == "disengage":
                self.disengage_command(player, args)
                command_handled = True
            elif cmd == "quests":
                self.quests_command(player, args)
                command_handled = True
            elif cmd == "quest" and args:
                self.quest_command(player, args)
                command_handled = True
            elif cmd == "equip" and args:
                self.equip_command(player, args)
                command_handled = True
            elif cmd == "unequip" and args:
                self.unequip_command(player, args)
                command_handled = True
            elif cmd == "wield" and args:
                # Alias for equip weapon
                self.equip_command(player, ["weapon"] + args)
                command_handled = True
            elif cmd == "weapons" and self.is_admin(player):
                self.list_weapons_command(player, args)
                command_handled = True
            elif cmd == "create_weapon" and args and self.is_admin(player):
                self.create_weapon_command(player, args)
                command_handled = True
            elif cmd == "inspect" and args:
                self.inspect_command(player, args)
                command_handled = True
            elif cmd == "time":
                self.time_command(player, args)
                command_handled = True
            elif cmd == "set_time" and args and self.is_admin(player):
                self.set_time_command(player, args)
                command_handled = True
            elif cmd == "talk" and args:
                self.talk_command(player, args)
                command_handled = True
            elif cmd == "buy" and args:
                self.buy_command(player, args)
                command_handled = True
            elif cmd == "sell" and args:
                self.sell_command(player, args)
                command_handled = True
            elif cmd == "list" or (cmd == "shop" and not args):
                self.shop_list_command(player, args)
                command_handled = True
            elif cmd == "repair" and args:
                repair_command(self, player, args)
                command_handled = True
        
        # If command was already handled, return early
        if command_handled:
            return
        
        # Commands that don't use the command handlers (special cases)
        if cmd == "setpassword" and args:
            # Password changes are managed through Firebase
            self.send_to_player(player, "Password changes must be done through Firebase Authentication.")
            self.send_to_player(player, "Please use the Firebase Console or contact an administrator.")
        elif cmd == "setoutlook" and args and len(args) >= 3:
            # Admin command to set NPC outlook
            if not self.is_admin(player):
                self.send_to_player(player, "You don't have permission.")
                return
            npc_name = args[0].lower()
            player_name = args[1].lower()
            try:
                outlook_value = int(args[2])
            except ValueError:
                self.send_to_player(player, "Outlook value must be a number (-100 to 100).")
                return
            
            # Find NPC
            npc = None
            for npc_id, n in self.npcs.items():
                if npc_name in n.name.lower():
                    npc = n
                    break
            
            if not npc:
                self.send_to_player(player, f"NPC '{npc_name}' not found.")
                return
            
            if not hasattr(npc, 'outlooks'):
                npc.outlooks = {}
            
            npc.outlooks[player_name] = max(-100, min(100, outlook_value))
            self.send_to_player(player, f"Set {npc.name}'s outlook toward {player_name} to {outlook_value}.")
            if self.logger:
                self.logger.log_admin_action(player.name, "SET_OUTLOOK", f"NPC: {npc.name}, Player: {player_name}, Value: {outlook_value}")
        elif cmd == "setadminpassword" and args and self.is_admin(player):
            # Admin command removed - passwords are managed through Firebase
            self.send_to_player(player, "Admin passwords are managed through Firebase Authentication.")
            self.send_to_player(player, "Use Firebase Console to manage user accounts.")
        elif cmd == "fixcharacter":
            # Command to fix corrupted character data (invalid planet/race/starsign)
            issues = []
            fixes = []
            
            # Check and fix planet
            if player.planet:
                if player.planet not in self.planets:
                    issues.append(f"Invalid planet: '{player.planet}'")
                    # Special mappings for common typos/old names
                    planet_mappings = {
                        'earth': 'veyra',  # Earth-aligned -> Veyra
                        'fire': 'aurelion',  # Fire-aligned -> Aurelion
                        'water': 'thalos',  # Water-aligned -> Thalos
                        'air': 'nyssara',  # Air-aligned -> Nyssara
                    }
                    
                    planet_lower = player.planet.lower()
                    matching_planet = planet_mappings.get(planet_lower)
                    
                    # Try to find a matching planet (case-insensitive or partial match)
                    if not matching_planet:
                        for planet_id in self.planets.keys():
                            if planet_lower in planet_id.lower() or planet_id.lower() in planet_lower:
                                matching_planet = planet_id
                                break
                    
                    if matching_planet:
                        fixes.append(f"Planet '{player.planet}' -> '{matching_planet}'")
                        player.planet = matching_planet
                    else:
                        # Default to first available planet
                        if self.planets:
                            default_planet = list(self.planets.keys())[0]
                            fixes.append(f"Planet '{player.planet}' -> '{default_planet}' (default)")
                            player.planet = default_planet
            
            # Check and fix race
            if player.race:
                if player.race not in self.races:
                    issues.append(f"Invalid race: '{player.race}'")
                    race_lower = player.race.lower()
                    matching_race = None
                    for race_id in self.races.keys():
                        if race_lower in race_id.lower() or race_id.lower() in race_lower:
                            matching_race = race_id
                            break
                    
                    if matching_race:
                        fixes.append(f"Race '{player.race}' -> '{matching_race}'")
                        player.race = matching_race
                    elif self.races:
                        default_race = list(self.races.keys())[0]
                        fixes.append(f"Race '{player.race}' -> '{default_race}' (default)")
                        player.race = default_race
            
            # Check and fix starsign
            if player.starsign:
                if player.starsign not in self.starsigns:
                    issues.append(f"Invalid starsign: '{player.starsign}'")
                    starsign_lower = player.starsign.lower()
                    matching_starsign = None
                    for starsign_id in self.starsigns.keys():
                        if starsign_lower in starsign_id.lower() or starsign_id.lower() in starsign_lower:
                            matching_starsign = starsign_id
                            break
                    
                    if matching_starsign:
                        fixes.append(f"Starsign '{player.starsign}' -> '{matching_starsign}'")
                        player.starsign = matching_starsign
                    elif self.starsigns:
                        default_starsign = list(self.starsigns.keys())[0]
                        fixes.append(f"Starsign '{player.starsign}' -> '{default_starsign}' (default)")
                        player.starsign = default_starsign
            
            if issues:
                self.send_to_player(player, f"\n{self.format_header('Character Data Issues Found:')}")
                for issue in issues:
                    self.send_to_player(player, f"  - {issue}")
                
                if fixes:
                    self.send_to_player(player, f"\n{self.format_header('Applied Fixes:')}")
                    for fix in fixes:
                        self.send_to_player(player, f"  - {fix}")
                    self.save_player_data(player)
                    self.send_to_player(player, "\nCharacter data has been fixed and saved!")
                else:
                    self.send_to_player(player, "\nCould not automatically fix issues. Please contact an admin.")
            else:
                self.send_to_player(player, "No character data issues found. Your character data is valid!")
        elif cmd == "create_room":
            if self.is_admin(player):
                if self.logger:
                    self.logger.log_admin_action(player.name, "CREATE_ROOM", f"Room: {args[0] if args else 'unknown'}")
                if COMMANDS_AVAILABLE:
                    create_room_command(self, player, args)
                else:
                    self.create_room_command(player, args)
            else:
                self.send_to_player(player, "You don't have permission to create rooms.")
        elif cmd == "edit_room":
            if self.is_admin(player):
                if self.logger:
                    self.logger.log_admin_action(player.name, "EDIT_ROOM", f"Room: {args[0] if args else 'unknown'}")
                if COMMANDS_AVAILABLE:
                    edit_room_command(self, player, args)
                else:
                    self.edit_room_command(player, args)
            else:
                self.send_to_player(player, "You don't have permission to edit rooms.")
        elif cmd == "delete_room":
            if self.is_admin(player):
                if self.logger:
                    self.logger.log_admin_action(player.name, "DELETE_ROOM", f"Room: {args[0] if args else 'unknown'}")
                if COMMANDS_AVAILABLE:
                    delete_room_command(self, player, args)
                else:
                    self.delete_room_command(player, args)
            else:
                self.send_to_player(player, "You don't have permission to delete rooms.")
        elif cmd == "list_rooms":
            if self.is_admin(player):
                if self.logger:
                    self.logger.log_admin_action(player.name, "LIST_ROOMS", "")
                if COMMANDS_AVAILABLE:
                    list_rooms_command(self, player, args)
                else:
                    self.list_rooms_command(player, args)
            else:
                self.send_to_player(player, "You don't have permission to list rooms.")
        elif cmd == "goto":
            if self.is_admin(player):
                if self.logger:
                    self.logger.log_admin_action(player.name, "GOTO", f"Room: {args[0] if args else 'unknown'}")
                if COMMANDS_AVAILABLE:
                    goto_command(self, player, args)
                else:
                    self.goto_command(player, args)
            else:
                self.send_to_player(player, "You don't have permission to teleport.")
        elif cmd == "quit":
            player.is_logged_in = False
            return
        else:
            # Only show "Unknown command" if no command was handled
            if not command_handled:
                self.send_to_player(player, "Unknown command. Type 'help' for available commands.")
            
    async def handle_websocket_client(self, websocket, path):
        """Handle WebSocket client connections"""
        player_name = None
        player = None
        room = None
        
        # Get remote address safely
        try:
            address = websocket.remote_address if hasattr(websocket, 'remote_address') else ('unknown', 0)
        except Exception:
            address = ('unknown', 0)
        
        # Check connection limit
        try:
            with self.connection_lock:
                if self.active_connections >= self.max_connections:
                    await websocket.send("Server is full. Please try again later.\n")
                    await websocket.close()
                    return
                self.active_connections += 1
        except Exception as e:
            print(f"Error checking connection limit: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Create message queue for sending
        send_queue = asyncio.Queue()
        ws_loop = asyncio.get_running_loop()
        
        # Task to send queued messages
        async def send_messages():
            while True:
                try:
                    if websocket.closed:
                        break
                    message = await asyncio.wait_for(send_queue.get(), timeout=0.1)
                    await websocket.send(message)
                except asyncio.TimeoutError:
                    continue
                except (websockets.exceptions.ConnectionClosed, websockets.exceptions.InvalidState):
                    break
                except Exception as e:
                    print(f"Error sending WebSocket message: {e}")
                    break
        
        send_task = asyncio.create_task(send_messages())
        
        try:
            # Token-based authentication - expect JSON message with token
            try:
                auth_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            except asyncio.TimeoutError:
                await websocket.close(code=1008, reason="Auth timeout")
                with self.connection_lock:
                    self.active_connections = max(0, self.active_connections - 1)
                return
            except websockets.exceptions.ConnectionClosed:
                with self.connection_lock:
                    self.active_connections = max(0, self.active_connections - 1)
                return
            
            if not auth_message:
                await websocket.close()
                with self.connection_lock:
                    self.active_connections = max(0, self.active_connections - 1)
                return
            
            # Parse auth message (expect JSON with type and token)
            id_token = None
            try:
                auth_data = json.loads(auth_message)
                if auth_data.get('type') != 'auth':
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Authentication required. Send {"type": "auth", "token": "your_token"}'
                    }))
                    await websocket.close()
                    with self.connection_lock:
                        self.active_connections = max(0, self.active_connections - 1)
                    return
                id_token = auth_data.get('token')
            except json.JSONDecodeError:
                # Not JSON - might be plain text command from vanilla client
                # Send helpful error and close
                await websocket.send(json.dumps({
                    'type': 'error',
                    'message': 'This server requires Firebase authentication. Send {"type": "auth", "token": "your_firebase_token"} as the first message.'
                }))
                await websocket.close()
                with self.connection_lock:
                    self.active_connections = max(0, self.active_connections - 1)
                return
            
            if not id_token:
                await websocket.send(json.dumps({
                    'type': 'auth_error',
                    'error': 'No token provided'
                }))
                await websocket.close()
                with self.connection_lock:
                    self.active_connections = max(0, self.active_connections - 1)
                return
            
            # Verify ID token with Firebase Admin SDK
            try:
                # IMPORTANT: Firebase verification is synchronous and can block the event loop.
                # Run it in a worker thread with a timeout.
                decoded_token = await asyncio.wait_for(
                    asyncio.to_thread(self.firebase_auth.verify_id_token, id_token),
                    timeout=5.0,
                )
                if not decoded_token:
                    await websocket.send(json.dumps({
                        'type': 'auth_error',
                        'error': 'Invalid token'
                    }))
                    await websocket.close()
                    return
                
                uid = decoded_token['uid']
                email = decoded_token.get('email', '').lower()
            except asyncio.TimeoutError:
                await websocket.send(json.dumps({
                    'type': 'auth_error',
                    'error': 'Token verification timed out'
                }))
                await websocket.close()
                with self.connection_lock:
                    self.active_connections = max(0, self.active_connections - 1)
                return
            except Exception as e:
                print(f"Error verifying token: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send(json.dumps({
                    'type': 'auth_error',
                    'error': 'Token verification failed'
                }))
                if self.logger:
                    self.logger.log_login_attempt(email if 'email' in locals() else 'unknown', address, False)
                await websocket.close()
                with self.connection_lock:
                    self.active_connections = max(0, self.active_connections - 1)
                return
            
            # Load player data by Firebase UID
            player_data = None
            if self.firebase:
                # Firebase IO is synchronous; run it off the event loop with a timeout.
                try:
                    player_data = await asyncio.wait_for(
                        asyncio.to_thread(self.firebase.load_player_by_uid, uid),
                        timeout=5.0,
                    )
                except asyncio.TimeoutError:
                    player_data = None
            
            # Create WebSocket wrapper for Player class
            ws_connection = WebSocketConnection(websocket, address, send_queue, loop=ws_loop)
            
            is_new_character = False
            if player_data:
                # Existing character - load data
                player_name = player_data.get('name')
                player = Player(player_name, ws_connection, address)
                player.from_dict(player_data)
                
                # Update Firebase UID and email if not set (for migration)
                if not hasattr(player, 'firebase_uid') or not player.firebase_uid:
                    player.firebase_uid = uid
                    player.email = email
                    # Saving may do synchronous IO; avoid blocking the event loop.
                    try:
                        await asyncio.wait_for(
                            asyncio.to_thread(self.save_player_data, player),
                            timeout=5.0,
                        )
                    except asyncio.TimeoutError:
                        pass  # Timeout saving player data
            else:
                # New user - need to create character
                # Send message requesting character name
                await websocket.send(json.dumps({
                    'type': 'auth_success',
                    'new_user': True,
                    'message': 'Enter your character name:'
                }))
                
                # Wait for character name - loop until we get a valid name (ignore duplicate auth messages)
                character_name_raw = None
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    except asyncio.TimeoutError:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': 'Timeout waiting for character name. Please reconnect and try again.'
                        }))
                        await websocket.close()
                        return
                    
                    if not message:
                        await websocket.close()
                        return
                    
                    # Parse if JSON, otherwise treat as plain text
                    try:
                        name_data = json.loads(message)
                        # Ignore duplicate auth messages (frontend may send them due to React Strict Mode)
                        if name_data.get('type') == 'auth':
                            # Just ignore it and continue waiting for character name
                            continue
                        character_name_raw = name_data.get('name') or name_data.get('text') or message
                    except json.JSONDecodeError:
                        character_name_raw = message
                    
                    # Reject if it looks like a JWT token (starts with "eyJ")
                    if character_name_raw.strip().startswith('eyJ'):
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': 'Invalid character name. Please enter a proper character name, not a token.'
                        }))
                        # Continue waiting for a valid name instead of closing
                        continue
                    
                    # We have a valid-looking name, break out of the loop
                    break
                
                try:
                    player_name = self.sanitize_player_name(character_name_raw.strip()).lower()
                except ValueError as e:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': f'Invalid character name: {str(e)}'
                    }))
                    await websocket.close()
                    return
                
                # Check if character name already exists
                existing_data = self.load_player_data(player_name)
                if existing_data:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Character name already taken.'
                    }))
                    await websocket.close()
                    return
                
                # Create new player
                player = Player(player_name, ws_connection, address)
                player.firebase_uid = uid
                player.email = email
                is_new_character = True
                
                if self.logger:
                    self.logger.log_security_event("CHARACTER_CREATED", email, f"Character: {player_name}")
            
            # Log successful authentication
            if self.logger:
                self.logger.log_login_attempt(email, address, True)
            
            # Send auth success message (only for existing users, new users already got it)
            if not is_new_character:
                await websocket.send(json.dumps({
                    'type': 'auth_success',
                    'new_user': False
                }))
            
            # If this player name is already logged in, always kick the old
            # connection and remove the old player entry before proceeding.
            # This makes browser refresh / reconnects robust.
            old_player = None
            try:
                with self.player_lock:
                    old_player = self.players.get(player_name)
            except Exception as e:
                print(f"Error checking for old player: {e}")
            
            if old_player is not None:
                old_ws = getattr(getattr(old_player, 'ws_connection', None), 'websocket', None)
                if old_ws is not None:
                    try:
                        await old_ws.close()
                    except Exception:
                        pass
                
                # Ensure old player is fully removed before we continue.
                # Run in executor to avoid blocking (remove_player calls Firebase synchronously)
                try:
                    loop = asyncio.get_running_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(self.ws_executor, self.remove_player, player_name),
                        timeout=2.0
                    )
                except (asyncio.TimeoutError, Exception):
                    pass  # Continue anyway
            
            # Set creation state
            # New characters (is_new_character=True) should have creation_state as None to trigger character creation
            # Existing characters should have creation_state as "complete"
            if is_new_character:
                # New character - leave creation_state as None to start character creation
                pass
            elif not hasattr(player, 'creation_state') or player.creation_state is None:
                # Existing character without creation_state - set to complete
                player.creation_state = "complete"
            
            # Check admin status and set custom claims
            if player.name in self.admin_config.get("admins", {}):
                if hasattr(player, 'firebase_uid') and player.firebase_uid:
                    admin_info = self.admin_config["admins"][player.name]
                    permissions = admin_info.get("permissions", ["all"])
                    # Synchronous Firebase call; avoid blocking the event loop.
                    try:
                        await asyncio.wait_for(
                            asyncio.to_thread(self.firebase_auth.set_admin_claim, player.firebase_uid, True, permissions),
                            timeout=5.0,
                        )
                    except asyncio.TimeoutError:
                        pass  # Timeout setting admin claim
            
            # Load or create character
            try:
                if player.creation_state == "complete":
                    welcome_back = f"Welcome back, {player_name}!\nType {self.format_command('help')} to see available commands.\n\n"
                    # Use send_to_player to strip ANSI codes for WebSocket
                    self.send_to_player(player, welcome_back.rstrip())
                    
                    player.max_maneuvers = player.get_max_maneuvers()
                    
                    room = self.get_room(player.room_id)
                    if room:
                        room.players.add(player.name)
                        self.explored_rooms[player.name].add(player.room_id)
                    else:
                        print(f"Warning: Room {player.room_id} not found for {player_name}")
                    
                    self.add_player(player)
                    # Run look command off the event loop (may involve heavy sync work).
                    loop = asyncio.get_running_loop()
                    if COMMANDS_AVAILABLE:
                        await loop.run_in_executor(self.ws_executor, look_command, self, player, [])
                    else:
                        await loop.run_in_executor(self.ws_executor, self.look_command, player, [])
                else:
                    # New character - start creation
                    self.send_to_player(player, f"Welcome, {player_name}!\n\n")
                    self.add_player(player)
                    self.character_creation_welcome(player)
            except Exception as e:
                print(f"Error loading/creating character {player_name}: {e}")
                import traceback
                traceback.print_exc()
            
            # Ensure player is added and marked as logged in before starting game loop
            if player_name not in self.players:
                self.add_player(player)
            
            if not player.is_logged_in:
                player.is_logged_in = True
            
            # Game loop
            try:
                while player.is_logged_in and not websocket.closed:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        
                        if not message:
                            break
                        
                        command = message.strip()
                        if command:
                            try:
                                loop = asyncio.get_running_loop()
                                await loop.run_in_executor(self.ws_executor, self.process_command, player, command)
                            except Exception as e:
                                print(f"Error processing command '{command}': {e}")
                                traceback.print_exc()
                                self.send_to_player(player, f"Error processing command: {e}")
                    except asyncio.TimeoutError:
                        # Timeout is normal - check connection state and continue
                        if websocket.closed or not player.is_logged_in:
                            break
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        break
                    except websockets.exceptions.InvalidState:
                        break
            except websockets.exceptions.ConnectionClosed as e:
                # 1000=normal close, 1001=going away (reload/tab close) — don't log
                if e.code not in (1000, 1001, None) and self.logger:
                    self.logger.log_error("WEBSOCKET_ERROR", f"Unexpected close code {e.code}: {e.reason}", address)
            except Exception as e:
                ip_str = f"{address[0]}" if isinstance(address, tuple) else str(address)
                print(f"Exception in game loop for {player_name} from {ip_str}: {e}")
                import traceback
                traceback.print_exc()
                if self.logger:
                    self.logger.log_error("WEBSOCKET_ERROR", str(e), address)
            finally:
                # Ensure player is marked as logged out
                player.is_logged_in = False
                    
        except websockets.exceptions.ConnectionClosed as e:
            # 1000=normal close, 1001=going away (reload/tab close) — don't log
            ip_str = f"{address[0]}" if isinstance(address, tuple) else str(address)
            if e.code not in (1000, 1001, None):
                if self.logger:
                    self.logger.log_error("WEBSOCKET_ERROR", f"Unexpected close code {e.code}: {e.reason}", address)
                print(f"ConnectionClosed for {ip_str}: code={e.code}, reason={e.reason}")
        except websockets.exceptions.InvalidState:
            # Connection already closed - normal, don't log
            pass
        except Exception as e:
            ip_str = f"{address[0]}" if isinstance(address, tuple) else str(address)
            # Check if it's a normal disconnection message
            error_str = str(e)
            if "1001" in error_str and "going away" in error_str.lower():
                # Normal client disconnection - don't log as error
                pass
            else:
                if self.logger:
                    self.logger.log_error("WEBSOCKET_ERROR", str(e), address)
                print(f"Error handling WebSocket client from {ip_str}: {e}")
        finally:
            # Cancel send task
            send_task.cancel()
            try:
                await asyncio.wait_for(send_task, timeout=1.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            
            # Clean up player state - run in executor to avoid blocking event loop
            if player_name is not None:
                try:
                    loop = asyncio.get_running_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(self.ws_executor, self.remove_player, player_name),
                        timeout=2.0
                    )
                    if room is not None:
                        room.players.discard(player_name)
                except (asyncio.TimeoutError, Exception):
                    pass  # Continue cleanup even if removal fails
            
            # Decrement connection counter
            try:
                with self.connection_lock:
                    self.active_connections = max(0, self.active_connections - 1)
            except Exception:
                # Force decrement even if lock fails
                try:
                    self.active_connections = max(0, self.active_connections - 1)
                except:
                    pass
            
            # Try to close websocket (but don't block if it's already closed)
            try:
                if not websocket.closed:
                    await asyncio.wait_for(websocket.close(), timeout=0.5)
            except (websockets.exceptions.ConnectionClosed, websockets.exceptions.InvalidState, asyncio.TimeoutError, Exception):
                pass
    
    def start_websocket_server(self):
        """Start WebSocket server in a separate thread"""
        if not WEBSOCKET_AVAILABLE:
            print("WebSocket support not available. Install websockets library.")
            return
        
        async def run_websocket_server():
            # Suppress InvalidUpgrade errors (common when browsers/proxies hit the port)
            import logging
            websockets_logger = logging.getLogger('websockets.server')
            websockets_logger.setLevel(logging.WARNING)  # Only show warnings and errors, not InvalidUpgrade

            # Use legacy server API for a reliable HTTP upgrade handshake.
            # (We observed TCP accept works but websocket opening handshake times out even locally.)
            from websockets.legacy.server import serve

            async def handler(ws, path):
                async def handle_connection():
                    try:
                        remote_addr = getattr(ws, "remote_address", "unknown")
                    except Exception:
                        remote_addr = "unknown"
                    
                    # Check connection limit
                    try:
                        with self.connection_lock:
                            if self.active_connections >= self.max_connections:
                                await ws.close(code=1008, reason="Server full")
                                return
                    except Exception as e:
                        print(f"Error checking connection limit: {e}")
                        return
                    
                    # Call the actual handler
                    try:
                        await self.handle_websocket_client(ws, path)
                    except websockets.exceptions.ConnectionClosed:
                        pass  # Normal connection closure
                    except Exception as e:
                        print(f"WebSocket handler error: {e}")
                        import traceback
                        traceback.print_exc()
                
                await handle_connection()

            print(f"Starting WebSocket server on {self.bind_address}:{self.websocket_port}...")
            async with serve(
                handler,
                self.bind_address,
                self.websocket_port,
                ping_interval=20,
                ping_timeout=20,
                compression=None,
                # Add connection timeout to prevent hanging connections
                close_timeout=10,
            ) as server:
                print(f"WebSocket server started and listening on {self.bind_address}:{self.websocket_port}")
                await asyncio.Future()  # Run forever
        
        # Run in new event loop in separate thread
        server_ready = threading.Event()
        server_started = threading.Event()
        
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                task = loop.create_task(run_websocket_server())
                server_ready.set()
                loop.call_later(0.5, lambda: server_started.set())
                loop.run_until_complete(task)
            except KeyboardInterrupt:
                pass
            except Exception as e:
                print(f"ERROR: WebSocket server failed to start: {e}")
                import traceback
                traceback.print_exc()
            finally:
                loop.close()
        
        ws_thread = threading.Thread(target=run_in_thread, daemon=True)
        ws_thread.start()
        
        # Wait for server to be ready (with timeout)
        if server_ready.wait(timeout=2.0):
            if not server_started.wait(timeout=3.0):
                print("Warning: WebSocket server thread started but may not be listening yet")
        else:
            print("ERROR: WebSocket server thread failed to start within timeout")
            

if __name__ == "__main__":
    if not WEBSOCKET_AVAILABLE:
        print("Error: websockets library is required. Install it with: pip install websockets")
        exit(1)
    
    try:
        print("Initializing MUD server...")
        game = MudGame()
        print("MUD server initialized successfully.")
        print(f"WebSocket will bind to: {game.bind_address}:{game.websocket_port}")
        
        # Start WebSocket server (web-only now)
        print("Starting web-based MUD server...")
        game.start_websocket_server()
        
        # Keep main thread alive
        print("Server is running. Press Ctrl+C to stop.")
        print(f"WebSocket accepting connections on {game.bind_address}:{game.websocket_port}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down server...")
            if hasattr(game, 'logger') and game.logger:
                game.logger.log_info("Server shutting down")
    except Exception as e:
        print(f"\nFATAL ERROR: Server crashed during initialization or runtime:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        import traceback
        traceback.print_exc()
        exit(1)