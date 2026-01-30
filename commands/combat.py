"""Combat-related commands."""

import random


class _InstanceCombatTarget:
    """Wrapper so runtime entity instances can be used as combat targets (same interface as NPC)."""
    def __init__(self, inst, template_npc):
        self._template = template_npc
        self._inst = inst
        self.name = template_npc.name if template_npc else inst.get("template_id", "Unknown")
        self.health = inst.get("hp_current", 0)
        self.max_health = inst.get("hp_max", 10)
        self.instance_id = inst.get("instance_id")
        self.template_id = inst.get("template_id")
        self.loot_table = getattr(template_npc, "loot_table", []) if template_npc else []
        self.npc_id = self.instance_id
        self.equipped = getattr(template_npc, "equipped", {}) if template_npc else {}
    def get_tier(self):
        return getattr(self._template, "get_tier", lambda: "Low")() if self._template else "Low"
    def get_attribute_bonus(self, attribute):
        return getattr(self._template, "get_attribute_bonus", lambda _: 0)(attribute) if self._template else 0
    def roll_skill_check(self, skill_name, difficulty_mod=0):
        return getattr(self._template, "roll_skill_check", lambda _s, _m=0: {"result": "success", "roll": random.randint(1, 100), "effective_skill": 50})(skill_name, difficulty_mod) if self._template else {"result": "success", "roll": random.randint(1, 100), "effective_skill": 50}
    @property
    def exp_value(self):
        return getattr(self._template, "exp_value", 0) if self._template else 0


