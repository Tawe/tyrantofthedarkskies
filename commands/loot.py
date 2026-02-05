"""Loot and corpse commands (docs/loot_system.md).

- loot [all] [corpse]: list corpses, show contents, or take all from a corpse.
- take <item> from <corpse>: handled via handle_take_from_corpse() from get_command.
"""

import time


def can_loot_corpse(game, player, corpse_inst):
    """True if player is allowed to loot (ownership window or expired)."""
    ownership = corpse_inst.get("ownership") or {}
    if not ownership:
        return True
    now = time.time()
    expires_at = ownership.get("expires_at") or 0
    if now >= expires_at:
        return True
    allowed = ownership.get("allowed_player_ids") or []
    return player.name in allowed


def maybe_remove_empty_corpse(game, corpse_inst):
    """Remove corpse from world if it has no items and 0 coins."""
    loot = corpse_inst.get("loot") or {}
    if (loot.get("coins") or 0) > 0:
        return
    items = loot.get("items") or []
    if any((e.get("count") or 0) > 0 for e in items):
        return
    instance_id = corpse_inst.get("instance_id")
    if instance_id and game.runtime_state:
        game.runtime_state.remove_entity_from_world(instance_id, delete_instance=True)


def handle_take_from_corpse(game, player, room, part, source):
    """Handle 'take <part> from <source>' when source is a corpse. Returns True if handled."""
    if not part or not source or not game.runtime_state:
        return False
    for inst in game.runtime_state.get_entities_in_room(room.room_id):
        if inst.get("entity_type") != "corpse":
            continue
        corpse_name = (inst.get("name") or "").lower()
        if source not in corpse_name and corpse_name not in source:
            continue
        if not can_loot_corpse(game, player, inst):
            game.send_to_player(player, "You hesitate. This kill isn't yours to claim yet.")
            return True
        loot = inst.get("loot") or {}
        items_list = loot.get("items") or []
        for i, entry in enumerate(items_list):
            item_id = entry.get("item_id")
            item = game.items.get(item_id) if item_id else None
            if not item or part not in item.name.lower():
                continue
            count = entry.get("count", 1)
            if count <= 1:
                items_list.pop(i)
            else:
                entry["count"] = count - 1
            if not hasattr(player, "inventory"):
                player.inventory = []
            player.inventory.append(item_id)
            game.runtime_state.update_entity_instance(
                inst["instance_id"],
                loot={"rolled": True, "coins": loot.get("coins", 0), "items": items_list},
            )
            item_display = game.format_item(item.name)
            game.send_to_player(player, game.format_success(f"You take {item_display} from the corpse."))
            game.broadcast_to_room(player.room_id, f"{player.name} takes {item_display} from the corpse.", player.name)
            maybe_remove_empty_corpse(game, inst)
            return True
        if part in ("coin", "coins", "gold", "money") and loot.get("coins", 0) > 0:
            amount = loot["coins"]
            player.gold = getattr(player, "gold", 0) + amount
            game.runtime_state.update_entity_instance(
                inst["instance_id"],
                loot={"rolled": True, "coins": 0, "items": loot.get("items") or []},
            )
            game.send_to_player(player, game.format_success(f"You take {amount} coin from the corpse."))
            game.broadcast_to_room(player.room_id, f"{player.name} takes coin from the corpse.", player.name)
            maybe_remove_empty_corpse(game, inst)
            return True
        game.send_to_player(player, "You don't see that in the corpse.")
        return True
    return False


def loot_command(game, player, args):
    """Loot system (docs/loot_system.md): loot [all] [corpse] — list corpses, show contents, or take all."""
    room = game.get_room(player.room_id)
    if not room:
        game.send_to_player(player, "You are in an unknown location.")
        return
    corpses = []
    if game.runtime_state:
        for inst in game.runtime_state.get_entities_in_room(room.room_id):
            if inst.get("entity_type") == "corpse":
                corpses.append(inst)
    if not corpses:
        game.send_to_player(player, "There are no corpses here to loot.")
        return
    # loot all [corpse_name]
    if args and args[0].lower() == "all":
        corpse = None
        if len(args) > 1:
            # "loot all king" or "loot all drowned"
            target_name = " ".join(args[1:]).lower()
            for inst in corpses:
                name = (inst.get("name") or "").lower()
                if target_name in name or name in target_name:
                    corpse = inst
                    break
            if not corpse:
                game.send_to_player(player, f"You don't see a corpse matching '{target_name}' here.")
                return
        elif len(corpses) == 1:
            corpse = corpses[0]
        else:
            names = [inst.get("name", "a corpse") for inst in corpses]
            game.send_to_player(player, f"Which corpse? Try: loot all <name>. Corpses here: {', '.join(names)}")
            return
        if not can_loot_corpse(game, player, corpse):
            game.send_to_player(player, "You hesitate. This kill isn't yours to claim yet.")
            return
        loot = corpse.get("loot") or {}
        items_list = list(loot.get("items") or [])
        coins = loot.get("coins") or 0
        taken = []
        for entry in items_list:
            item_id = entry.get("item_id")
            count = entry.get("count", 1)
            item = game.items.get(item_id) if item_id else None
            if item:
                for _ in range(count):
                    player.inventory.append(item_id)
                taken.append(f"{item.name}" + (f" (x{count})" if count > 1 else ""))
        if coins > 0:
            player.gold = getattr(player, "gold", 0) + coins
            taken.append(f"{coins} coin")
        game.runtime_state.update_entity_instance(
            corpse["instance_id"], loot={"rolled": True, "coins": 0, "items": []}
        )
        maybe_remove_empty_corpse(game, {**corpse, "loot": {"coins": 0, "items": []}})
        if taken:
            game.send_to_player(player, game.format_success(f"You take {', '.join(taken)} from the corpse."))
            game.broadcast_to_room(player.room_id, f"{player.name} loots the corpse.", player.name)
        else:
            game.send_to_player(player, "The corpse is already empty.")
        return
    # loot <corpse> — show contents
    target = " ".join(args).lower() if args else ""
    if target:
        for inst in corpses:
            name = (inst.get("name") or "").lower()
            if target in name or name in target:
                if not can_loot_corpse(game, player, inst):
                    game.send_to_player(player, "You hesitate. This kill isn't yours to claim yet.")
                    return
                loot = inst.get("loot") or {}
                coins = loot.get("coins") or 0
                items_list = loot.get("items") or []
                lines = []
                if coins > 0:
                    lines.append(f"Coins: {coins}")
                if items_list:
                    item_parts = []
                    for entry in items_list:
                        item_id = entry.get("item_id")
                        count = entry.get("count", 1)
                        item = game.items.get(item_id) if item_id else None
                        name_str = item.name if item else item_id or "?"
                        item_parts.append(f"{name_str}" + (f" (x{count})" if count > 1 else ""))
                    lines.append("Items: " + ", ".join(item_parts))
                if not lines:
                    game.send_to_player(player, "The corpse is empty.")
                else:
                    game.send_to_player(
                        player,
                        game.format_header(inst.get("name", "Corpse")) + "\n" + "\n".join(lines),
                    )
                return
        game.send_to_player(player, "You don't see that corpse here.")
        return
    # loot — list corpses
    names = [inst.get("name", "a corpse") for inst in corpses]
    game.send_to_player(player, "Lootable corpses here: " + ", ".join(names) + ".")
