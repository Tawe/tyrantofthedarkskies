"""Movement and exploration commands."""

def look_command(game, player, args):
    """Look around the current room, at an NPC, or in a direction."""
    room = game.get_room(player.room_id)
    if not room:
        game.send_to_player(player, game.format_error("You are in an unknown location."))
        return
    
    # Handle "look <npc>" command
    if args:
        npc_name = " ".join(args).lower()
        
        # Check for scheduled NPCs
        present_npc_ids = set(room.npcs)
        if game.npc_scheduler:
            scheduled_npcs = game.npc_scheduler.get_present_npcs(room.room_id)
            present_npc_ids.update(scheduled_npcs)
        
        # Try to find NPC
        npc = None
        for npc_id in present_npc_ids:
            n = game.npcs.get(npc_id)
            if n and npc_name in n.name.lower():
                npc = n
                break
        
        if npc:
            look_npc(game, player, npc)
            return

        # Try interactable (e.g. look barrel)
        interactables = getattr(room, "interactables", []) or []
        target = " ".join(args).lower()
        for obj in interactables:
            keywords = (obj.get("keywords") or []) + [obj.get("name", "")]
            if any(target in str(k).lower() or str(k).lower() in target for k in keywords):
                text = obj.get("examine_text", "You see nothing special.")
                output = f"\n{game.format_header(obj.get('name', 'Object').title())}\n{text}\n"
                actions = []
                if obj.get("actions", {}).get("examine"):
                    actions.append(f"examine {obj.get('name', 'object')}")
                take_cfg = obj.get("actions", {}).get("take")
                if isinstance(take_cfg, dict) and take_cfg.get("gives_item"):
                    actions.append(f"take stick")
                if actions:
                    output += f"\nActions: {', '.join(actions)}"
                game.send_to_player(player, output.strip())
                return
        
        # Handle "look <direction>" command
        direction = args[0].lower()
        look_direction(game, player, room, direction)
        return
        
    output = f"\n{game.format_header(room.name)}\n{room.description}\n"
    # Append in-world hint when spawned creatures (e.g. random encounter) are present
    if getattr(game, 'runtime_state', None):
        for inst in game.runtime_state.get_entities_in_room(room.room_id):
            if inst.get("entity_type") in ("creature", "npc"):
                output += "\n\nCreatures stir here.\n"
                break
    # Regional weather overlay (docs/weather_system.md); indoor = no overlay
    exposure = getattr(room, "weather_exposure", None) or "outdoor"
    if exposure != "indoor" and getattr(game, "get_weather_overlay", None):
        overlay = game.get_weather_overlay(getattr(room, "region_id", None), exposure)
        if overlay:
            output += f"\n\n{overlay}\n"
    
    if room.exits:
        exits = []
        for direction in room.exits.keys():
            exits.append(game.format_exit(direction))
        output += f"\nExits: {' '.join(exits)}"
        
    other_players = [p for p in room.players if p != player.name]
    if other_players:
        player_list = ", ".join(other_players)
        output += f"\nPlayers here: {player_list}"
        
    # Check for scheduled NPCs (lazy presence)
    present_npc_ids = set(room.npcs)  # Start with static NPCs
    if game.npc_scheduler:
        # Check if NPCs can change schedule (not in combat, transaction, etc.)
        def can_change_schedule(npc_id):
            npc = game.npcs.get(npc_id)
            if not npc:
                return True
            # Check if NPC is in combat
            if game.combat_manager:
                combat = game.combat_manager.get_combat_state(room.room_id)
                if combat and combat.is_active:
                    if npc_id in [name for name in combat.combatants.keys()]:
                        return False  # In combat, defer schedule change
            # Note: Additional checks for transactions, dialogue, etc. can be added here
            return True
        
        scheduled_npcs = game.npc_scheduler.get_present_npcs(room.room_id, can_change_schedule)
        present_npc_ids.update(scheduled_npcs)
    
    if present_npc_ids:
        npcs_here = []
        for npc_id in present_npc_ids:
            npc = game.npcs.get(npc_id)
            if npc:
                npcs_here.append(game.format_npc(npc.name))
        if npcs_here:
            output += f"\nNPCs here: {', '.join(npcs_here)}"
            
    if room.items:
        items_here = []
        for item_id in room.items:
            item = game.items.get(item_id)
            if item:
                items_here.append(game.format_item(item.name))
        output += f"\nItems here: {', '.join(items_here)}"
        
    # Show room flags if present
    if room.flags:
        flags_text = ", ".join(room.flags)
        output += f"\nRoom flags: {game.format_brackets(flags_text, 'orange')}"
        
    # Show combat tags if present
    if room.combat_tags:
        tags_text = ", ".join(room.combat_tags)
        output += f"\nCombat environment: {game.format_brackets(tags_text, 'yellow')}"
        
    # Show combat status if active
    if game.combat_manager:
        combat = game.combat_manager.get_combat_state(player.room_id)
        if combat and combat.is_active:
            output += f"\n{game.format_header('COMBAT IN PROGRESS')}"
            combatants = list(combat.combatants.keys())
            output += f"Combatants: {', '.join(combatants)}"
            if player.name not in combatants:
                output += f"\nYou are observing. Use {game.format_command('join combat')} to participate."
            
    game.send_to_player(player, output)