def attack_command(game, player, args):
    """Attack a target (NPC or player)."""
    if not args:
        game.send_to_player(player, "Attack whom?")
        return

    target_name = " ".join(args).lower()
    room = game.get_room(player.room_id)
    
    if not room:
        return
    
    # Check for player target first (PvP)
    target_player = None
    for pname, p in game.players.items():
        if pname != player.name and pname.lower() == target_name and p.room_id == player.room_id:
            target_player = p
            break
    
    # Check for NPC target
    target_npc = None
    for npc_id in room.npcs:
        npc = game.npcs.get(npc_id)
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
            
    # Resolve runtime entity instance (spawned creature) if no template NPC matched
    if not target_npc and not target_player and game.runtime_state:
        for inst in game.runtime_state.get_entities_in_room(room.room_id):
            if inst.get("entity_type") not in ("creature", "npc"):
                continue
            template_id = inst.get("template_id")
            template_npc = game.npcs.get(template_id) if template_id else None
            display_name = (template_npc.name if template_npc else template_id or "").lower()
            if target_name in display_name:
                target_npc = _InstanceCombatTarget(inst, template_npc)
                break
    if not target_npc and not target_player:
        game.send_to_player(player, "You don't see that target here or it's not hostile.")
        return

    # Use combat system if available, otherwise use simple combat
    if game.combat_manager and (target_npc or target_player):
        target = target_npc if target_npc else target_player
        target_display = target_npc.name if target_npc else target_player.name

        # Start or join combat
        combat = game.combat_manager.get_combat_state(player.room_id)
        if not combat or not combat.is_active:
            # Start new combat (also sets initial target & engaged state)
            game.combat_manager.start_combat(player.room_id, player.name, player, target_display, target)
            combat = game.combat_manager.get_combat_state(player.room_id)
        elif player.name not in combat.combatants:
            # Join existing combat
            game.combat_manager.join_combat(player.room_id, player.name, player, target_display)

        # At this point the player is a combatant; manage autoattack targeting.
        combatant_info = combat.combatants.get(player.name)
        if combatant_info:
            current_target = combatant_info.get("target")
            combatant_info["state"] = "Engaged"

            # Already attacking this target → do not force another immediate attack.
            if current_target and current_target.lower() == target_display.lower():
                game.send_to_player(player, f"You are already attacking {target_display}.")
                return

            # Switching targets mid-combat.
            if current_target and current_target.lower() != target_display.lower():
                combatant_info["target"] = target_display
                game.send_to_player(player, f"You turn your focus to {target_display}.")
                return

            # No existing target: set and perform an initial attack (also enables autoattack).
            combatant_info["target"] = target_display

        # Process initial attack through combat system
        result = game.combat_manager.process_turn(player.room_id, player.name, "attack", {"target": target_display})
        if result:
            if result.get("success"):
                damage = result.get("damage", 0)
                if damage > 0:
                    if result.get("critical"):
                        game.send_to_player(player, f"You critically strike {target_display} for {damage} damage!")
                    else:
                        game.send_to_player(player, f"You attack {target_display} for {damage} damage!")
                else:
                    game.send_to_player(player, f"You attack {target_display} but miss!")
                
                # Handle defeat and EXP (template NPCs only; runtime instances handled by _on_combat_defeated)
                if target_npc and hasattr(target_npc, 'health') and target_npc.health <= 0 and not getattr(target_npc, 'instance_id', None):
                    # Award EXP
                    if hasattr(target_npc, 'exp_value') and target_npc.exp_value > 0:
                        exp_gain = target_npc.exp_value
                    else:
                        tier_multiplier = {"Low": 1, "Mid": 2, "High": 3, "Epic": 5}.get(target_npc.get_tier(), 1)
                        exp_gain = 25 + (target_npc.max_health // 2) * tier_multiplier
                    
                    player.experience += exp_gain
                    game.send_to_player(player, f"You gain {exp_gain} experience points!")
                    
                    # Handle loot
                    if hasattr(target_npc, 'loot_table') and target_npc.loot_table:
                        for loot_entry in target_npc.loot_table:
                            if isinstance(loot_entry, dict):
                                chance = loot_entry.get("chance", 100)
                                if random.randint(1, 100) <= chance:
                                    item_id = loot_entry.get("item")
                                    if item_id:
                                        room.items.append(item_id)
                                        item = game.items.get(item_id)
                                        if item:
                                            game.broadcast_to_room(player.room_id, f"{item.name} drops from {target_npc.name}!")
                            elif isinstance(loot_entry, str):
                                room.items.append(loot_entry)
                                item = game.items.get(loot_entry)
                                if item:
                                    game.broadcast_to_room(player.room_id, f"{item.name} drops from {target_npc.name}!")
                    
                    # Remove NPC from room (template only)
                    if target_npc.npc_id in room.npcs:
                        room.npcs.remove(target_npc.npc_id)
                    game.check_level_up(player)
            else:
                game.send_to_player(player, result.get("message", "Attack failed"))
        return
    
    # Fallback to simple combat (if combat manager not available)
    if not target_npc:
        game.send_to_player(player, "You can only attack NPCs in simple combat mode.")
        return
        
    # Get equipped weapon
    equipped_weapon = None
    weapon_item = None
    if "weapon" in player.equipped:
        weapon_id = player.equipped["weapon"]
        weapon_item = game.items.get(weapon_id)
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
            else:
                if random.random() <= 0.01:
                    is_critical = True
            
            if is_critical:
                damage = base_damage * 2
                game.send_to_player(player, f"You critically strike {target_npc.name} for {damage} damage with your {equipped_weapon.name}!")
            elif is_glancing:
                damage = max(1, base_damage // 2)
                game.send_to_player(player, f"You land a glancing blow on {target_npc.name} for {damage} damage with your {equipped_weapon.name}!")
            else:
                damage = base_damage
                game.send_to_player(player, f"You attack {target_npc.name} for {damage} damage with your {equipped_weapon.name}!")
            
            damage_type = equipped_weapon.damage_type
            if getattr(game, 'apply_armor_damage_reduction', None):
                damage = game.apply_armor_damage_reduction(
                    target_npc, damage, damage_type, game.items,
                    game.broadcast_to_room, player.room_id
                )
            # Reduce weapon durability
            if equipped_weapon.reduce_durability(1):
                game.send_to_player(player, f"Your {equipped_weapon.name} breaks!")
                # Remove from equipped and inventory
                if "weapon" in player.equipped:
                    del player.equipped["weapon"]
                if weapon_id in player.inventory:
                    player.inventory.remove(weapon_id)
        else:
            # Unarmed: 1-1 damage, crit 0.01 (worse than stick)
            base_damage = 1
            damage_type = "bludgeoning"
            if is_critical:
                damage = base_damage * 2
                game.send_to_player(player, f"You critically strike {target_npc.name} for {damage} damage (unarmed)!")
            elif is_glancing:
                damage = max(1, base_damage // 2)
                game.send_to_player(player, f"You land a glancing blow on {target_npc.name} for {damage} damage (unarmed)!")
            else:
                damage = base_damage
                game.send_to_player(player, f"You attack {target_npc.name} for {damage} damage (unarmed)!")
            
            if getattr(game, 'apply_armor_damage_reduction', None):
                damage = game.apply_armor_damage_reduction(
                    target_npc, damage, "bludgeoning", game.items,
                    game.broadcast_to_room, player.room_id
                )
        game.broadcast_to_room(player.room_id, 
                              f"{player.name} attacks {target_npc.name}!", player.name)
        
        target_npc.health -= damage
        target_npc.health = max(0, target_npc.health)
        
        # Track skill use for advancement
        player.check_skill_advancement("fighting", True)
    else:
        # Miss - defender's dodge succeeded
        game.send_to_player(player, f"You attack {target_npc.name} but they dodge out of the way!")
        game.broadcast_to_room(player.room_id, 
                              f"{player.name} attacks {target_npc.name} but misses!", player.name)
        player.check_skill_advancement("fighting", False)
    
    if target_npc.health <= 0:
        game.send_to_player(player, f"You have slain {target_npc.name}!")
        game.broadcast_to_room(player.room_id, 
                              f"{player.name} has slain {target_npc.name}!", player.name)
        
        # Use NPC's exp_value if set, otherwise calculate based on tier/level
        if hasattr(target_npc, 'exp_value') and target_npc.exp_value > 0:
            exp_gain = target_npc.exp_value
        else:
            # Calculate based on tier
            tier_multiplier = {"Low": 1, "Mid": 2, "High": 3, "Epic": 5}.get(target_npc.get_tier(), 1)
            exp_gain = 25 + (target_npc.max_health // 2) * tier_multiplier
        
        player.experience += exp_gain
        game.send_to_player(player, f"You gain {exp_gain} experience points!")
        
        # Update quest progress (defeat creature)
        if game.quest_manager:
            completed = game.quest_manager.update_quest_progress(
                player.name, "defeat_creature", target_npc.npc_id, 1
            )
            for quest in completed:
                player.experience += quest.exp_reward
                game.send_to_player(player, f"{game.format_header('Quest Complete!')}")
                game.send_to_player(player, f"Quest: {quest.name}")
                game.send_to_player(player, f"You gain {quest.exp_reward} EXP from quest completion!")
                game.check_level_up(player)
        
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
                            item = game.items.get(item_id)
                            if item:
                                game.broadcast_to_room(player.room_id, f"{item.name} drops from {target_npc.name}!")
                elif isinstance(loot_entry, str):
                    # Simple item ID
                    room.items.append(loot_entry)
                    item = game.items.get(loot_entry)
                    if item:
                        game.broadcast_to_room(player.room_id, f"{item.name} drops from {target_npc.name}!")
        
        # Legacy inventory drop (for backward compatibility)
        if target_npc.inventory:
            for item_id in target_npc.inventory:
                room.items.append(item_id)
                item = game.items.get(item_id)
                if item:
                    game.broadcast_to_room(player.room_id, 
                                          f"{item.name} drops from {target_npc.name}!")
        
        room.npcs.remove(target_npc.npc_id)
        game.check_level_up(player)
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
            game.send_to_player(player, f"{target_npc.name} hits you for {counter_damage} damage!")
            
            if player.health <= 0:
                player.health = 0
                game.send_to_player(player, "You have been defeated! You respawn at The Black Anchor - Common Room.")
                game.broadcast_to_room(player.room_id, 
                                      f"{player.name} has been defeated!", player.name)
                respawn_player(game, player)
        else:
            game.send_to_player(player, f"{target_npc.name} attacks but misses!")


def respawn_player(game, player):
    """Respawn a defeated player."""
    old_room = game.get_room(player.room_id)
    if old_room:
        old_room.players.discard(player.name)
        
    player.room_id = "black_anchor_common"
    player.health = player.max_health // 2
    
    new_room = game.get_room(player.room_id)
    if new_room:
        new_room.players.add(player.name)
        
        game.send_to_player(player, "You respawn at The Black Anchor - Common Room with half health.")
    # Import look_command to avoid circular dependency
    from .movement import look_command
    look_command(game, player, [])
    game.broadcast_to_room(player.room_id, f"{player.name} appears, looking wounded.", player.name)


def join_combat_command(game, player, args):
    """Join an existing combat in the room"""
    room = game.get_room(player.room_id)
    if not room:
        return
    
    if not game.combat_manager:
        game.send_to_player(player, "Combat system not available.")
        return
    
    # Check if there's active combat
    combat = game.combat_manager.get_combat_state(player.room_id)
    if not combat or not combat.is_active:
        game.send_to_player(player, "There is no active combat here.")
        return
    
    # Check if already in combat
    if player.name in combat.combatants:
        game.send_to_player(player, "You are already in combat.")
        return
    
    # Join combat
    target_name = args[1] if len(args) > 1 else None
    game.combat_manager.join_combat(player.room_id, player.name, player, target_name)
    game.send_to_player(player, "You join the combat!")


def disengage_command(game, player, args):
    """Attempt to disengage from combat"""
    if not game.combat_manager:
        game.send_to_player(player, "Combat system not available.")
        return
    
    combat = game.combat_manager.get_combat_state(player.room_id)
    if not combat or not combat.is_active:
        game.send_to_player(player, "You are not in combat.")
        return
    
    if player.name not in combat.combatants:
        game.send_to_player(player, "You are not in combat.")
        return
    
    # Attempt disengage
    if game.combat_manager.leave_combat(player.room_id, player.name):
        game.send_to_player(player, "You disengage from combat.")
    else:
        game.send_to_player(player, "You cannot disengage right now.")


def use_maneuver_command(game, player, args):
    """Use a maneuver in combat or out of combat"""
    if not args:
        game.send_to_player(player, "Use which maneuver? Usage: use maneuver <name>")
        return
    
    maneuver_name = " ".join(args).lower()
    
    # Find maneuver by name
    maneuver_id = None
    for mid, maneuver in game.maneuvers.items():
        if maneuver_name in maneuver.get("name", "").lower():
            maneuver_id = mid
            break
    
    if not maneuver_id:
        game.send_to_player(player, f"You don't know a maneuver called '{maneuver_name}'.")
        return
    
    if maneuver_id not in player.known_maneuvers:
        game.send_to_player(player, f"You don't know the maneuver '{maneuver_name}'.")
        return
    
    if maneuver_id not in player.active_maneuvers:
        game.send_to_player(player, f"The maneuver '{maneuver_name}' is not currently active.")
        game.send_to_player(player, f"Use {game.format_command('maneuvers')} to activate it.")
        return
    
    # Check if in combat
    if game.combat_manager:
        combat = game.combat_manager.get_combat_state(player.room_id)
        if combat and combat.is_active and player.name in combat.combatants:
            # Use in combat (would integrate with turn system)
            game.send_to_player(player, f"You prepare to use {maneuver_name}...")
            # Note: Combat maneuver integration pending
        else:
            # Use out of combat
            game.send_to_player(player, f"You use {maneuver_name}.")
            # Note: Maneuver effects implementation pending
    else:
        game.send_to_player(player, f"You use {maneuver_name}.")
        # Note: Maneuver effects implementation pending
