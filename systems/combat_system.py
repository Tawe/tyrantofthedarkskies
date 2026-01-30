"""Comprehensive combat system implementing room-level tactical combat."""

import random
import time
import asyncio
from collections import defaultdict

# Armor slots per docs/armor_system.md (also support legacy "armor"=chest, "offhand"=shield)
ARMOR_SLOTS = ("head", "chest", "arms", "legs", "shield", "armor", "offhand")


def apply_armor_damage_reduction(target, damage, damage_type, items_dict, broadcast_func=None, room_id=None):
    """
    Apply DR from all equipped armor and degrade each piece by amount absorbed (docs/armor_system.md).
    Returns final damage to apply to target HP. Call after hit is confirmed.
    """
    if not items_dict or not hasattr(target, 'equipped'):
        return damage
    armor_pieces = []
    for slot in ARMOR_SLOTS:
        item_id = target.equipped.get(slot)
        if not item_id:
            continue
        piece = items_dict.get(item_id)
        if not piece or not getattr(piece, 'is_armor', lambda: False)():
            continue
        dr = piece.get_dr_for_damage_type(damage_type) if hasattr(piece, 'get_dr_for_damage_type') else piece.damage_reduction.get(damage_type, 0)
        if dr > 0:
            armor_pieces.append((slot, item_id, piece, dr))
    if not armor_pieces:
        return damage
    total_dr = sum(p[3] for p in armor_pieces)
    damage_after = max(1, damage - total_dr)
    absorbed = damage - damage_after
    for slot, item_id, piece, piece_dr in armor_pieces:
        if total_dr <= 0:
            break
        absorbed_by_piece = max(0, int(round(absorbed * piece_dr / total_dr)))
        if absorbed_by_piece > 0 and hasattr(piece, 'reduce_armor_hp'):
            broken = piece.reduce_armor_hp(absorbed_by_piece)
            if broken and broadcast_func and room_id:
                target_name_display = getattr(target, 'name', str(target))
                broadcast_func(room_id, f"{target_name_display}'s {piece.name} is broken!")
    return damage_after

class CombatState:
    """Represents the state of combat in a room"""
    
    def __init__(self, room_id):
        self.room_id = room_id
        self.is_active = False
        self.round_number = 0
        self.initiative_order = []  # List of (entity_name, entity_type, initiative)
        self.current_turn_index = 0
        self.combatants = {}  # {name: {"type": "player"/"npc", "entity": object, "state": "Observing"/"Engaged"/etc, "states": []}}
        self.round_summary = []
        self.started_at = None
        self.turn_actions = {}  # Track primary and minor actions per turn {name: {"primary": None, "minor": None}}
        self.turn_started_at = {}  # Track when each combatant's turn started {name: timestamp}
    
    def add_combatant(self, name, entity, entity_type="player"):
        """Add a combatant to the combat"""
        if name not in self.combatants:
            initiative = random.randint(1, 20) + entity.get_attribute_bonus("physical")
            self.combatants[name] = {
                "type": entity_type,
                "entity": entity,
                "state": "Observing",  # Primary state
                "states": ["Observing"],  # All active states (can have multiple)
                "initiative": initiative,
                "target": None
            }
            self.turn_actions[name] = {"primary": None, "minor": None}
            # Insert at end of current round
            self.initiative_order.append((name, entity_type, initiative))
            # Sort by initiative (highest first)
            self.initiative_order.sort(key=lambda x: x[2], reverse=True)
    
    def remove_combatant(self, name):
        """Remove a combatant from combat"""
        if name in self.combatants:
            del self.combatants[name]
            self.initiative_order = [(n, t, i) for n, t, i in self.initiative_order if n != name]
    
    def get_current_turn(self):
        """Get the entity whose turn it is"""
        if not self.initiative_order:
            return None
        name, entity_type, _ = self.initiative_order[self.current_turn_index]
        return self.combatants.get(name)
    
    def next_turn(self):
        """Advance to next turn"""
        self.current_turn_index += 1
        if self.current_turn_index >= len(self.initiative_order):
            self.current_turn_index = 0
            self.round_number += 1
            return True  # New round
        return False
    
    def get_combat_summary(self):
        """Get summary of combat state"""
        summary = []
        enemies_count = 0
        for name, info in self.combatants.items():
            entity = info["entity"]
            states = info.get("states", [info.get("state", "Observing")])
            state_display = ", ".join(states) if isinstance(states, list) else states
            
            if hasattr(entity, 'health'):
                health_pct = (entity.health / entity.max_health * 100) if entity.max_health > 0 else 0
                if health_pct < 25:
                    status = "critical"
                elif health_pct < 50:
                    status = "wounded"
                elif health_pct < 75:
                    status = "injured"
                else:
                    status = "healthy"
                
                # Count enemies
                if info.get("type") == "npc":
                    enemies_count += 1
                
                summary.append(f"{name}: {status} ({state_display})")
        
        if enemies_count > 0:
            summary.insert(0, f"Enemies: {enemies_count} remaining")
        
        return summary


