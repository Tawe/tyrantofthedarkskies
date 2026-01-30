"""Information and character display commands."""

def help_command(game, player, args):
    """Display help text with all available commands."""
    help_text = f"""
{game.format_header('=== TYRANT OF THE DARK SKIES - COMMAND HELP ===')}

"""
    
    # Show character creation commands if player is in creation
    if hasattr(player, 'creation_state') and player.creation_state != "complete":
        help_text += f"""
{game.format_header('Character Creation Commands:')}
{game.format_command('race')} <name> - Choose your race
{game.format_command('assign')} <attribute> - Assign free attribute points (humans only)
{game.format_command('planet')} <name> - Choose your planet
{game.format_command('starsign')} <name> - Choose your starsign
{game.format_command('maneuver')} <name> - Choose your starting maneuver

"""
    
    help_text += f"""
{game.format_header('Movement & Exploration:')}
{game.format_command('look')} or {game.format_command('l')} - Look around the current room
{game.format_command('look')} <direction> - Look in a specific direction (e.g., 'look north')
{game.format_command('move')} or {game.format_command('go')} <direction> - Move in a direction (north, south, east, west, etc.)
{game.format_command('say')} <message> - Say something to others in the room
{game.format_command('who')} - See who is currently online

{game.format_header('Inventory & Items:')}
{game.format_command('inventory')} or {game.format_command('i')} - Check your inventory
{game.format_command('get')}, {game.format_command('take')}, or {game.format_command('pickup')} <item> - Pick up an item from the room (or from an interactable)
{game.format_command('drop')} <item> - Drop an item from your inventory
{game.format_command('use')} <item> - Use a consumable item (potions, etc.)
{game.format_command('equip')} <item> or {game.format_command('equip')} <slot> <item> - Equip a weapon or armor
{game.format_command('unequip')} <slot> - Unequip an item
{game.format_command('wield')} <weapon> - Equip a weapon (alias)
{game.format_command('inspect')} <item> - Inspect an item for detailed stats
{game.format_command('time')} - Check the current in-game time
{game.format_command('talk')} <npc> <keyword> - Talk to an NPC using keywords
{game.format_command('list')} or {game.format_command('shop')} - List items for sale
{game.format_command('buy')} <item> - Buy an item from a merchant
{game.format_command('sell')} <item> - Sell an item to a merchant
{game.format_command('repair')} <item> - Repair a weapon or armor

{game.format_header('Combat:')}
{game.format_command('attack')} <target> - Attack a hostile creature
{game.format_command('join combat')} [target] - Join an active combat
{game.format_command('disengage')} - Attempt to leave combat
{game.format_command('use maneuver')} <name> - Use a maneuver

{game.format_header('Character Information:')}
{game.format_command('stats')} - View your character sheet (attributes, resources, race, planet, starsign)
{game.format_command('skills')} - View all your skills and effective skill levels
{game.format_command('maneuvers')} - View your known maneuvers and available ones to learn
{game.format_command('quests')} - View your active quests
{game.format_command('quest')} <command> - Manage quests (list, accept, complete)

{game.format_header('System:')}
{game.format_command('help')} or {game.format_command('?')} - Show this help message
{game.format_command('quit')} - Leave the game

"""
    
    # Show admin commands if player is admin
    if game.is_admin(player):
        help_text += f"""
{game.format_header('Admin Commands:')}
{game.format_command('create_room')} <room_id> <name> - Create a new room
{game.format_command('edit_room')} <room_id> <field> <value> - Edit room properties
{game.format_command('delete_room')} <room_id> - Delete a room
{game.format_command('list_rooms')} - List all rooms
{game.format_command('goto')} <room_id> - Teleport to a room
{game.format_command('weapons')} - List available weapon templates
{game.format_command('create_weapon')} <template> [modifier] [item_id] - Create a weapon item
{game.format_command('setoutlook')} <npc> <player> <value> - Set NPC outlook
{game.format_command('set_time')} <day> <hour> [minute] - Set world time

"""
    
    help_text += f"""
{game.format_header('Game System Notes:')}
- Skills use a unified {game.format_command('d100')} check system
- Effective skill = base skill + attribute bonuses + difficulty modifiers
- Skills advance through successful use (higher skills are harder to advance)
- Maneuvers are special abilities learned from masters throughout the world
- Your planet, race, and starsign affect your starting attributes and abilities
- Type {game.format_command('look')} to see available exits and items in each room
"""
    
    # Send help text using send_to_player_raw to preserve newlines
    # (send_to_player adds extra newline which we don't want here)
    game.send_to_player_raw(player, help_text)


