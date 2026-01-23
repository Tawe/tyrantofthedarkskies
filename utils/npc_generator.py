"""NPC generation system with role-based stat generation."""

import random

class NPCGenerator:
    """Generates NPCs with role-based stats and behaviors"""
    
    # Role-based stat biases
    ROLE_STAT_BIASES = {
        "Brute": {
            "physical": +3,
            "mental": -1,
            "spiritual": 0,
            "social": -1,
            "hp_multiplier": 1.5,
            "damage_bonus": +2
        },
        "Minion": {
            "physical": 0,
            "mental": -2,
            "spiritual": -2,
            "social": -2,
            "hp_multiplier": 0.5,
            "damage_bonus": -1
        },
        "Boss": {
            "physical": +2,
            "mental": +2,
            "spiritual": +2,
            "social": +1,
            "hp_multiplier": 2.5,
            "damage_bonus": +3
        },
        "Artillery": {
            "physical": 0,
            "mental": +3,
            "spiritual": +1,
            "social": 0,
            "hp_multiplier": 0.8,
            "damage_bonus": +1
        },
        "Healer": {
            "physical": -1,
            "mental": +1,
            "spiritual": +3,
            "social": +1,
            "hp_multiplier": 1.0,
            "damage_bonus": -2
        },
        "Controller": {
            "physical": -1,
            "mental": +3,
            "spiritual": +2,
            "social": 0,
            "hp_multiplier": 1.0,
            "damage_bonus": -1
        }
    }
    
    # Tier-based attribute ranges
    TIER_ATTRIBUTE_RANGES = {
        "Low": {"min": 8, "max": 14, "base": 10},
        "Mid": {"min": 12, "max": 18, "base": 14},
        "High": {"min": 16, "max": 22, "base": 18},
        "Epic": {"min": 20, "max": 26, "base": 22}
    }
    
    # Tier-based EXP values
    TIER_EXP_VALUES = {
        "Low": {"min": 10, "max": 50},
        "Mid": {"min": 50, "max": 150},
        "High": {"min": 150, "max": 400},
        "Epic": {"min": 400, "max": 1000}
    }
    
    @staticmethod
    def generate_npc_stats(role, tier, level=None):
        """Generate NPC stats based on role and tier"""
        if tier not in NPCGenerator.TIER_ATTRIBUTE_RANGES:
            tier = "Low"
        
        tier_range = NPCGenerator.TIER_ATTRIBUTE_RANGES[tier]
        role_bias = NPCGenerator.ROLE_STAT_BIASES.get(role, {})
        
        # Generate base attributes
        attributes = {}
        for attr in ["physical", "mental", "spiritual", "social"]:
            base = tier_range["base"]
            bias = role_bias.get(attr, 0)
            min_val = max(tier_range["min"], base + bias - 2)
            max_val = min(tier_range["max"], base + bias + 2)
            attributes[attr] = random.randint(min_val, max_val)
        
        # Calculate HP based on tier and role
        hp_multiplier = role_bias.get("hp_multiplier", 1.0)
        base_hp = tier_range["base"] * 10
        max_health = int(base_hp * hp_multiplier)
        
        # Set level based on tier if not provided
        if level is None:
            if tier == "Low":
                level = random.randint(1, 5)
            elif tier == "Mid":
                level = random.randint(6, 10)
            elif tier == "High":
                level = random.randint(11, 15)
            else:  # Epic
                level = random.randint(16, 20)
        
        # Calculate EXP value
        exp_range = NPCGenerator.TIER_EXP_VALUES.get(tier, {"min": 10, "max": 50})
        exp_value = random.randint(exp_range["min"], exp_range["max"])
        
        # Bosses get more EXP
        if role == "Boss":
            exp_value = int(exp_value * 2.5)
        
        # Minions get less EXP
        if role == "Minion":
            exp_value = int(exp_value * 0.5)
        
        return {
            "attributes": attributes,
            "max_health": max_health,
            "health": max_health,
            "level": level,
            "exp_value": exp_value,
            "tier": tier,
            "combat_role": role
        }
    
    @staticmethod
    def generate_npc_skills(role, tier, level):
        """Generate skills based on role"""
        skills = {}
        
        # Base skill level based on tier
        base_skill = {
            "Low": 5,
            "Mid": 15,
            "High": 30,
            "Epic": 50
        }.get(tier, 5)
        
        # Role-specific skill focuses
        role_skills = {
            "Brute": ["fighting", "dodging", "climbing"],
            "Minion": ["fighting"],
            "Boss": ["fighting", "dodging", "tracking", "investigating", "channeling"],
            "Artillery": ["throwing", "tracking", "investigating"],
            "Healer": ["channeling", "warding", "meditating"],
            "Controller": ["channeling", "binding", "investigating", "tracking"]
        }
        
        focus_skills = role_skills.get(role, ["fighting"])
        
        # Set skills
        for skill in ["fighting", "dodging", "climbing", "swimming", "throwing",
                     "tracking", "investigating", "remembering", "lockpicking", "brewing",
                     "praying", "meditating", "channeling", "warding", "binding",
                     "persuading", "intimidating", "deceiving", "leading", "bargaining",
                     "repairing", "smithing", "taming"]:
            if skill in focus_skills:
                skills[skill] = base_skill + random.randint(0, 10)
            else:
                skills[skill] = max(1, base_skill - random.randint(5, 15))
        
        return skills
    
    @staticmethod
    def create_npc(npc_id, name, description, role="Brute", tier="Low", level=None):
        """Create a fully generated NPC"""
        from mud_server import NPC
        
        npc = NPC(npc_id, name, description)
        
        # Generate stats
        stats = NPCGenerator.generate_npc_stats(role, tier, level)
        npc.attributes = stats["attributes"]
        npc.max_health = stats["max_health"]
        npc.health = stats["max_health"]
        npc.level = stats["level"]
        npc.exp_value = stats["exp_value"]
        npc.tier = stats["tier"]
        npc.combat_role = stats["combat_role"]
        
        # Generate skills
        npc.skills = NPCGenerator.generate_npc_skills(role, tier, npc.level)
        
        # Set hostility based on role (default)
        if role in ["Brute", "Boss", "Minion"]:
            npc.is_hostile = True
        else:
            npc.is_hostile = False
        
        # Set mana/stamina based on attributes
        npc.max_mana = npc.attributes["spiritual"] * 5
        npc.mana = npc.max_mana
        npc.max_stamina = npc.attributes["physical"] * 10
        npc.stamina = npc.max_stamina
        
        return npc