class CombatManager:
    """Manages all combat instances across rooms"""
    
    def __init__(self, formatter, get_room_func, broadcast_func, items_dict=None):
        self.formatter = formatter
        self.get_room_func = get_room_func
        self.broadcast_func = broadcast_func
        self.items_dict = items_dict  # Reference to items dictionary for weapon lookups
        self.active_combats = {}  # {room_id: CombatState}
        self.combat_tick_task = None  # Background task for processing combat ticks
        # Base Attack Tick in *real* seconds.
        # Design doc: BAT = 3 in-game seconds, with a 3x time ratio ⇒ 1 real second.
        # We operate directly in real seconds here.
        self.base_attack_tick = 1.0
    
    def get_combat_state(self, room_id):
        """Get or create combat state for a room"""
        if room_id not in self.active_combats:
            self.active_combats[room_id] = CombatState(room_id)
        return self.active_combats[room_id]
    
    def start_combat(self, room_id, attacker_name, attacker, target_name, target):
        """Start combat between two entities"""
        combat = self.get_combat_state(room_id)
        combat.is_active = True
        combat.started_at = time.time()
        combat.round_number = 1
        
        # Add both combatants
        combat.add_combatant(attacker_name, attacker, "player" if hasattr(attacker, 'connection') else "npc")
        combat.add_combatant(target_name, target, "player" if hasattr(target, 'connection') else "npc")
        
        # Set them as engaged
        combat.combatants[attacker_name]["state"] = "Engaged"
        combat.combatants[attacker_name]["target"] = target_name
        combat.combatants[target_name]["state"] = "Engaged"
        combat.combatants[target_name]["target"] = attacker_name
        
        # Track when each combatant's turn started (for timeout)
        combat.turn_started_at[attacker_name] = time.time()
        combat.turn_started_at[target_name] = time.time()
        
        # Broadcast combat start
        self.broadcast_func(room_id, f"Combat begins! {attacker_name} vs {target_name}")
        
        # Start combat tick task if not already running
        self._ensure_combat_tick_task()
        
        return combat
    
    def join_combat(self, room_id, entity_name, entity, target_name=None):
        """Join an existing combat"""
        combat = self.get_combat_state(room_id)
        if not combat.is_active:
            return None
        
        combat.add_combatant(entity_name, entity, "player" if hasattr(entity, 'connection') else "npc")
        
        if target_name and target_name in combat.combatants:
            combat.combatants[entity_name]["state"] = "Engaged"
            combat.combatants[entity_name]["target"] = target_name
        
        # Initialize turn tracking
        if not hasattr(combat, 'turn_started_at'):
            combat.turn_started_at = {}
        combat.turn_started_at[entity_name] = time.time()
        
        self.broadcast_func(room_id, f"{entity_name} joins the combat!")
        
        # Ensure combat tick task is running
        self._ensure_combat_tick_task()
        
        return combat
    
    def leave_combat(self, room_id, entity_name):
        """Attempt to leave combat (disengage)"""
        combat = self.get_combat_state(room_id)
        if entity_name not in combat.combatants:
            return False

        # Set to disengaging state on the tracked combatant
        combat.combatants[entity_name]["state"] = "Disengaging"

        # TODO: Check for opportunity attacks before completing disengage

        # Remove from combat tracking structures
        combat.remove_combatant(entity_name)
        combat.turn_actions.pop(entity_name, None)
        combat.turn_started_at.pop(entity_name, None)

        self.broadcast_func(room_id, f"{entity_name} disengages from combat.")
        
        # Check if combat should end
        if len(combat.combatants) < 2:
            self.end_combat(room_id)
        
        return True
    
    def end_combat(self, room_id):
        """End combat in a room"""
        if room_id in self.active_combats:
            combat = self.active_combats[room_id]
            combat.is_active = False
            self.broadcast_func(room_id, "Combat ends.")
            # Don't delete, keep for potential re-engagement
    
    def _ensure_combat_tick_task(self):
        """Ensure the combat tick background task is running"""
        if self.combat_tick_task is None or self.combat_tick_task.done():
            try:
                loop = asyncio.get_event_loop()
                self.combat_tick_task = loop.create_task(self._combat_tick_loop())
            except RuntimeError:
                # No event loop running, skip (will be started when combat begins)
                pass
    
    async def _combat_tick_loop(self):
        """Background task that processes combat turns automatically"""
        while True:
            try:
                await asyncio.sleep(0.1)  # Check every 0.1 seconds for very responsive combat
                self.process_combat_ticks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue
                print(f"Error in combat tick loop: {e}")
                import traceback
                traceback.print_exc()
    
    def _get_weapon_speed_cost(self, entity):
        """Get weapon speed cost for an entity (defaults to unarmed profile if no weapon).
        
        Design doc:
        - Weapons define `speed_cost` (lower = faster, higher = slower).
        - Unarmed baseline: speed_cost = 1.0 (worse than stick 0.9).
        """
        if hasattr(entity, 'equipped') and "weapon" in entity.equipped and self.items_dict:
            weapon_id = entity.equipped["weapon"]
            weapon = self.items_dict.get(weapon_id)
            if weapon and hasattr(weapon, 'get_effective_speed_cost'):
                return weapon.get_effective_speed_cost()
        # Unarmed: 1-1 damage, speed 1.0, crit 0.01
        return 1.0
    
    def _get_turn_timeout(self, entity):
        """Calculate attack interval based on weapon speed.

        Design doc:
        - attack_interval = BAT × weapon.speed_cost
        Where BAT is expressed here directly in real seconds.
        """
        speed_cost = self._get_weapon_speed_cost(entity)
        # Faster weapons (lower speed_cost) = shorter interval.
        timeout = self.base_attack_tick * speed_cost
        # Keep a small lower bound so we never spin absurdly fast.
        return max(0.2, timeout)
    
    def process_combat_ticks(self):
        """Process all active combats, handling automatic turns"""
        for room_id, combat in list(self.active_combats.items()):
            if not combat.is_active:
                continue
            
            # Check if combat has ended (not enough combatants)
            if len(combat.combatants) < 2:
                self.end_combat(room_id)
                continue
            
            # Get the name of the entity whose turn it is
            if not combat.initiative_order:
                continue
            
            name, entity_type, _ = combat.initiative_order[combat.current_turn_index]
            
            # Get current turn info
            current_turn_info = combat.combatants.get(name)
            if not current_turn_info:
                continue
            
            entity = current_turn_info.get("entity")
            if not entity:
                continue
            
            # Check if this entity has already acted this turn
            turn_actions = combat.turn_actions.get(name, {"primary": None, "minor": None})
            
            # If it's an NPC and hasn't acted, make them attack automatically (with weapon speed delay)
            if entity_type == "npc" and turn_actions["primary"] is None:
                # Check if enough time has passed based on weapon speed
                if not hasattr(combat, 'turn_started_at'):
                    combat.turn_started_at = {}
                turn_start = combat.turn_started_at.get(name, combat.started_at if hasattr(combat, 'started_at') else time.time())
                elapsed = time.time() - turn_start
                timeout = self._get_turn_timeout(entity)
                if elapsed >= timeout:
                    self._process_npc_turn(combat, name, current_turn_info)
            # If it's a player and hasn't acted within timeout, auto-attack
            elif entity_type == "player" and turn_actions["primary"] is None:
                # Check if turn timeout has passed (based on weapon speed)
                if not hasattr(combat, 'turn_started_at'):
                    combat.turn_started_at = {}
                turn_start = combat.turn_started_at.get(name, combat.started_at if hasattr(combat, 'started_at') else time.time())
                elapsed = time.time() - turn_start
                timeout = self._get_turn_timeout(entity)
                if elapsed >= timeout:
                    self._process_player_auto_attack(combat, name, current_turn_info)
    
    def _process_npc_turn(self, combat, npc_name, npc_info):
        """Process an NPC's turn automatically"""
        target_name = npc_info.get("target")
        if not target_name or target_name not in combat.combatants:
            # Find any enemy target
            for name, info in combat.combatants.items():
                if info.get("type") == "player":
                    target_name = name
                    break
        
        if target_name:
            # NPC attacks their target
            result = self.process_turn(combat.room_id, npc_name, "attack", {"target": target_name})
            if result and not result.get("success"):
                # If attack failed, still advance turn to prevent stalling
                combat.turn_actions[npc_name]["primary"] = "attack"  # Mark as used
                new_round = combat.next_turn()
                if new_round:
                    for name in combat.combatants:
                        combat.turn_actions[name] = {"primary": None, "minor": None}
                        combat.turn_started_at[name] = time.time()
                else:
                    next_turn_info = combat.get_current_turn()
                    if next_turn_info:
                        next_name = combat.initiative_order[combat.current_turn_index][0]
                        combat.turn_started_at[next_name] = time.time()
    
    def _process_player_auto_attack(self, combat, player_name, player_info):
        """Process a player's auto-attack when they haven't acted"""
        target_name = player_info.get("target")
        # Autoattack should be *paused* if there is no valid target.
        if not target_name or target_name not in combat.combatants:
            return
        
        if target_name:
            # Player auto-attacks their target
            result = self.process_turn(combat.room_id, player_name, "attack", {"target": target_name})
            if result and not result.get("success"):
                # If attack failed, still advance turn
                combat.turn_actions[player_name]["primary"] = "attack"
                new_round = combat.next_turn()
                if new_round:
                    for name in combat.combatants:
                        combat.turn_actions[name] = {"primary": None, "minor": None}
                        combat.turn_started_at[name] = time.time()
                else:
                    next_turn_info = combat.get_current_turn()
                    if next_turn_info:
                        next_name = combat.initiative_order[combat.current_turn_index][0]
                        combat.turn_started_at[next_name] = time.time()
    
    def process_turn(self, room_id, entity_name, action_type, action_data, is_primary=True):
        """Process a combat turn for a specific entity
        
        Args:
            room_id: Room where combat is happening
            entity_name: Name of entity taking action
            action_type: Type of action (attack, maneuver, move, support, etc.)
            action_data: Data for the action
            is_primary: True for primary action, False for minor action
        """
        combat = self.get_combat_state(room_id)
        if not combat or not combat.is_active:
            return None
        
        if entity_name not in combat.combatants:
            return {"success": False, "message": "You are not in combat"}
        
        entity_info = combat.combatants[entity_name]
        entity = entity_info["entity"]
        
        # Check if action slot is already used
        if is_primary:
            if combat.turn_actions[entity_name]["primary"] is not None:
                return {"success": False, "message": "You have already used your primary action this turn"}
        else:
            if combat.turn_actions[entity_name]["minor"] is not None:
                return {"success": False, "message": "You have already used your minor action this turn"}
        
        # Process action based on type
        result = None
        if action_type == "attack":
            if not is_primary:
                return {"success": False, "message": "Attacks must be primary actions"}
            result = self._process_attack(combat, entity, action_data, self.items_dict)
            if result and result.get("success"):
                combat.turn_actions[entity_name]["primary"] = action_type
        elif action_type == "maneuver":
            if not is_primary:
                return {"success": False, "message": "Maneuvers must be primary actions"}
            result = self._process_maneuver(combat, entity, action_data)
            if result and result.get("success"):
                combat.turn_actions[entity_name]["primary"] = action_type
        elif action_type == "move":
            if is_primary:
                return {"success": False, "message": "Movement is a minor action"}
            result = self._process_move(combat, entity, action_data)
            if result and result.get("success"):
                combat.turn_actions[entity_name]["minor"] = action_type
        elif action_type == "support":
            if not is_primary:
                return {"success": False, "message": "Support actions must be primary actions"}
            result = self._process_support(combat, entity, action_data)
            if result and result.get("success"):
                combat.turn_actions[entity_name]["primary"] = action_type
        elif action_type == "ready":
            # Ready action (minor)
            if is_primary:
                return {"success": False, "message": "Ready is a minor action"}
            result = {"success": True, "message": "You ready yourself"}
            combat.turn_actions[entity_name]["minor"] = action_type
        elif action_type == "interact":
            # Interact with environment (minor)
            if is_primary:
                return {"success": False, "message": "Interact is a minor action"}
            result = {"success": True, "message": "You interact with the environment"}
            combat.turn_actions[entity_name]["minor"] = action_type
        
        # Broadcast result
        if result and result.get("success"):
            if action_type == "attack":
                damage = result.get("damage", 0)
                target = result.get("target", "target")
                if damage > 0:
                    self.broadcast_func(room_id, f"{entity_name} attacks {target} for {damage} damage!")
                else:
                    self.broadcast_func(room_id, f"{entity_name} attacks {target} but misses!")
        
        # Check for defeat
        if result and result.get("damage", 0) > 0:
            target_name = result.get("target")
            if target_name in combat.combatants:
                target_entity = combat.combatants[target_name]["entity"]
                if hasattr(target_entity, 'health') and target_entity.health <= 0:
                    self.broadcast_func(room_id, f"{target_name} has been defeated!")
                    # Notify game for runtime B2 (remove instance, create loot)
                    if hasattr(self.formatter, '_on_combat_defeated'):
                        self.formatter._on_combat_defeated(room_id, target_name, target_entity, entity_name)
                    combat.remove_combatant(target_name)
                    
                    # Check if combat should end
                    if len(combat.combatants) < 2:
                        self.end_combat(room_id)
        
        # Advance turn if primary action was used (or if both actions used)
        # Reset turn actions when moving to next combatant
        if is_primary or (combat.turn_actions[entity_name]["primary"] and combat.turn_actions[entity_name]["minor"]):
            # Check if current entity's turn is complete
            if not hasattr(combat, 'turn_started_at'):
                combat.turn_started_at = {}
            
            # Get current turn name
            if combat.initiative_order:
                current_name = combat.initiative_order[combat.current_turn_index][0]
                if current_name == entity_name:
                    # Advance to next turn
                    new_round = combat.next_turn()
                    
                    # Reset actions for all combatants at start of new round
                    if new_round:
                        for name in combat.combatants:
                            combat.turn_actions[name] = {"primary": None, "minor": None}
                            combat.turn_started_at[name] = time.time()
                        # End of round summary
                        summary = combat.get_combat_summary()
                        if summary:
                            summary_text = f"\n{self.formatter.format_header(f'Round {combat.round_number} Summary')}\n"
                            summary_text += "\n".join(f"- {s}" for s in summary)
                            self.broadcast_func(room_id, summary_text)
                    else:
                        # Reset actions for next combatant
                        if combat.initiative_order:
                            next_name = combat.initiative_order[combat.current_turn_index][0]
                            combat.turn_actions[next_name] = {"primary": None, "minor": None}
                            combat.turn_started_at[next_name] = time.time()
        
        return result
    
    def _process_attack(self, combat, attacker, action_data, items_dict=None):
        """Process an attack action with weapon support and Defense Model (Accuracy vs Dodging)"""
        target_name = action_data.get("target")
        if not target_name:
            return {"success": False, "message": "No target specified"}
        
        # Find target
        target_info = None
        for name, info in combat.combatants.items():
            if name == target_name or target_name.lower() in name.lower():
                target_info = info
                break
        
        if not target_info:
            return {"success": False, "message": "Target not found in combat"}
        
        target = target_info["entity"]
        
        # Get equipped weapon
        equipped_weapon = None
        damage_type = "bludgeoning"  # Default for unarmed
        if hasattr(attacker, 'equipped') and "weapon" in attacker.equipped and items_dict:
            weapon_id = attacker.equipped["weapon"]
            equipped_weapon = items_dict.get(weapon_id)
            if equipped_weapon and equipped_weapon.is_weapon():
                damage_type = equipped_weapon.damage_type
            else:
                equipped_weapon = None
        
        # DEFENSE MODEL: Accuracy (Fighting) vs Dodging contest
        # Attacker rolls Accuracy (Fighting skill)
        if hasattr(attacker, 'roll_skill_check'):
            accuracy_check = attacker.roll_skill_check("fighting")
            attacker_effective = accuracy_check.get("effective_skill", 50)
        else:
            # NPCs without skill system
            attacker_effective = 50
            accuracy_check = {"result": "success", "roll": random.randint(1, 100)}
        
        # Defender rolls Dodging
        if hasattr(target, 'roll_skill_check'):
            dodge_check = target.roll_skill_check("dodging")
            defender_effective = dodge_check.get("effective_skill", 50)
        else:
            # NPCs without skill system
            defender_effective = 50
            dodge_check = {"result": "success", "roll": random.randint(1, 100)}
        
        # Contest: Attacker's roll must beat defender's roll
        # If attacker roll <= attacker_effective AND attacker_roll < defender_roll, hit
        # OR if attacker roll <= attacker_effective AND defender_roll > defender_effective, hit
        attacker_roll = accuracy_check.get("roll", random.randint(1, 100))
        defender_roll = dodge_check.get("roll", random.randint(1, 100))
        
        # Hit determination: Attacker succeeds AND beats defender's roll
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
                else:
                    # Unarmed crit 0.01
                    if random.random() <= 0.01:
                        is_critical = True
                
                # Check for glancing hit (defender's dodge was close)
                if defender_roll <= defender_effective and defender_roll >= defender_effective * 0.8:
                    is_glancing = True
            else:
                # Defender's dodge succeeded
                hit = False
        
        if not hit:
            # Track skill use even on failure
            if hasattr(attacker, 'check_skill_advancement'):
                attacker.check_skill_advancement("fighting", False)
            if hasattr(target, 'check_skill_advancement'):
                target.check_skill_advancement("dodging", True)
            return {"success": False, "message": "Attack missed"}
        
        # HIT CONFIRMED - Now calculate damage
        if equipped_weapon:
            # Use weapon damage
            damage_min, damage_max = equipped_weapon.get_effective_damage()
            base_damage = random.randint(damage_min, damage_max)
            base_damage += attacker.get_attribute_bonus("physical")
            
            if is_critical:
                damage = base_damage * 2
            elif is_glancing:
                damage = max(1, base_damage // 2)  # Glancing hits do half damage
            else:
                damage = base_damage
            
            # Reduce weapon durability
            if equipped_weapon.reduce_durability(1):
                # Weapon breaks - would need to notify player
                pass
        else:
            # Unarmed: 1-1 damage, crit 0.01 (worse than stick)
            base_damage = 1
            if is_critical:
                damage = base_damage * 2
            elif is_glancing:
                damage = max(1, base_damage // 2)
            else:
                damage = base_damage
        
        # ARMOR MITIGATION (docs/armor_system.md): DR stacks; each piece degrades by amount absorbed
        if items_dict:
            damage = apply_armor_damage_reduction(
                target, damage, damage_type, items_dict,
                broadcast_func=self.broadcast_func, room_id=combat.room_id
            )

        # Apply damage
        target.health -= damage
        target.health = max(0, target.health)
        
        # Track skill use
        if hasattr(attacker, 'check_skill_advancement'):
            attacker.check_skill_advancement("fighting", True)
        if hasattr(target, 'check_skill_advancement'):
            target.check_skill_advancement("dodging", False)
        
        return {
            "success": True,
            "damage": damage,
            "target": target_info.get("name", target_name),
            "critical": is_critical,
            "glancing": is_glancing,
            "weapon": equipped_weapon.name if equipped_weapon else None,
            "damage_type": damage_type
        }
    
    def _process_maneuver(self, combat, entity, maneuver_data):
        """Process a maneuver action (placeholder for future implementation)."""
        return {"success": False, "message": "Maneuver system not yet implemented"}
    
    def _process_move(self, combat, entity, move_data):
        """Process a move action (placeholder for future implementation)."""
        return {"success": True, "message": "Moved"}
    
    def _process_support(self, combat, entity, support_data):
        """Process a support action (placeholder for future implementation)."""
        return {"success": False, "message": "Support system not yet implemented"}

