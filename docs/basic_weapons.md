# Weapon Master List – Basic Weapons

This document defines the **baseline weapon templates** available in the early game. These weapons are **unmodified templates** and form the foundation for crafting, modifiers, loot generation, and maneuver requirements.

All values are balanced for **Low–Mid Tier play** and assume:

- Dodging determines hit
    
- Armor provides damage reduction by damage type
    
- Speed represents **action cost** (lower = faster)
    

---

## Melee Weapons

### Longsword

```
{
  "id": "longsword",
  "name": "Longsword",
  "category": "Melee",
  "class": "Sword",
  "hands": 1,
  "range": 0,
  "damage_min": 4,
  "damage_max": 5,
  "damage_type": "slashing",
  "crit_chance": 0.20,
  "speed_cost": 1.0,
  "durability": 50
}
```

---

### Shortsword

```
{
  "id": "shortsword",
  "name": "Shortsword",
  "category": "Melee",
  "class": "Sword",
  "hands": 1,
  "range": 0,
  "damage_min": 3,
  "damage_max": 4,
  "damage_type": "piercing",
  "crit_chance": 0.25,
  "speed_cost": 0.9,
  "durability": 45
}
```

---

### Dagger

```
{
  "id": "dagger",
  "name": "Dagger",
  "category": "Melee",
  "class": "Dagger",
  "hands": 1,
  "range": 0,
  "damage_min": 2,
  "damage_max": 3,
  "damage_type": "piercing",
  "crit_chance": 0.35,
  "speed_cost": 0.7,
  "durability": 30
}
```

---

### Mace

```
{
  "id": "mace",
  "name": "Mace",
  "category": "Melee",
  "class": "Mace",
  "hands": 1,
  "range": 0,
  "damage_min": 4,
  "damage_max": 6,
  "damage_type": "bludgeoning",
  "crit_chance": 0.15,
  "speed_cost": 1.1,
  "durability": 60
}
```

---

### Warhammer

```
{
  "id": "warhammer",
  "name": "Warhammer",
  "category": "Melee",
  "class": "Hammer",
  "hands": 2,
  "range": 0,
  "damage_min": 6,
  "damage_max": 8,
  "damage_type": "bludgeoning",
  "crit_chance": 0.10,
  "speed_cost": 1.4,
  "durability": 70
}
```

---

### Axe

```
{
  "id": "axe",
  "name": "Axe",
  "category": "Melee",
  "class": "Axe",
  "hands": 1,
  "range": 0,
  "damage_min": 5,
  "damage_max": 7,
  "damage_type": "slashing",
  "crit_chance": 0.18,
  "speed_cost": 1.2,
  "durability": 55
}
```

---

### Pickaxe

```
{
  "id": "pickaxe",
  "name": "Pickaxe",
  "category": "Melee",
  "class": "Pick",
  "hands": 1,
  "range": 0,
  "damage_min": 4,
  "damage_max": 6,
  "damage_type": "piercing",
  "crit_chance": 0.22,
  "speed_cost": 1.2,
  "durability": 65
}
```

---

### Spear

```
{
  "id": "spear",
  "name": "Spear",
  "category": "Melee",
  "class": "Spear",
  "hands": 2,
  "range": 1,
  "damage_min": 4,
  "damage_max": 6,
  "damage_type": "piercing",
  "crit_chance": 0.20,
  "speed_cost": 1.1,
  "durability": 55
}
```

---

## Ranged Weapons

### Shortbow

```
{
  "id": "shortbow",
  "name": "Shortbow",
  "category": "Ranged",
  "class": "Bow",
  "hands": 2,
  "range": 5,
  "damage_min": 3,
  "damage_max": 5,
  "damage_type": "piercing",
  "crit_chance": 0.18,
  "speed_cost": 1.0,
  "durability": 40
}
```

---

### Longbow

```
{
  "id": "longbow",
  "name": "Longbow",
  "category": "Ranged",
  "class": "Bow",
  "hands": 2,
  "range": 7,
  "damage_min": 4,
  "damage_max": 6,
  "damage_type": "piercing",
  "crit_chance": 0.20,
  "speed_cost": 1.2,
  "durability": 45
}
```

---

### Sling

```
{
  "id": "sling",
  "name": "Sling",
  "category": "Ranged",
  "class": "Sling",
  "hands": 1,
  "range": 4,
  "damage_min": 2,
  "damage_max": 4,
  "damage_type": "bludgeoning",
  "crit_chance": 0.25,
  "speed_cost": 0.9,
  "durability": 35
}
```

---

## Design Notes

- All weapons are intentionally **simple and readable**
    
- Damage ranges overlap to prevent strict best-in-slot choices
    
- Speed and crit chance create distinct play styles
    
- Modifiers and maneuvers provide long-term differentiation
    

These templates serve as the foundation for crafting, loot generation, and progression.

---

## Weapon Modifiers

Weapon modifiers alter a base weapon template to create distinct materials, cultures, and crafting identities. Modifiers do **not** replace the base weapon stats; they apply additive or multiplicative changes.

Modifiers may adjust:

- Damage
    
- Crit chance
    
- Speed cost
    
- Durability
    
- Damage type (rarely)
    

Modifiers are applied at item creation or crafting time.

### Bone Modifier

```
{
  "id": "bone",
  "name": "Bone",
  "damage_bonus": 0,
  "crit_bonus": 0.06,
  "speed_multiplier": 1.0,
  "durability_bonus": -30,
  "notes": "Lightweight, brittle, common among tribal cultures"
}
```

---

### Wood Modifier

```
{
  "id": "wood",
  "name": "Wood",
  "damage_bonus": -1,
  "crit_bonus": 0.02,
  "speed_multiplier": 0.9,
  "durability_bonus": -20,
  "notes": "Cheap and fast, unsuitable for heavy combat"
}
```

---

### Coral Modifier

```
{
  "id": "coral",
  "name": "Coral",
  "damage_bonus": 0,
  "crit_bonus": 0.04,
  "speed_multiplier": 1.0,
  "durability_bonus": -10,
  "damage_type_override": "piercing",
  "notes": "Favored by Unflooded Sea cultures, serrated and sharp"
}
```

---

### Blacksteel Modifier

```
{
  "id": "blacksteel",
  "name": "Blacksteel",
  "damage_bonus": 1,
  "crit_bonus": 0.03,
  "speed_multiplier": 1.1,
  "durability_bonus": 40,
  "notes": "Dense and durable alloy, rare and highly valued"
}
```

---

### Glass Modifier

```
{
  "id": "glass",
  "name": "Glass",
  "damage_bonus": 2,
  "crit_bonus": 0.10,
  "speed_multiplier": 0.85,
  "durability_bonus": -40,
  "notes": "Extremely sharp but fragile; devastating on critical hits"
}
```

---

### Shell Modifier

```
{
  "id": "shell",
  "name": "Shell",
  "damage_bonus": 0,
  "crit_bonus": 0.03,
  "speed_multiplier": 1.0,
  "durability_bonus": 10,
  "notes": "Resilient organic material used by coastal and Crabfolk cultures"
}
```

---

## Modifier Application Rules

- Final damage is calculated after all bonuses are applied
    
- Speed multipliers stack multiplicatively
    
- Durability bonuses are applied once at creation
    
- Some modifiers may be restricted by culture, faction, or region
    

Example final item:

**Bone Longsword**

- Base: Longsword
    
- Modifier: Bone
    
- Result: Higher crit chance, lower durability