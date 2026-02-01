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
        # Check interactables with talk->travel (e.g. Old Lorek's skiff)
        interactables = getattr(room, "interactables", []) or []
        full_input = " ".join(args).lower()
        for obj in interactables:
            talk_cfg = (obj.get("actions") or {}).get("talk")
            if not isinstance(talk_cfg, dict):
                continue
            result = talk_cfg.get("result") or {}
            travel_to = result.get("travel_to_room_id")
            if not travel_to:
                continue
            required_flag = result.get("required_flag")
            if required_flag and not getattr(player, "has_flag", lambda n: False)(required_flag):
                fail_text = result.get("required_fail_text") or "You can't do that yet."
                game.send_to_player(player, fail_text)
                return
            keywords = (obj.get("keywords") or []) + [obj.get("name", "")]
            if not any(k and (full_input in str(k).lower() or str(k).lower() in full_input) for k in keywords):
                continue
            # Optional: require one of talk.keywords in input
            req_keywords = talk_cfg.get("keywords") or []
            if req_keywords and not any(kw in full_input for kw in req_keywords):
                continue
            target_room = game.get_room(travel_to)
            if not target_room:
                game.send_to_player(player, "That doesn't seem to go anywhere right now.")
                return
            old_room_id = player.room_id
            old_room = game.get_room(old_room_id)
            if old_room:
                old_room.players.discard(player.name)
            player.room_id = travel_to
            target_room.players.add(player.name)
            msg = talk_cfg.get("success_text") or "You travel to another place."
            game.send_to_player(player, game.format_success(msg))
            game.broadcast_to_room(old_room_id, f"{player.name} leaves.", player.name)
            game.broadcast_to_room(travel_to, f"{player.name} arrives.", player.name)
            try:
                from commands.movement import look_command
                look_command(game, player, [])
            except ImportError:
                if hasattr(game, "look_command"):
                    game.look_command(player, [])
            return
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
            raw = npc.keywords[matched_key]
            if isinstance(raw, dict):
                response = raw.get("response", "")
                set_flag_name = raw.get("set_flag")
                if set_flag_name and hasattr(player, "set_flag"):
                    player.set_flag(set_flag_name)
                    if hasattr(game, "save_player_data"):
                        game.save_player_data(player)
            else:
                response = raw
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