def look_npc(game, player, npc):
    """Look at an NPC to see detailed information"""
    output = f"\n{game.format_header(npc.name)}\n"
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
        output += f"Role: {game.format_brackets('Merchant', 'yellow')}\n"
        if game.store_hours:
            room = game.get_room(player.room_id)
            if room and room.room_id in game.store_hours.store_hours:
                store_status = game.store_hours.get_store_status(room.room_id)
                status_color = "green" if store_status == "Open" else "yellow"
                output += f"Shop: {game.format_brackets(store_status, status_color)}\n"
        
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
            item = game.items.get(item_id)
            if item:
                equipped_items.append(f"{slot}: {item.name}")
        if equipped_items:
            output += f"Equipped: {', '.join(equipped_items)}\n"
        
    # Show dialogue hint
    if hasattr(npc, 'dialogue') and npc.dialogue:
        output += f"\n{game.format_header('Greeting:')}\n"
        output += f"{npc.dialogue[0]}\n"
        
    # Show available keywords if merchant
    if hasattr(npc, 'is_merchant') and npc.is_merchant:
        output += f"\n{game.format_header('Available Actions:')}\n"
        output += f"Use {game.format_command('talk jalia buy')} or {game.format_command('talk jalia shop')} to see items for sale\n"
        output += f"Use {game.format_command('talk jalia sell')} to sell items\n"
        output += f"Use {game.format_command('talk jalia repair')} or {game.format_command('talk jalia repairs')} for repair services\n"
        output += f"Use {game.format_command('list')} or {game.format_command('shop')} to browse inventory\n"
        
    game.send_to_player(player, output)


def look_direction(game, player, room, direction):
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
        available = ", ".join([game.format_exit(d) for d in room.exits.keys()])
        game.send_to_player(player, game.format_error(f"You cannot look {game.format_brackets(direction)}. Available directions: {available}"))
        return
    
    exit_data = room.exits[direction]
    target_room_id = game.get_exit_target(exit_data)
    door_info = game.get_exit_door(exit_data)
    
    # Check if there's a door or obstacle blocking the view
    if door_info:
        if isinstance(door_info, str):
            # Simple string description
            game.send_to_player(player, f"You look {game.format_exit(direction)}, but {door_info} blocks your view.")
        elif isinstance(door_info, dict):
            # Detailed door/obstacle info
            door_desc = door_info.get("description", "something blocks your view")
            door_name = door_info.get("name", "A door")
            game.send_to_player(player, f"You look {game.format_exit(direction)}, but {door_name} blocks your view. {door_desc}")
        else:
            game.send_to_player(player, f"You look {game.format_exit(direction)}, but something blocks your view.")
        return
    
    # No door/obstacle - show the adjacent room
    if not target_room_id:
        game.send_to_player(player, game.format_error("That direction leads to an unknown place."))
        return
    
    target_room = game.get_room(target_room_id)
    if not target_room:
        game.send_to_player(player, game.format_error("That direction leads to an unknown place."))
        return
    
    # Show what can be seen in that direction
    output = f"\n{game.format_header(f'Looking {game.format_exit(direction)}')}\n"
    output += f"You can see: {game.format_header(target_room.name)}\n"
    output += f"{target_room.description}\n"
    
    # Show visible players/NPCs in the adjacent room
    if target_room.players:
        visible_players = [p for p in target_room.players if p != player.name]
        if visible_players:
            output += f"\nYou can see {', '.join(visible_players)} there.\n"
        
    if target_room.npcs:
        npcs_visible = []
        for npc_id in target_room.npcs:
            npc = game.npcs.get(npc_id)
            if npc:
                npcs_visible.append(game.format_npc(npc.name))
        if npcs_visible:
            output += f"You can see {', '.join(npcs_visible)} there.\n"
        
    game.send_to_player(player, output)


def move_command(game, player, direction):
    """Move the player in a direction."""
    room = game.get_room(player.room_id)
    if not room:
        game.send_to_player(player, game.format_error("You are in an unknown location."))
        return
        
    if direction not in room.exits:
        available_exits = ", ".join([game.format_exit(d) for d in room.exits.keys()])
        game.send_to_player(player, game.format_error(f"You cannot go {game.format_brackets(direction)}. Available exits: {available_exits}"))
        return
        
    old_room_id = player.room_id
    # Handle both string and dict exit formats
    exit_data = room.exits[direction]
    new_room_id = game.get_exit_target(exit_data)
    new_room = game.get_room(new_room_id)
    
    if not new_room:
        game.send_to_player(player, game.format_error("That direction leads to an unknown place."))
        return
    
    # Check if target room is a shop that's currently closed
    if game.store_hours and new_room_id in game.store_hours.store_hours:
        if not game.store_hours.is_store_open(new_room_id):
            status = game.store_hours.get_store_status(new_room_id)
            game.send_to_player(player, game.format_error(f"The shop is {status.lower()}. You cannot enter while it's closed."))
            return
            
    room.players.discard(player.name)
    new_room.players.add(player.name)
    player.room_id = new_room_id
    
    # Exploration EXP reward (first time visiting a room)
    if new_room_id not in game.explored_rooms[player.name]:
        game.explored_rooms[player.name].add(new_room_id)
        exp_gain = 10  # Base exploration EXP
        player.experience += exp_gain
        game.send_to_player(player, game.format_success(f"You discover a new area! +{exp_gain} EXP"))
        
        # Update quest progress (explore room)
        if game.quest_manager:
            completed = game.quest_manager.update_quest_progress(
                player.name, "explore_room", new_room_id, 1
            )
            for quest in completed:
                player.experience += quest.exp_reward
                game.send_to_player(player, f"{game.format_header('Quest Complete!')}")
                game.send_to_player(player, f"Quest: {quest.name}")
                game.send_to_player(player, f"You gain {quest.exp_reward} EXP from quest completion!")
            
        game.check_level_up(player)
    
    game.broadcast_to_room(old_room_id, f"{player.name} leaves {direction}.", player.name)
    game.send_to_player(player, game.format_success(f"You move {game.format_exit(direction)}."))
    look_command(game, player, [])
    game.broadcast_to_room(new_room_id, f"{player.name} arrives.", player.name)
