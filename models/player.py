"""Player class and player data management."""

import time
import random

class Player:
    def __init__(self, name, connection, address):
        self.name = name
        self.connection = connection
        self.address = address
        self.room_id = "black_anchor_common"
        self.health = 100
        self.max_health = 100
        self.mana = 50
        self.max_mana = 50
        self.stamina = 100
        self.max_stamina = 100
        self.level = 1
        self.experience = 0
        self.gold = 120
        self.inventory = []
        self.equipped = {}
        
        # New attribute system
        self.attributes = {
            "physical": 10,
            "mental": 10,
            "spiritual": 10,
            "social": 10
        }
        
        # Skills system
        self.skills = {
            # Physical skills
            "fighting": 1,
            "dodging": 1,
            "climbing": 1,
            "swimming": 1,
            "throwing": 1,
            
            # Mental skills
            "tracking": 1,
            "investigating": 1,
            "remembering": 1,
            "lockpicking": 1,
            "brewing": 1,
            
            # Spiritual skills
            "praying": 1,
            "meditating": 1,
            "channeling": 1,
            "warding": 1,
            "binding": 1,
            
            # Social skills
            "persuading": 1,
            "intimidating": 1,
            "deceiving": 1,
            "leading": 1,
            "bargaining": 1,
            
            # Crafting skills
            "repairing": 1,
            "smithing": 1,
            "taming": 1
        }
        
        # Skill attribute mapping
        self.skill_attributes = {
            "fighting": {"primary": "physical", "secondary": "mental"},
            "dodging": {"primary": "physical", "secondary": "mental"},
            "climbing": {"primary": "physical", "secondary": None},
            "swimming": {"primary": "physical", "secondary": None},
            "throwing": {"primary": "physical", "secondary": "mental"},
            
            "tracking": {"primary": "mental", "secondary": "physical"},
            "investigating": {"primary": "mental", "secondary": "social"},
            "remembering": {"primary": "mental", "secondary": None},
            "lockpicking": {"primary": "mental", "secondary": "physical"},
            "brewing": {"primary": "mental", "secondary": "spiritual"},
            
            "praying": {"primary": "spiritual", "secondary": "social"},
            "meditating": {"primary": "spiritual", "secondary": "mental"},
            "channeling": {"primary": "spiritual", "secondary": "mental"},
            "warding": {"primary": "spiritual", "secondary": "mental"},
            "binding": {"primary": "spiritual", "secondary": None},
            
            "persuading": {"primary": "social", "secondary": "mental"},
            "intimidating": {"primary": "social", "secondary": "physical"},
            "deceiving": {"primary": "social", "secondary": "mental"},
            "leading": {"primary": "social", "secondary": None},
            "bargaining": {"primary": "social", "secondary": "mental"},
            
            "repairing": {"primary": "physical", "secondary": "mental"},
            "smithing": {"primary": "physical", "secondary": None},
            "taming": {"primary": "social", "secondary": "spiritual"}
        }
        
        # Maneuver system
        self.known_maneuvers = []
        self.active_maneuvers = []
        self.max_maneuvers = 2
        self.planet = "earth"  # Default planet
        
        self.is_logged_in = True
        self.last_command_time = time.time()
        self.skill_use_tracking = {}  # Track skill use for advancement
        self.creation_state = None  # Character creation state
        self.race = None  # Character race
        self.starsign = None  # Character starsign
        self.fated_mark = None  # Character's fated mark
        self.free_attribute_points = 0  # For human free points
        self.gift_maneuver = None  # Planet gift maneuver
        self.firebase_uid = None  # Firebase Authentication UID
        self.email = None  # Email address for Firebase Auth
        
    def to_dict(self):
        """
        Serialize player data to dictionary.
        NOTE: Does NOT include 'address' or 'connection' for security/privacy reasons.
        These are server-only and should never be persisted or exposed to players.
        """
        return {
            "name": self.name,
            "room_id": self.room_id,
            "health": self.health,
            "max_health": self.max_health,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "stamina": self.stamina,
            "max_stamina": self.max_stamina,
            "level": self.level,
            "experience": self.experience,
            "gold": self.gold,
            "inventory": self.inventory,
            "equipped": self.equipped,
            "attributes": self.attributes,
            "skills": self.skills,
            "known_maneuvers": self.known_maneuvers,
            "active_maneuvers": self.active_maneuvers,
            "planet": self.planet,
            "race": self.race,
            "starsign": self.starsign,
            "free_attribute_points": self.free_attribute_points,
            "gift_maneuver": self.gift_maneuver,
            "creation_state": self.creation_state,
            "firebase_uid": self.firebase_uid,
            "email": self.email
            # NOTE: 'address' and 'connection' are intentionally excluded
            # They are server-only data and should never be serialized or exposed
        }
    
    def from_dict(self, data):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
    def get_tier(self):
        """Get player's tier based on level"""
        if self.level <= 5:
            return "Low"
        elif self.level <= 10:
            return "Mid"
        elif self.level <= 15:
            return "High"
        else:
            return "Epic"
            
    def get_max_maneuvers(self):
        """Get maximum active maneuvers based on tier"""
        tier = self.get_tier()
        if tier == "Low":
            return 2
        elif tier == "Mid":
            return 3
        elif tier == "High":
            return 4
        else:
            return 5
            
    def get_attribute_bonus(self, attribute):
        """Calculate attribute bonus using formula: floor((attribute - 5) / 2)"""
        return (self.attributes.get(attribute, 10) - 5) // 2
        
    def get_effective_skill(self, skill_name, difficulty_mod=0):
        """Calculate effective skill with attribute bonuses and difficulty modifiers"""
        if skill_name not in self.skills:
            return 0
            
        base_skill = self.skills[skill_name]
        skill_attrs = self.skill_attributes.get(skill_name, {})
        
        # Add primary attribute bonus
        primary_attr = skill_attrs.get("primary")
        if primary_attr:
            base_skill += self.get_attribute_bonus(primary_attr)
            
        # Add secondary attribute bonus (half)
        secondary_attr = skill_attrs.get("secondary")
        if secondary_attr:
            base_skill += self.get_attribute_bonus(secondary_attr) // 2
            
        # Apply difficulty modifier
        base_skill += difficulty_mod
        
        return max(0, base_skill)
        
    def roll_skill_check(self, skill_name, difficulty_mod=0):
        """Perform unified d100 skill check"""
        effective_skill = self.get_effective_skill(skill_name, difficulty_mod)
        roll = random.randint(1, 100)
        
        # Determine degrees of success
        critical_threshold = effective_skill // 10
        
        if roll <= critical_threshold:
            result = "critical"
        elif roll <= effective_skill:
            result = "success"
        elif roll >= 95:
            result = "critical_failure"
        else:
            result = "failure"
            
        return {
            "roll": roll,
            "effective_skill": effective_skill,
            "result": result,
            "skill": skill_name
        }
        
    def check_skill_advancement(self, skill_name, success):
        """Check if skill should advance after use"""
        if skill_name not in self.skills:
            return
            
        current_skill = self.skills[skill_name]
        
        # Don't advance beyond 100
        if current_skill >= 100:
            return
            
        # Track usage
        if skill_name not in self.skill_use_tracking:
            self.skill_use_tracking[skill_name] = {"successes": 0, "failures": 0, "total": 0}
            
        self.skill_use_tracking[skill_name]["total"] += 1
        if success:
            self.skill_use_tracking[skill_name]["successes"] += 1
        else:
            self.skill_use_tracking[skill_name]["failures"] += 1
            
        # Skill gain chance decreases as skill increases
        base_chance = (100 - current_skill) * 0.1  # Simple formula for now
        if success:
            gain_chance = base_chance
        else:
            gain_chance = base_chance * 0.3  # Lower chance on failure
            
        if random.randint(1, 100) <= int(gain_chance):
            self.skills[skill_name] = min(100, current_skill + 1)
            return True
            
        return False