def stats_command(game, player, args):
    """Display player's character statistics."""
    # Safely get race name
    if player.race and player.race in game.races:
        race_name = game.races[player.race].get('name', player.race.title())
    else:
        race_name = player.race.title() if player.race else "Unknown"
    
    # Safely get planet name (handle missing/corrupted data)
    if player.planet:
        if player.planet in game.planets:
            planet_name = game.planets[player.planet].get('name', player.planet.title())
        else:
            # Planet ID doesn't exist - might be corrupted data
            planet_name = f"{player.planet.title()} (Invalid)"
    else:
        planet_name = "Unknown"
    
    # Safely get starsign name
    if player.starsign and player.starsign in game.starsigns:
        starsign_name = game.starsigns[player.starsign].get('name', player.starsign.title())
    else:
        starsign_name = player.starsign.title() if player.starsign else "Unknown"
    
    # Get equipped weapon info
    equipped_weapon = None
    if "weapon" in player.equipped:
        weapon_id = player.equipped["weapon"]
        equipped_weapon = game.items.get(weapon_id)
    
    # Get race cultural traits
    race_traits = ""
    if player.race and player.race in game.races and "cultural_traits" in game.races[player.race]:
        race_traits = ", ".join(game.races[player.race]["cultural_traits"])
        
    # Get planet theme
    planet_theme = ""
    if player.planet and player.planet in game.planets and "theme" in game.planets[player.planet]:
        planet_theme = game.planets[player.planet]["theme"]
        
    # Get starsign theme
    starsign_theme = ""
    if player.starsign and player.starsign in game.starsigns and "theme" in game.starsigns[player.starsign]:
        starsign_theme = game.starsigns[player.starsign]["theme"]
        
    # Get fated mark description
    fated_mark_desc = ""
    if player.starsign and player.starsign in game.starsigns and "fated_mark" in game.starsigns[player.starsign]:
        fated_mark = game.starsigns[player.starsign]["fated_mark"]
        if "description" in fated_mark:
            fated_mark_desc = fated_mark["description"]
    
    header_text = f"{player.name}'s Character Sheet"
    stats_text = f"""
{game.format_header(header_text)}
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
        stats_text += f"\n{game.format_header('Fated Mark:')}"
        stats_text += f"{fated_mark_desc}"
        
    game.send_to_player(player, stats_text)


def skills_command(game, player, args):
    """Show player's skills and levels"""
    if player.race and player.race in game.races:
        race_name = game.races[player.race].get('name', player.race.title())
    else:
        race_name = player.race.title() if player.race else "Unknown"
    header_text = f"{player.name}'s Skills"
    skills_text = f"\n{game.format_header(header_text)}\n"
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
        
    game.send_to_player(player, skills_text.strip())


def maneuvers_command(game, player, args):
    """Show player's known and active maneuvers"""
    header_text = f"{player.name}'s Maneuvers"
    maneuvers_text = f"\n{game.format_header(header_text)}\n"
    maneuvers_text += f"Active: {len(player.active_maneuvers)}/{player.get_max_maneuvers()}\n\n"
    
    maneuvers_text += game.format_header("Known Maneuvers:") + "\n"
    for maneuver_id in player.known_maneuvers:
        if maneuver_id in game.maneuvers:
            maneuver = game.maneuvers[maneuver_id]
            status = "ACTIVE" if maneuver_id in player.active_maneuvers else "INACTIVE"
            status_formatted = game.format_success(status) if status == "ACTIVE" else game.format_error(status)
            maneuvers_text += f"  {maneuver['name']} {game.format_brackets(status_formatted)}\n"
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
    for maneuver_id, maneuver in game.maneuvers.items():
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
            
    game.send_to_player(player, maneuvers_text.strip())


def quests_command(game, player, args):
    """Show player's active quests"""
    if not game.quest_manager:
        game.send_to_player(player, "Quest system not available.")
        return
    
    quests = game.quest_manager.get_player_quests(player.name)
    if not quests:
        game.send_to_player(player, "You have no active quests.")
        return
    
    output = f"\n{game.format_header('Active Quests')}\n"
    for quest in quests:
        if quest.completed:
            output += f"{game.format_success(f'[COMPLETE] {quest.name}')}\n"
        else:
            output += f"{game.format_header(quest.name)}\n"
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
    
    game.send_to_player(player, output)


