"""Comprehensive combat system implementing room-level tactical combat."""

import random
import time
import asyncio
from collections import defaultdict

# Armor slots per docs/armor_system.md (also support legacy "armor"=chest, "offhand"=shield)
ARMOR_SLOTS = ("head", "chest", "arms", "legs", "shield", "armor", "offhand")


class InstanceCombatTarget:
    """Wrapper so runtime entity instances (spawned creatures) can be used as combat targets (same interface as NPC)."""
    def __init__(self, inst, template_npc):
        self._template = template_npc
        self._inst = inst
        self.name = template_npc.name if template_npc else inst.get("template_id", "Unknown")
        self.health = inst.get("hp_current", 0)
        self.max_health = inst.get("hp_max", 10)
        self.instance_id = inst.get("instance_id")
        self.template_id = inst.get("template_id")
        self.spawn_group_id = inst.get("spawn_group_id")
        self.loot_table = getattr(template_npc, "loot_table", []) if template_npc else []
        self.npc_id = self.instance_id
        self.equipped = getattr(template_npc, "equipped", {}) if template_npc else {}

    def get_tier(self):
        return getattr(self._template, "get_tier", lambda: "Low")() if self._template else "Low"

    def get_attribute_bonus(self, attribute):
        return getattr(self._template, "get_attribute_bonus", lambda _: 0)(attribute) if self._template else 0

    def roll_skill_check(self, skill_name, difficulty_mod=0):
        return getattr(
            self._template, "roll_skill_check",
            lambda _s, _m=0: {"result": "success", "roll": random.randint(1, 100), "effective_skill": 50}
        )(skill_name, difficulty_mod) if self._template else {"result": "success", "roll": random.randint(1, 100), "effective_skill": 50}

    @property
    def exp_value(self):
        return getattr(self._template, "exp_value", 0) if self._template else 0


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
    """Combat state per room. Driven by weapon speed and attack tick (BAT), not rounds (see combat.md)."""
    
    def __init__(self, room_id):
        self.room_id = room_id
        self.is_active = False
        self.combatants = {}  # {name: {"type": "player"/"npc", "entity": object, "state": "Engaged"/etc, "states": [], "target": name}}
        self.initiative_order = []  # (entity_name, entity_type, initiative) for display/order only
        self.next_attack_at = {}  # name -> timestamp; when this combatant can next make a basic attack (BAT × speed_cost)
        self.started_at = None
    
    def add_combatant(self, name, entity, entity_type="player"):
        """Add a combatant to the combat."""
        if name not in self.combatants:
            initiative = random.randint(1, 20) + entity.get_attribute_bonus("physical")
            self.combatants[name] = {
                "type": entity_type,
                "entity": entity,
                "state": "Observing",
                "states": ["Observing"],
                "initiative": initiative,
                "target": None
            }
            self.initiative_order.append((name, entity_type, initiative))
            self.initiative_order.sort(key=lambda x: x[2], reverse=True)
    
    def remove_combatant(self, name):
        """Remove a combatant from combat."""
        if name in self.combatants:
            del self.combatants[name]
            self.next_attack_at.pop(name, None)
            self.initiative_order = [(n, t, i) for n, t, i in self.initiative_order if n != name]
    
    def get_combat_summary(self):
        """Get summary of combat state"""
        summary = []
        enemies_count = 0
        for name, info in self.combatants.items():
            entity = info["entity"]
            # Prefer current "state" (e.g. Engaged) over initial "states" list
            state_display = info.get("state") or (
                ", ".join(info.get("states", [])) if isinstance(info.get("states"), list) and info.get("states") else "Observing"
            )
            
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
        """Start combat between two entities. Attack timing is BAT × weapon speed (combat.md)."""
        combat = self.get_combat_state(room_id)
        combat.is_active = True
        combat.started_at = time.time()
        
        combat.add_combatant(attacker_name, attacker, "player" if hasattr(attacker, 'connection') else "npc")
        combat.add_combatant(target_name, target, "player" if hasattr(target, 'connection') else "npc")
        
        combat.combatants[attacker_name]["state"] = "Engaged"
        combat.combatants[attacker_name]["target"] = target_name
        combat.combatants[target_name]["state"] = "Engaged"
        combat.combatants[target_name]["target"] = attacker_name
        
        # Next attack time for each: attacker's first attack is processed in the command; next is in one interval. Target's first attack is in one interval.
        now = time.time()
        combat.next_attack_at[attacker_name] = now + self._get_turn_timeout(attacker)
        combat.next_attack_at[target_name] = now + self._get_turn_timeout(target)
        
        self.broadcast_func(room_id, f"Combat begins! {attacker_name} vs {target_name}")
        self._ensure_combat_tick_task()
        
        return combat
    
    def join_combat(self, room_id, entity_name, entity, target_name=None):
        """Join an existing combat. Next attack in one interval (BAT × speed)."""
        combat = self.get_combat_state(room_id)
        if not combat.is_active:
            return None
        
        combat.add_combatant(entity_name, entity, "player" if hasattr(entity, 'connection') else "npc")
        
        if target_name and target_name in combat.combatants:
            combat.combatants[entity_name]["state"] = "Engaged"
            combat.combatants[entity_name]["target"] = target_name
        
        combat.next_attack_at[entity_name] = time.time() + self._get_turn_timeout(entity)
        
        self.broadcast_func(room_id, f"{entity_name} joins the combat!")
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

        combat.remove_combatant(entity_name)

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
        """Drive combat by weapon speed: each combatant attacks when next_attack_at <= now (combat.md)."""
        now = time.time()
        for room_id, combat in list(self.active_combats.items()):
            if not combat.is_active:
                continue
            if len(combat.combatants) < 2:
                self.end_combat(room_id)
                continue
            
            for name in list(combat.combatants.keys()):
                next_at = combat.next_attack_at.get(name)
                if next_at is None or now < next_at:
                    continue
                info = combat.combatants.get(name)
                if not info:
                    continue
                target_name = info.get("target")
                if not target_name or target_name not in combat.combatants:
                    if info.get("type") == "npc":
                        for n, i in combat.combatants.items():
                            if i.get("type") == "player":
                                target_name = n
                                break
                    if not target_name:
                        continue
                # Process one basic attack for this combatant; process_turn will set next_attack_at
                self.process_turn(combat.room_id, name, "attack", {"target": target_name})
    
    def process_turn(self, room_id, entity_name, action_type, action_data, is_primary=True):
        """Process one action (e.g. one basic attack). Timing is driven by next_attack_at and combat tick (combat.md)."""
        combat = self.get_combat_state(room_id)
        if not combat or not combat.is_active:
            return None
        
        if entity_name not in combat.combatants:
            return {"success": False, "message": "You are not in combat"}
        
        entity_info = combat.combatants[entity_name]
        entity = entity_info["entity"]
        
        result = None
        if action_type == "attack":
            result = self._process_attack(combat, entity, action_data, self.items_dict)
        elif action_type == "maneuver":
            result = self._process_maneuver(combat, entity, action_data)
        elif action_type == "move":
            result = self._process_move(combat, entity, action_data)
        elif action_type == "support":
            result = self._process_support(combat, entity, action_data)
        elif action_type == "ready":
            result = {"success": True, "message": "You ready yourself"}
        elif action_type == "interact":
            result = {"success": True, "message": "You interact with the environment"}
        
        if result and action_type == "attack" and result.get("target"):
            damage = result.get("damage", 0)
            target = result.get("target", "target")
            if damage > 0:
                self.broadcast_func(room_id, f"{entity_name} attacks {target} for {damage} damage!")
            else:
                self.broadcast_func(room_id, f"{entity_name} attacks {target} but misses!")
            # Schedule next attack after this one (hit or miss); interval = BAT × speed (combat.md)
            combat.next_attack_at[entity_name] = time.time() + self._get_turn_timeout(entity)

        if result and action_type == "maneuver":
            # Broadcast maneuver result and delay next auto-attack (maneuver uses the turn)
            if result.get("damage") is not None:
                damage = result.get("damage", 0)
                target = result.get("target", "target")
                maneuver_name = result.get("maneuver_name", "maneuver")
                if damage > 0:
                    self.broadcast_func(room_id, f"{entity_name} uses {maneuver_name} on {target} for {damage} damage!")
                else:
                    self.broadcast_func(room_id, f"{entity_name} uses {maneuver_name} on {target} but misses!")
            elif result.get("success") and result.get("message"):
                self.broadcast_func(room_id, f"{entity_name} {result['message'].lower()}")
            combat.next_attack_at[entity_name] = time.time() + self._get_turn_timeout(entity)
        
        if result and result.get("damage", 0) > 0:
            target_name = result.get("target")
            if target_name in combat.combatants:
                target_entity = combat.combatants[target_name]["entity"]
                if hasattr(target_entity, 'health') and target_entity.health <= 0:
                    self.broadcast_func(room_id, f"{target_name} has been defeated!")
                    if hasattr(self.formatter, '_on_combat_defeated'):
                        self.formatter._on_combat_defeated(room_id, target_name, target_entity, entity_name)
                    combat.remove_combatant(target_name)
                    if len(combat.combatants) < 2:
                        self.end_combat(room_id)
        
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
            if hasattr(attacker, 'check_skill_advancement'):
                attacker.check_skill_advancement("fighting", False)
            if hasattr(target, 'check_skill_advancement'):
                target.check_skill_advancement("dodging", True)
            return {"success": False, "message": "Attack missed", "target": target_info.get("name", target_name), "damage": 0}
        
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
        # Brace maneuver: reduce incoming damage (e.g. half) for one attack
        if getattr(target, "brace_next_attack", False):
            damage = max(1, damage // 2)
            setattr(target, "brace_next_attack", False)

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
        """Process a maneuver action: pay cost, resolve damage or defensive effects (docs/maneuver.md)."""
        maneuver = maneuver_data.get("maneuver") or {}
        target_name = maneuver_data.get("target")
        maneuver_id = maneuver_data.get("maneuver_id", "")
        effects = maneuver.get("effects") or {}
        success_effect = (effects.get("success") or "").lower()

        # Pay stamina cost
        cost = maneuver.get("cost") or {}
        stamina_cost = cost.get("stamina", 0)
        if stamina_cost > 0 and hasattr(entity, "stamina"):
            if (getattr(entity, "stamina", 0) or 0) < stamina_cost:
                return {"success": False, "message": "Not enough stamina."}
            entity.stamina = max(0, (entity.stamina or 0) - stamina_cost)

        # Defensive: e.g. Brace (damage_reduction_next_attack)
        if "damage_reduction" in success_effect or "damage_reduction_next_attack" in success_effect:
            setattr(entity, "brace_next_attack", True)
            return {"success": True, "message": "You brace for the next attack.", "maneuver_id": maneuver_id}

        # Damage-dealing maneuver: resolve hit and apply damage (same model as attack)
        if "damage" in success_effect and target_name:
            target_info = None
            for name, info in combat.combatants.items():
                if name == target_name or (target_name.lower() in name.lower()):
                    target_info = info
                    break
            if not target_info:
                return {"success": False, "message": "Target not in combat."}
            target = target_info["entity"]

            items_dict = self.items_dict or {}
            equipped_weapon = None
            damage_type = "bludgeoning"
            if hasattr(entity, "equipped") and "weapon" in entity.equipped and items_dict:
                weapon_id = entity.equipped["weapon"]
                w = items_dict.get(weapon_id)
                if w and getattr(w, "is_weapon", lambda: False)():
                    equipped_weapon = w
                    damage_type = getattr(w, "damage_type", "bludgeoning")

            # Accuracy vs Dodging
            if hasattr(entity, "roll_skill_check"):
                accuracy_check = entity.roll_skill_check("fighting")
                attacker_effective = accuracy_check.get("effective_skill", 50)
            else:
                attacker_effective = 50
                accuracy_check = {"result": "success", "roll": random.randint(1, 100)}
            if hasattr(target, "roll_skill_check"):
                dodge_check = target.roll_skill_check("dodging")
                defender_effective = dodge_check.get("effective_skill", 50)
            else:
                defender_effective = 50
                dodge_check = {"result": "success", "roll": random.randint(1, 100)}

            attacker_roll = accuracy_check.get("roll", random.randint(1, 100))
            defender_roll = dodge_check.get("roll", random.randint(1, 100))
            hit = False
            is_critical = False
            is_glancing = False
            # Increased crit chance for e.g. desperate_strike
            bonus_crit = 0.15 if "increased_crit_chance" in success_effect else 0

            if attacker_roll <= attacker_effective and (attacker_roll < defender_roll or defender_roll > defender_effective):
                hit = True
                if accuracy_check.get("result") == "critical":
                    is_critical = True
                elif bonus_crit > 0 and random.random() < bonus_crit:
                    is_critical = True
                elif equipped_weapon and random.random() <= getattr(equipped_weapon, "get_effective_crit_chance", lambda: 0.01)():
                    is_critical = True
                elif not equipped_weapon and random.random() <= 0.01:
                    is_critical = True
                if defender_roll <= defender_effective and defender_roll >= defender_effective * 0.8:
                    is_glancing = True

            if not hit:
                return {"success": False, "message": "Maneuver missed.", "target": target_name, "damage": 0}

            if equipped_weapon:
                damage_min, damage_max = equipped_weapon.get_effective_damage()
                base_damage = random.randint(damage_min, damage_max)
                if hasattr(entity, "get_attribute_bonus"):
                    base_damage += entity.get_attribute_bonus("physical")
            else:
                base_damage = 1
            if is_critical:
                damage = base_damage * 2
            elif is_glancing:
                damage = max(1, base_damage // 2)
            else:
                damage = base_damage

            if items_dict:
                damage = apply_armor_damage_reduction(
                    target, damage, damage_type, items_dict,
                    broadcast_func=self.broadcast_func, room_id=combat.room_id
                )
            target.health = max(0, (getattr(target, "health", 0) - damage))
            if hasattr(target, "brace_next_attack"):
                setattr(target, "brace_next_attack", False)

            return {
                "success": True,
                "damage": damage,
                "target": target_name,
                "critical": is_critical,
                "glancing": is_glancing,
                "maneuver_id": maneuver_id,
                "maneuver_name": maneuver.get("name", maneuver_id),
            }
        return {"success": True, "message": "Maneuver used.", "maneuver_id": maneuver_id}
    
    def _process_move(self, combat, entity, move_data):
        """Process a move action (placeholder for future implementation)."""
        return {"success": True, "message": "Moved"}
    
    def _process_support(self, combat, entity, support_data):
        """Process a support action (placeholder for future implementation)."""
        return {"success": False, "message": "Support system not yet implemented"}

