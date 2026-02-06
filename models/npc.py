"""NPC/Creature model for MUD world state."""

import random


class NPC:
    def __init__(self, npc_id, name, description):
        self.npc_id = npc_id
        self.name = name
        self.description = description
        self.health = 50
        self.max_health = 50
        self.mana = 25
        self.max_mana = 25
        self.stamina = 50
        self.max_stamina = 50
        self.attributes = {"physical": 10, "mental": 10, "spiritual": 10, "social": 10}
        self.skills = {}
        self.combat_role = None
        self.tier = "Low"
        self.level = 1
        self.exp_value = 0
        self.known_maneuvers = []
        self.active_maneuvers = []
        self.equipped = {}
        self.is_hostile = False
        self.aggression = {"type": "passive"}
        self.combat_state = "Observing"
        self.combat_target = None
        self.initiative = 0
        self.loot_table = []
        self.outlooks = {}
        self.faction_outlooks = {}
        self.dialogue = []
        self.inventory = []

    def get_tier(self):
        if self.level <= 5:
            return "Low"
        elif self.level <= 10:
            return "Mid"
        elif self.level <= 15:
            return "High"
        return "Epic"

    def get_attribute_bonus(self, attribute):
        if attribute not in self.attributes:
            return 0
        return (self.attributes[attribute] - 5) // 2

    def roll_skill_check(self, skill_name, difficulty_mod=0):
        base_skill = self.skills.get(skill_name, 1)
        effective_skill = max(1, base_skill + difficulty_mod)
        roll = random.randint(1, 100)
        if roll <= effective_skill // 10:
            return {"result": "critical", "roll": roll, "skill": effective_skill, "effective_skill": effective_skill}
        elif roll <= effective_skill:
            return {"result": "success", "roll": roll, "skill": effective_skill, "effective_skill": effective_skill}
        return {"result": "failure", "roll": roll, "skill": effective_skill, "effective_skill": effective_skill}

    def to_dict(self):
        result = {
            "npc_id": self.npc_id,
            "name": self.name,
            "description": self.description,
            "health": self.health,
            "max_health": self.max_health,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "stamina": self.stamina,
            "max_stamina": self.max_stamina,
            "attributes": self.attributes,
            "skills": self.skills,
            "combat_role": self.combat_role,
            "tier": self.tier,
            "level": self.level,
            "exp_value": self.exp_value,
            "known_maneuvers": self.known_maneuvers,
            "active_maneuvers": self.active_maneuvers,
            "equipped": self.equipped,
            "is_hostile": self.is_hostile,
            "aggression": self.aggression,
            "combat_state": self.combat_state,
            "loot_table": self.loot_table,
            "outlooks": self.outlooks,
            "faction_outlooks": self.faction_outlooks,
            "dialogue": self.dialogue,
            "inventory": self.inventory,
        }
        if hasattr(self, "shop_inventory"):
            result["shop_inventory"] = self.shop_inventory
        if hasattr(self, "keywords"):
            result["keywords"] = self.keywords
        if hasattr(self, "is_merchant"):
            result["is_merchant"] = self.is_merchant
        if hasattr(self, "faction"):
            result["faction"] = self.faction
        return result

    def from_dict(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        self.tier = self.get_tier()
        # Infer aggression from is_hostile if no explicit aggression block
        if "aggression" not in data and self.is_hostile:
            self.aggression = {"type": "aggressive", "radius_rooms": 0}
