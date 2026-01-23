"""Social and communication commands."""

def say_command(game, player, args):
    """Say something to others in the room."""
    if not args:
        game.send_to_player(player, "Say what?")
        return
        
    message = " ".join(args)
    game.broadcast_to_room(player.room_id, f"{player.name} says: {message}")


def who_command(game, player, args):
    """Show online players. Only shows names, never IP addresses or other sensitive data."""
    with game.player_lock:
        online_players = [name for name, p in game.players.items() if p.is_logged_in]
        if online_players:
            game.send_to_player(player, f"Players online: {', '.join(online_players)}")
        else:
            game.send_to_player(player, "No other players are online.")


def talk_command(game, player, args):
    """Talk to an NPC using keyword-based dialogue"""
    if not args:
        game.send_to_player(player, "Talk to whom? Usage: talk <npc> <keyword>")
        return
    
    # Find NPC in room
    room = game.get_room(player.room_id)
    if not room:
        game.send_to_player(player, "You are in an unknown location.")
        return
    
    # Check for scheduled NPCs
    present_npc_ids = set(room.npcs)
    if game.npc_scheduler:
        scheduled_npcs = game.npc_scheduler.get_present_npcs(room.room_id)
        present_npc_ids.update(scheduled_npcs)
    
    # Find NPC by name
    npc_name = args[0].lower()
    npc = None
    npc_id = None
    
    for nid in present_npc_ids:
        n = game.npcs.get(nid)
        if n and npc_name in n.name.lower():
            npc = n
            npc_id = nid
            break
    
    if not npc:
        game.send_to_player(player, f"You don't see {npc_name} here.")
        return
    
    # Get keyword (rest of args)
    if len(args) < 2:
        # Show greeting/dialogue
        if hasattr(npc, 'dialogue') and npc.dialogue:
            greeting = npc.dialogue[0] if npc.dialogue else f"{npc.name} looks at you expectantly."
            game.send_to_player(player, f"{npc.name} says: \"{greeting}\"")
        else:
            game.send_to_player(player, f"{npc.name} looks at you expectantly.")
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
            game.send_to_player(player, f"{npc.name} says: \"{response}\"")
            game.broadcast_to_room(player.room_id, f"{player.name} talks with {npc.name}.", player.name)
            
            # Special handling for certain keywords
            if hasattr(npc, 'is_merchant') and npc.is_merchant:
                if matched_key in ["goods", "buy", "shop"]:
                    game.send_to_player(player, f"\n{game.format_header('Shop Interface')}")
                    game.send_to_player(player, f"Use {game.format_command('list')} or {game.format_command('shop')} to see available items.")
                    game.send_to_player(player, f"Use {game.format_command('buy <item>')} to purchase items.")
                elif matched_key == "sell":
                    game.send_to_player(player, f"\n{game.format_header('Selling Items')}")
                    game.send_to_player(player, f"Use {game.format_command('sell <item>')} to sell items from your inventory.")
                    game.send_to_player(player, f"I'll give you a fair price based on the item's value and our relationship.")
                elif matched_key in ["repair", "repairs"]:
                    game.send_to_player(player, f"\n{game.format_header('Repair Service')}")
                    game.send_to_player(player, f"Use {game.format_command('repair <item>')} to repair weapons or armor.")
                    game.send_to_player(player, f"Cost depends on the damage. I can fix most basic gear.")
            
            return
    
    # No keyword match
    game.send_to_player(player, f"{npc.name} doesn't seem to respond to that.")
