"""Inventory and item management commands."""

def inventory_command(game, player, args):
    """Display player's inventory."""
    if not player.inventory:
        game.send_to_player(player, "You are not carrying anything.")
        return
        
    output = game.format_header("You are carrying:") + "\n"
    for item_id in player.inventory:
        item = game.items.get(item_id)
        if item:
            item_name = game.format_item(item.name)
            equipped_mark = ""
            # Check if item is equipped
            for slot, eq_item_id in player.equipped.items():
                if eq_item_id == item_id:
                    equipped_mark = f" [{game.format_brackets('EQUIPPED', 'green')}]"
                    break
            
            output += f"- {item_name}{equipped_mark}: {item.description}"
            
            # Show weapon stats if it's a weapon
            if item.is_weapon():
                damage_min, damage_max = item.get_effective_damage()
                output += f"\n  Damage: {damage_min}-{damage_max} ({item.damage_type}), Crit: {int(item.get_effective_crit_chance() * 100)}%, Durability: {item.get_current_durability()}/{item.max_durability}"
            
            output += "\n"
            
    game.send_to_player(player, output.strip())


def get_command(game, player, args):
    """Pick up an item from the room."""
    if not args:
        game.send_to_player(player, "Get what?")
        return
        
    item_name = " ".join(args).lower()
    room = game.get_room(player.room_id)
    
    if not room:
        game.send_to_player(player, "You are in an unknown location.")
        return
    
    for item_id in room.items[:]:
        item = game.items.get(item_id)
        if item and item_name in item.name.lower():
            room.items.remove(item_id)
            player.inventory.append(item_id)
            item_display = game.format_item(item.name)
            game.send_to_player(player, game.format_success(f"You pick up {item_display}."))
            game.broadcast_to_room(player.room_id, f"{player.name} picks up {item_display}.", player.name)
            return
            
    game.send_to_player(player, "You don't see that here.")


def drop_command(game, player, args):
    """Drop an item from inventory."""
    if not args:
        game.send_to_player(player, "Drop what?")
        return
        
    item_name = " ".join(args).lower()
    room = game.get_room(player.room_id)
    
    if not room:
        game.send_to_player(player, "You are in an unknown location.")
        return
    
    for item_id in player.inventory[:]:
        item = game.items.get(item_id)
        if item and item_name in item.name.lower():
            player.inventory.remove(item_id)
            room.items.append(item_id)
            item_display = game.format_item(item.name)
            game.send_to_player(player, game.format_success(f"You drop {item_display}."))
            game.broadcast_to_room(player.room_id, f"{player.name} drops {item_display}.", player.name)
            return
            
    game.send_to_player(player, "You don't have that.")


def use_command(game, player, args):
    """Use a consumable item."""
    if not args:
        game.send_to_player(player, "Use what?")
        return
        
    item_name = " ".join(args).lower()
    
    for item_id in player.inventory[:]:
        item = game.items.get(item_id)
        if item and item_name in item.name.lower():
            if item.item_type == "consumable":
                if item.item_id == "potion":
                    heal_amount = 30
                    player.health = min(player.max_health, player.health + heal_amount)
                    player.inventory.remove(item_id)
                    game.send_to_player(player, f"You drink the potion and heal {heal_amount} health.")
                    game.broadcast_to_room(player.room_id, 
                                          f"{player.name} drinks a health potion.", player.name)
                    return
            else:
                game.send_to_player(player, "You can't use that item.")
                return
                
    game.send_to_player(player, "You don't have that.")


def equip_command(game, player, args):
    """Equip a weapon or armor"""
    if not args:
        game.send_to_player(player, "Equip what? Usage: equip <slot> <item> or equip <item>")
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
        game.send_to_player(player, "Equip what? Usage: equip <slot> <item> or equip <item>")
        return
    
    # Find item in inventory
    item_id = None
    item = None
    for inv_item_id in player.inventory:
        inv_item = game.items.get(inv_item_id)
        if inv_item and item_name in inv_item.name.lower():
            item_id = inv_item_id
            item = inv_item
            break
    
    if not item:
        game.send_to_player(player, f"You don't have '{item_name}' in your inventory.")
        return
    
    # Check if item is appropriate for slot
    if slot == "weapon":
        if not item.is_weapon():
            game.send_to_player(player, f"{item.name} is not a weapon.")
            return
        
        # Check hands requirement
        if item.hands == 2:
            # Two-handed weapon - unequip shield/offhand if equipped
            if "offhand" in player.equipped:
                old_offhand = player.equipped["offhand"]
                old_offhand_item = game.items.get(old_offhand)
                old_offhand_name = old_offhand_item.name if old_offhand_item else "item"
                game.send_to_player(player, f"You unequip your {old_offhand_name} to wield {item.name}.")
                del player.equipped["offhand"]
        
        # Unequip old weapon if any
        if "weapon" in player.equipped:
            old_weapon_id = player.equipped["weapon"]
            old_weapon = game.items.get(old_weapon_id)
            if old_weapon:
                game.send_to_player(player, f"You unequip your {old_weapon.name}.")
        
        player.equipped["weapon"] = item_id
        game.send_to_player(player, f"You equip {item.name}.")
        
        # Show weapon stats
        damage_min, damage_max = item.get_effective_damage()
        game.send_to_player(player, f"  Damage: {damage_min}-{damage_max} ({item.damage_type})")
        game.send_to_player(player, f"  Critical: {int(item.get_effective_crit_chance() * 100)}%")
        game.send_to_player(player, f"  Durability: {item.get_current_durability()}/{item.max_durability}")
    else:
        game.send_to_player(player, f"Equipping to '{slot}' slot is not yet implemented.")


def unequip_command(game, player, args):
    """Unequip a weapon or armor"""
    if not args:
        game.send_to_player(player, "Unequip what? Usage: unequip <slot>")
        return
    
    slot = args[0].lower()
    
    if slot not in player.equipped:
        game.send_to_player(player, f"You don't have anything equipped in your {slot} slot.")
        return
    
    item_id = player.equipped[slot]
    item = game.items.get(item_id)
    
    if item:
        del player.equipped[slot]
        game.send_to_player(player, f"You unequip your {item.name}.")
    else:
        del player.equipped[slot]
        game.send_to_player(player, f"You unequip your {slot}.")
