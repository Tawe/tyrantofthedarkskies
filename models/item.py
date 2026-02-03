"""Item model (weapons, armor, consumables) for MUD world state."""


class Item:
    def __init__(self, item_id, name, description, item_type="item"):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.item_type = item_type
        self.value = 0
        self.stats = {}
        self.food_effect = None
        self.potion_heal = None
        self.drink_heal = None
        self.weapon_template_id = None
        self.weapon_modifier_id = None
        self.current_durability = None
        self.category = None
        self.weapon_class = None
        self.hands = 1
        self.range = 0
        self.damage_min = 0
        self.damage_max = 0
        self.damage_type = None
        self.crit_chance = 0.0
        self.speed_cost = 1.0
        self.max_durability = 50
        self.armor_type = None
        self.slot = None
        self.damage_reduction = {}
        self.armor_slots = []
        self.primary_damage_type = None
        self.damage_types = []
        self.weight = 0
        self.armor_template_id = None
        self.armor_modifier_id = None

    def is_armor(self):
        return self.item_type == "armor" or self.armor_type is not None

    def get_armor_slot(self):
        if self.slot:
            return self.slot
        if self.armor_slots:
            s = self.armor_slots[0].lower()
            if s == "body":
                return "chest"
            if s == "offhand":
                return "shield"
            return s
        return "chest"

    def get_dr_for_damage_type(self, damage_type):
        if not self.damage_reduction:
            return 0
        cur = self.get_current_durability() if hasattr(self, "get_current_durability") else getattr(self, "current_durability", None)
        if cur is not None and cur <= 0:
            return 0
        base_dr = self.damage_reduction.get(damage_type, 0)
        if base_dr <= 0:
            return 0
        if self.primary_damage_type and damage_type == self.primary_damage_type:
            return base_dr
        if self.damage_types and damage_type in self.damage_types:
            return max(0, int(base_dr * 0.75))
        return base_dr

    def reduce_armor_hp(self, amount):
        if self.current_durability is None:
            self.current_durability = self.max_durability if self.max_durability else 50
        self.current_durability = max(0, self.current_durability - amount)
        return self.current_durability <= 0

    def get_effective_damage(self):
        return (self.damage_min, self.damage_max)

    def get_effective_crit_chance(self):
        return self.crit_chance

    def get_effective_speed_cost(self):
        return self.speed_cost

    def get_current_durability(self):
        if self.current_durability is None:
            return self.max_durability
        return self.current_durability

    def reduce_durability(self, amount=1):
        if self.current_durability is None:
            self.current_durability = self.max_durability
        self.current_durability = max(0, self.current_durability - amount)
        return self.current_durability <= 0

    def is_weapon(self):
        return self.item_type == "weapon" or self.category in ["Melee", "Ranged"]

    def to_dict(self):
        result = {
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type,
            "value": self.value,
            "stats": self.stats,
        }
        if self.is_weapon():
            result.update(
                weapon_template_id=self.weapon_template_id,
                weapon_modifier_id=self.weapon_modifier_id,
                current_durability=self.current_durability,
                category=self.category,
                weapon_class=self.weapon_class,
                hands=self.hands,
                range=self.range,
                damage_min=self.damage_min,
                damage_max=self.damage_max,
                damage_type=self.damage_type,
                crit_chance=self.crit_chance,
                speed_cost=self.speed_cost,
                max_durability=self.max_durability,
            )
        if self.is_armor():
            result.update(
                armor_type=self.armor_type,
                slot=self.slot,
                damage_reduction=self.damage_reduction,
                armor_slots=self.armor_slots,
                primary_damage_type=self.primary_damage_type,
                damage_types=getattr(self, "damage_types", []) or [],
                weight=getattr(self, "weight", 0),
                armor_template_id=getattr(self, "armor_template_id", None),
                armor_modifier_id=getattr(self, "armor_modifier_id", None),
                current_durability=self.current_durability,
                max_durability=getattr(self, "max_durability", 50),
            )
        return result

    def from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
