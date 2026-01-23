"""Shop and merchant interaction commands."""

def shop_list_command(game, player, args):
    """List items available in shop"""
    room = game.get_room(player.room_id)
    if not room:
        game.send_to_player(player, "You are in an unknown location.")
        return
    
    # Find merchant NPC
    present_npc_ids = set(room.npcs)
    if game.npc_scheduler:
        scheduled_npcs = game.npc_scheduler.get_present_npcs(room.room_id)
        present_npc_ids.update(scheduled_npcs)
    
    merchant = None
    for nid in present_npc_ids:
        n = game.npcs.get(nid)
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
        game.send_to_player(player, "There's no merchant here.")
        return
    
    # Check store hours
    if game.store_hours and room.room_id in game.store_hours.store_hours:
        if not game.store_hours.is_store_open(room.room_id):
            status = game.store_hours.get_store_status(room.room_id)
            game.send_to_player(player, f"The shop is {status.lower()}.")
            return
    
    # Get shop inventory
    shop_inventory = getattr(merchant, 'shop_inventory', [])
    if not shop_inventory:
        game.send_to_player(player, f"{merchant.name} has nothing for sale right now.")
        return
    
    # Get player's outlook with merchant
    outlook = game.get_npc_outlook(merchant, player.name)
    price_mod = game.get_price_modifier(outlook)
    
    output = f"\n{game.format_header(f'{merchant.name}\'s Goods')}\n"
    output += f"Outlook: {outlook} ({'Hostile' if outlook <= -50 else 'Unfriendly' if outlook <= -20 else 'Neutral' if outlook == 0 else 'Friendly' if outlook < 30 else 'Trusted'})\n\n"
    
    # Load shop items (from individual files or consolidated file)
    shop_items_data = game.load_shop_items()
    
    # Group items by category
    weapons = []
    armor = []
    tools = []
    consumables = []
    
    for item_id in shop_inventory:
        item_data = shop_items_data.get(item_id)
        if not item_data:
            # Try to get from regular items
            item = game.items.get(item_id)
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
        output += f"{game.format_header('Weapons:')}\n"
        for item in weapons:
            price_note = f" (was {item['base_price']})" if price_mod != 1.0 else ""
            output += f"  {item['name']} - {item['price']} coin{price_note}\n"
        output += "\n"
    
    if armor:
        output += f"{game.format_header('Armor & Gear:')}\n"
        for item in armor:
            price_note = f" (was {item['base_price']})" if price_mod != 1.0 else ""
            output += f"  {item['name']} - {item['price']} coin{price_note}\n"
        output += "\n"
    
    if tools:
        output += f"{game.format_header('Tools & Supplies:')}\n"
        for item in tools:
            price_note = f" (was {item['base_price']})" if price_mod != 1.0 else ""
            output += f"  {item['name']} - {item['price']} coin{price_note}\n"
        output += "\n"
    
    if consumables:
        output += f"{game.format_header('Consumables:')}\n"
        for item in consumables:
            price_note = f" (was {item['base_price']})" if price_mod != 1.0 else ""
            output += f"  {item['name']} - {item['price']} coin{price_note}\n"
        output += "\n"
    
    output += f"Use {game.format_command('buy <item>')} to purchase.\n"
    output += f"Use {game.format_command('sell <item>')} to sell your items.\n"
    
    game.send_to_player(player, output)


