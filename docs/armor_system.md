# Armor System

This document defines how **armor functions as damage reduction**, how armor pieces are constructed from **base templates + material modifiers**, and how armor **degrades and is repaired**.

The system mirrors weapons for consistency and composability.

---

## Design Goals

- Armor mitigates damage via **Damage Reduction (DR)**, not avoidance
    
- **Dodging** determines whether an attack hits
    
- Armor applies **after a hit is confirmed**
    
- Armor supports **multiple damage types**, with one primary focus
    
- Armor degrades organically through use
    
- Base templates + material modifiers allow large item variety with minimal data
    

---

## Armor Overview

Armor pieces are equippable items that reduce incoming damage of specific types.

Each armor piece:

- reduces damage after hit resolution
    
- applies reduction only to matching damage types
    
- loses durability proportional to the damage it absorbs
    

---

## Armor Properties

Each armor item has the following core properties:

- **Name** — Display name
    
- **Slot** — Where it is worn (head, chest, arms, legs, shield, etc.)
    
- **Weight** — Affects movement, dodging, and stamina (future-facing)
    
- **Damage Reduction (DR)** — Numeric value subtracted from incoming damage
    
- **Damage Types Protected** — One or more damage types
    
- **Primary Damage Type** — The armor’s main defensive focus
    
- **HP (Durability)** — Current and max durability
    

---

## Damage Reduction Model

1. Attack hits (via accuracy vs dodging)
    
2. Incoming damage is rolled
    
3. Armor DR is applied **per armor piece** that protects against the damage type
    
4. Final damage is applied to HP
    

**Example:**

- Incoming slashing damage: 10
    
- Chest armor DR (slashing): 3
    
- Arm guards DR (slashing): 1
    
- Final damage taken: 6
    

---

## Armor Degradation

Armor degrades based on **how much damage it prevents**.

### Degradation Rule

- Armor HP is reduced by the **amount of damage it absorbed**
    
- Damage that passes through armor does **not** degrade it
    

**Example:**

- Armor DR absorbs 4 damage
    
- Armor loses 4 durability HP
    

When armor reaches 0 HP:

- It provides **no damage reduction**
    
- It remains equipped but is considered **broken**
    

---

## Repairing Armor

Armor can be repaired via:

- NPC services (e.g., Jalia’s Repairs)
    
- Player skills (Repairing, Smithing)
    

Repairing restores armor HP but may:

- cost materials
    
- cost currency
    
- be limited by skill level
    

---

## Base Armor Templates

Armor templates define the **shape and defensive role** of a piece.

### Example Template: Leather Jerkin

```
{
  "template_id": "leather_jerkin",
  "name": "Leather Jerkin",
  "slot": "chest",
  "weight": 6,
  "base_dr": 2,
  "primary_damage_type": "slashing",
  "damage_types": ["slashing", "piercing"],
  "max_hp": 40
}
```

---

## Armor Material Modifiers

Material modifiers alter the base template.

Modifiers may affect:

- Damage Reduction
    
- Weight
    
- HP (durability)
    
- Damage types covered
    

### Example Modifier: Bone

```
{
  "modifier_id": "bone",
  "name": "Bone",
  "dr_bonus": 0,
  "weight_modifier": -1,
  "hp_bonus": -15,
  "notes": "Lightweight but brittle"
}
```

---

## Final Armor Item Construction

An armor item is constructed as:

```
{
  "name": "Bone Leather Jerkin",
  "armor_template": "leather_jerkin",
  "modifier": "bone"
}
```

Final stats are derived at creation time.

---

## Multiple Damage Types

Armor may protect against multiple damage types:

- **Primary type**: full DR applies
    
- **Secondary types**: reduced effectiveness (e.g., 50–75%)
    

This allows:

- layered defenses
    
- specialized gear
    
- meaningful tradeoffs
    

---

## Shields (Special Case)

Shields are armor pieces that:

- occupy a hand slot
    
- provide DR against frontal attacks
    
- may grant block-related maneuvers
    

Shields degrade faster due to frequent absorption.

---

## Stacking Rules

- DR stacks across multiple armor pieces
    
- DR does not reduce damage below 0
    
- Armor DR does not apply to damage types it does not protect against
    

---

## Integration with Combat System

- Dodging determines hit/miss
    
- Armor applies after hit confirmation
    
- Armor degradation occurs during damage resolution
    
- Broken armor should be clearly messaged to players
    

---

## Design Notes

- Early armor provides modest DR to keep combat dangerous
    
- Material choice matters as much as template
    
- Degradation reinforces repair economy and downtime loops
    
- System supports future extensions (enchantments, resistances, shields, set bonuses)