def quest_command(game, player, args):
    """Quest management commands"""
    if not game.quest_manager:
        game.send_to_player(player, "Quest system not available.")
        return
    
    if not args:
        game.send_to_player(player, "Usage: quest <list|accept|complete> [quest_id]")
        return
    
    subcmd = args[0].lower()
    
    if subcmd == "list":
        # List available quests (would need quest givers/NPCs)
        game.send_to_player(player, "Available quests feature coming soon.")
    elif subcmd == "accept" and len(args) > 1:
        quest_id = args[1]
        if game.quest_manager.assign_quest(player.name, quest_id):
            game.send_to_player(player, f"Quest '{quest_id}' accepted!")
        else:
            game.send_to_player(player, f"Quest '{quest_id}' not found or already accepted.")
    elif subcmd == "complete":
        # Show completed quests
        quests = game.quest_manager.get_player_quests(player.name)
        completed = [q for q in quests if q.completed]
        if completed:
            output = f"\n{game.format_header('Completed Quests')}\n"
            for quest in completed:
                output += f"- {quest.name}\n"
            game.send_to_player(player, output)
        else:
            game.send_to_player(player, "You have no completed quests.")


def time_command(game, player, args):
    """Display current world time"""
    if not game.world_time:
        game.send_to_player(player, "Time system is not available.")
        return
    
    include_exact = "exact" in args or "precise" in args
    time_string = game.world_time.get_time_string(include_exact=include_exact)
    game.send_to_player(player, time_string)


def set_time_command(game, player, args):
    """Set world time (admin command)"""
    if not game.world_time:
        game.send_to_player(player, "Time system is not available.")
        return
    
    if len(args) < 1:
        game.send_to_player(player, "Usage: set_time <day> <hour> [minute] or set_time <world_seconds>")
        return
    
    try:
        if len(args) == 1:
            # Set by world_seconds
            world_seconds = int(args[0])
            game.world_time.set_world_seconds(world_seconds)
            game.save_world_time()
            game.send_to_player(player, f"World time set to {world_seconds} seconds (Day {game.world_time.get_day_number()}, {game.world_time.get_hour():02d}:{game.world_time.get_minute():02d})")
        else:
            # Set by day, hour, minute
            day = int(args[0])
            hour = int(args[1])
            minute = int(args[2]) if len(args) > 2 else 0
            
            if not (0 <= hour < 24 and 0 <= minute < 60):
                game.send_to_player(player, "Invalid time. Hour must be 0-23, minute must be 0-59.")
                return
            
            world_seconds = day * 86400 + hour * 3600 + minute * 60
            game.world_time.set_world_seconds(world_seconds)
            game.save_world_time()
            game.send_to_player(player, f"World time set to Day {day}, {hour:02d}:{minute:02d}")
        
        if game.logger:
            game.logger.log_admin_action(player.name, "SET_TIME", f"Time: {args}")
    except ValueError:
        game.send_to_player(player, "Invalid time format. Use numbers only.")


def inspect_command(game, player, args):
    """Inspect an item to see detailed stats"""
    if not args:
        game.send_to_player(player, "Inspect what? Usage: inspect <item>")
        return
    
    item_name = " ".join(args).lower()
    
    # Check inventory first
    item = None
    for item_id in player.inventory:
        inv_item = game.items.get(item_id)
        if inv_item and item_name in inv_item.name.lower():
            item = inv_item
            break
    
    # Check room if not in inventory
    if not item:
        room = game.get_room(player.room_id)
        if room:
            for item_id in room.items:
                room_item = game.items.get(item_id)
                if room_item and item_name in room_item.name.lower():
                    item = room_item
                    break
    
    if not item:
        game.send_to_player(player, f"You don't see '{item_name}' here or in your inventory.")
        return
    
    # Show item details
    output = f"\n{game.format_header(item.name)}\n"
    output += f"{item.description}\n"
    output += f"Type: {item.item_type}\n"
    output += f"Value: {item.value} gold\n"
    
    # Show weapon stats if it's a weapon
    if item.is_weapon():
        output += f"\n{game.format_header('Weapon Stats')}\n"
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
            modifier = game.weapon_modifiers.get(item.weapon_modifier_id)
            if modifier:
                output += f"Modifier: {modifier['name']} - {modifier.get('notes', '')}\n"
    
    game.send_to_player(player, output)