def buy_command(game, player, args):
    """Buy an item from a merchant"""
    if not args:
        game.send_to_player(player, "Buy what? Usage: buy <item>")
        return
    
    room = game.get_room(player.room_id)
    if not room:
        game.send_to_player(player, "You are in an unknown location.")
        return
    
    # Find merchant NPC
    present_npc_ids = set(room.npcs)
    if game.npc_scheduler:
        scheduled_npcs = game.npc_scheduler.get_present_npcs(room.room_id)
        present_npc_ids.update(scheduled_npcs)
    
    merchant = None
    for nid in present_npc_ids:
        n = game.npcs.get(nid)
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
        game.send_to_player(player, "There's no merchant here.")
        return
    
    # Check store hours
    if game.store_hours and room.room_id in game.store_hours.store_hours:
        if not game.store_hours.is_store_open(room.room_id):
            status = game.store_hours.get_store_status(room.room_id)
            game.send_to_player(player, f"The shop is {status.lower()}.")
            return
    
    # Check outlook - refuse service if very hostile
    outlook = game.get_npc_outlook(merchant, player.name)
    if outlook <= -50:
        game.send_to_player(player, f"{merchant.name} refuses to serve you. Your reputation here is too low.")
        return
    
    # Find item in shop inventory
    item_name = " ".join(args).lower()
    shop_inventory = getattr(merchant, 'shop_inventory', [])
    
    if not shop_inventory:
        game.send_to_player(player, f"{merchant.name} has nothing for sale right now.")
        return
    
    # Load shop items (from individual files or consolidated file)
    shop_items_data = game.load_shop_items()
    
    item_id = None
    item_data = None
    
    # Try exact match first (item_id)
    if item_name in shop_inventory:
        item_id = item_name
        item_data = shop_items_data.get(item_id)
        if not item_data:
            item = game.items.get(item_id)
            if item:
                item_data = item.to_dict()
    
    # If no exact match, try name matching
    if not item_id or not item_data:
        for sid in shop_inventory:
            data = shop_items_data.get(sid)
            if not data:
                item = game.items.get(sid)
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
                item = game.items.get(sid)
                if item:
                    data = item.to_dict()
            if data:
                available_items.append(data.get("name", sid))
        
        if available_items:
            game.send_to_player(player, f"{merchant.name} doesn't have '{item_name}'. Available items: {', '.join(available_items)}")
        else:
            game.send_to_player(player, f"{merchant.name} doesn't have that item. Use {game.format_command('list')} or {game.format_command('shop')} to see available items.")
        return
    
    # Calculate price
    base_price = item_data.get("value", 0)
    if base_price == 0:
        # Try to get price from item if value not set
        item_obj = game.items.get(item_id)
        if item_obj:
            base_price = getattr(item_obj, 'value', 0)
    
    if base_price == 0:
        game.send_to_player(player, f"Error: {item_data.get('name', 'Item')} has no price set.")
        return
        
    price_mod = game.get_price_modifier(outlook)
    final_price = int(base_price * price_mod)
    
    # Check if player has enough gold
    if player.gold < final_price:
        game.send_to_player(player, f"You need {final_price} coin to buy {item_data.get('name')}, but you only have {player.gold} coin.")
        return
    
    # Create item - import Item class
    from mud_server import Item
    item = Item(item_data.get("item_id"), item_data.get("name"), item_data.get("description", ""), item_data.get("item_type", "item"))
    item.from_dict(item_data)
    
    # If it's a weapon, create from template
    if item_data.get("weapon_template_id") and game.weapons:
        template_id = item_data.get("weapon_template_id")
        modifier_id = item_data.get("weapon_modifier_id")
        created_item = game.create_weapon_item(template_id, modifier_id, item_id)
        if created_item:
            item = created_item
            item.value = final_price  # Set value to final price
    
    # Add to player inventory
    player.inventory.append(item.item_id)
    game.items[item.item_id] = item
    player.gold -= final_price
    
    # Improve outlook slightly for purchase
    if not hasattr(merchant, 'outlooks'):
        merchant.outlooks = {}
    merchant.outlooks[player.name] = merchant.outlooks.get(player.name, 0) + 1
    
    game.send_to_player(player, f"You buy {item.name} for {final_price} coin from {merchant.name}.")
    game.broadcast_to_room(player.room_id, f"{player.name} buys something from {merchant.name}.", player.name)
    
    # Save world data
    game.save_world_data()


