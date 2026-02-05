"""Interaction commands for the MUD server.

Commands for interacting with objects in the world: dig, etc.
"""

import random
import time


def dig_command(game, player, args):
    """Dig at an interactable that supports the dig action.

    Requires:
    - A valid dig target (interactable with dig action)
    - Equipped item with the required tag (usually 'shovel')
    - Passes an attribute check (usually Physical)
    """
    room = game.get_room(player.room_id)
    if not room:
        game.send_to_player(player, game.format_error("You are in an unknown location."))
        return

    interactables = getattr(room, "interactables", []) or []
    dig_configs = []

    for obj in interactables:
        actions = obj.get("actions") or {}
        dig_cfg = actions.get("dig") if isinstance(actions.get("dig"), dict) else None
        if not dig_cfg:
            continue
        keywords = (obj.get("keywords") or []) + [obj.get("name", "")]
        if args:
            target = " ".join(args).lower()
            if not any(target in str(k).lower() or str(k).lower() in target for k in keywords):
                continue
        dig_configs.append((obj, dig_cfg))

    if not dig_configs:
        if args:
            game.send_to_player(player, game.format_error("You can't dig there."))
        else:
            game.send_to_player(player, game.format_error("Dig what? Try 'dig <thing>'."))
        return

    if len(dig_configs) > 1:
        names = [c[0].get("name", c[0].get("object_id", "?")) for c in dig_configs]
        game.send_to_player(player, f"Dig which? {' '.join(f'[{n}]' for n in names)}")
        return

    obj, dig_cfg = dig_configs[0]
    key = obj.get("object_id", "?")

    # Check per-player limit
    state = getattr(player, "interactable_searches", None) or {}
    if not isinstance(state, dict):
        state = {}
    # Use a separate namespace for dig actions
    dig_key = f"dig_{key}"
    entry = state.get(dig_key, {"count": 0, "last_at": 0})
    limit = dig_cfg.get("limit_per_player")

    if limit is not None and entry.get("count", 0) >= limit:
        game.send_to_player(player, dig_cfg.get("already_done_text") or "You've already dug here.")
        return

    # Check if player has the required tool equipped
    required_tag = dig_cfg.get("requires_equipped_tag")
    if required_tag:
        has_tool = False
        equipped = getattr(player, "equipped", {}) or {}
        for slot, item_id in equipped.items():
            if item_id:
                item = game.items.get(item_id)
                if item:
                    item_tags = getattr(item, "tags", []) or []
                    if required_tag in item_tags:
                        has_tool = True
                        break

        if not has_tool:
            no_tool_text = dig_cfg.get("no_tool_text") or f"You need a {required_tag} equipped to dig here."
            game.send_to_player(player, no_tool_text)
            return

    # Perform attribute check
    attribute = dig_cfg.get("attribute", "physical")
    difficulty = dig_cfg.get("difficulty", 10)

    # Roll attribute check: attribute * 5 gives base chance, roll d100
    attr_value = player.attributes.get(attribute, 10)
    base_chance = attr_value * 5  # 10 attr = 50%, 12 attr = 60%, etc.

    # Apply shaken modifier if player recently died
    shaken_mod = 0
    if hasattr(game, "_skill_check_modifier"):
        shaken_mod = game._skill_check_modifier(player) * 5  # Convert to percentage

    effective_chance = base_chance - difficulty + shaken_mod
    effective_chance = max(5, min(95, effective_chance))  # Clamp between 5-95%

    roll = random.randint(1, 100)
    success = roll <= effective_chance

    if success:
        # Update state
        state[dig_key] = {"count": entry.get("count", 0) + 1, "last_at": time.time()}
        player.interactable_searches = state

        success_block = dig_cfg.get("success") or {}
        if isinstance(success_block, str):
            success_block = {"success_text": success_block}

        # Give item if specified
        gives_item = success_block.get("gives_item")
        if gives_item and gives_item in game.items:
            player.inventory.append(gives_item)
            if hasattr(game, "save_player_data"):
                game.save_player_data(player)
            item = game.items.get(gives_item)
            item_display = game.format_item(item.name) if item else gives_item
            game.send_to_player(player, game.format_success(success_block.get("success_text") or f"You dig up {item_display}."))
            game.broadcast_to_room(player.room_id, f"{player.name} digs something up from the ground.", player.name)
        elif gives_item:
            # Item specified but not found
            print(f"[dig] Warning: Item '{gives_item}' not found in items registry")
            game.send_to_player(player, game.format_success(success_block.get("success_text") or "You dig something up, but it crumbles to dust."))
        else:
            # Set flag if specified
            set_flag_name = success_block.get("set_flag")
            if set_flag_name and hasattr(player, "set_flag"):
                player.set_flag(set_flag_name)
                if hasattr(game, "save_player_data"):
                    game.save_player_data(player)
            msg = success_block.get("success_text") or "You dig successfully."
            game.send_to_player(player, game.format_success(msg))
    else:
        fail_text = dig_cfg.get("fail_text") or "You dig, but find nothing."
        game.send_to_player(player, fail_text)