def sell_command(game, player, args):
    """Sell an item to a merchant"""
    if not args:
        game.send_to_player(player, "Sell what? Usage: sell <item>")
        return
    
    room = game.get_room(player.room_id)
    if not room:
        game.send_to_player(player, "You are in an unknown location.")
        return
    
    # Find merchant NPC
    present_npc_ids = set(room.npcs)
    if game.npc_scheduler:
        scheduled_npcs = game.npc_scheduler.get_present_npcs(room.room_id)
        present_npc_ids.update(scheduled_npcs)
    
    merchant = None
    for nid in present_npc_ids:
        n = game.npcs.get(nid)
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
        game.send_to_player(player, "There's no merchant here.")
        return
    
    # Check store hours
    if game.store_hours and room.room_id in game.store_hours.store_hours:
        if not game.store_hours.is_store_open(room.room_id):
            status = game.store_hours.get_store_status(room.room_id)
            game.send_to_player(player, f"The shop is {status.lower()}.")
            return
    
    # Find item in player inventory
    item_name = " ".join(args).lower()
    item_id = None
    item = None
    
    for iid in player.inventory:
        i = game.items.get(iid)
        if i and item_name in i.name.lower():
            item_id = iid
            item = i
            break
    
    if not item:
        game.send_to_player(player, "You don't have that item.")
        return
    
    # Calculate sell price (typically 50% of base value, modified by outlook)
    base_value = item.value if item.value > 0 else 10
    sell_price = int(base_value * 0.5)  # 50% of value
    
    # Apply outlook modifier
    outlook = game.get_npc_outlook(merchant, player.name)
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
    
    game.send_to_player(player, f"You sell {item.name} to {merchant.name} for {sell_price} coin.")
    game.broadcast_to_room(player.room_id, f"{player.name} sells something to {merchant.name}.", player.name)
    
    # Save world data
    game.save_world_data()


def repair_command(game, player, args):
    """Repair a weapon or armor"""
    if not args:
        game.send_to_player(player, "Repair what? Usage: repair <item>")
        return
    
    room = game.get_room(player.room_id)
    if not room:
        game.send_to_player(player, "You are in an unknown location.")
        return
    
    # Find merchant NPC with repair service
    present_npc_ids = set(room.npcs)
    if game.npc_scheduler:
        scheduled_npcs = game.npc_scheduler.get_present_npcs(room.room_id)
        present_npc_ids.update(scheduled_npcs)
    
    merchant = None
    for nid in present_npc_ids:
        n = game.npcs.get(nid)
        if n and hasattr(n, 'is_merchant') and n.is_merchant:
            # Check if they have repair keyword
            if hasattr(n, 'keywords') and n.keywords and "repairs" in n.keywords:
                merchant = n
                break
    
    if not merchant:
        game.send_to_player(player, "There's no one here who can repair items.")
        return
    
    # Find item in player inventory
    item_name = " ".join(args).lower()
    item_id = None
    item = None
    
    for iid in player.inventory:
        i = game.items.get(iid)
        if i and item_name in i.name.lower():
            item_id = iid
            item = i
            break
    
    if not item:
        game.send_to_player(player, "You don't have that item.")
        return
    
    # Check if item is repairable (weapon or armor)
    if not (item.is_weapon() or item.is_armor()):
        game.send_to_player(player, f"{item.name} cannot be repaired.")
        return
    
    # Calculate repair cost based on damage
    if item.is_weapon():
        current_dur = item.get_current_durability()
        max_dur = item.max_durability
        damage = max_dur - current_dur
        if damage == 0:
            game.send_to_player(player, f"{item.name} is already at full durability.")
            return
        repair_cost = 10 + (damage * 2)  # 10-25 coin range
    else:  # armor
        # For armor, assume similar durability system
        if hasattr(item, 'current_durability') and item.current_durability:
            current_dur = item.current_durability
            max_dur = getattr(item, 'max_durability', 50)
        else:
            # Assume full if no durability system
            game.send_to_player(player, f"{item.name} doesn't need repair.")
            return
        damage = max_dur - current_dur
        if damage == 0:
            game.send_to_player(player, f"{item.name} is already at full durability.")
            return
        repair_cost = 15 + (damage * 3)  # 15-30 coin range
    
    # Apply outlook modifier
    outlook = game.get_npc_outlook(merchant, player.name)
    price_mod = game.get_price_modifier(outlook)
    final_cost = int(repair_cost * price_mod)
    
    # Check if player has enough gold
    if player.gold < final_cost:
        game.send_to_player(player, f"Repair costs {final_cost} coin, but you only have {player.gold} coin.")
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
    
    game.send_to_player(player, f"{merchant.name} repairs your {item.name} for {final_cost} coin.")
    game.broadcast_to_room(player.room_id, f"{player.name} has {item.name} repaired by {merchant.name}.", player.name)
    
    # Save world data
    game.save_world_data()
