# MUD Character Progression & Skill System

## Level Tiers

- **Low Tier:** Levels **1–5**
    
- **Mid Tier:** Levels **6–10**
    
- **High Tier:** Levels **11–15**
    
- **Epic Tier:** Levels **16+**
    

**Tier intent**

- **Low:** Survival & identity
    
- **Mid:** Specialization & reputation
    
- **High:** Mastery & influence
    
- **Epic:** Myth & world impact
    

---

## Skills

### Skill Range

- Skills range from **1–100**.
    

### Training vs Use

- Skills are **trainable up to 20** (trainers, books, guilds, starting bonuses).
    
- After **20**, skills increase **only through use**.
    

### Naming Convention

- All skills end with **“ing”** (e.g., **Dodging, Thieving, Climbing**).
    
- If a verb sounds awkward with “-ing,” rename the action (keep the convention consistent).
    

### Suggested Skill Categories (Examples)

**Physical**

- Fighting
    
- Dodging
    
- Climbing
    
- Swimming
    
- Throwing
    

**Mental**

- Tracking
    
- Investigating
    
- Remembering
    
- Lockpicking
    
- Brewing / Mixing _(avoid awkward “Alchemying” unless you like the tone)_
    

**Spiritual**

- Praying
    
- Meditating
    
- Channeling
    
- Warding
    
- Binding
    

**Social**

- Persuading
    
- Intimidating
    
- Deceiving
    
- Leading
    
- Bargaining
    

**Crafting & Handling**

- Repairing _(repair damaged weapons, armor, tools)_
    
- Smithing _(forge weapons, armor, metal items)_
    
- Taming _(tame, calm, and bond with animals)_
    

---

## Attributes → Skills & Maneuvers

### Attribute Model

Attributes:

- **Physical**
    
- **Mental**
    
- **Spiritual**
    
- **Social**
    

Attributes provide **bonuses to skills** in their areas and **improve maneuver effectiveness** (damage, duration, secondary effects, etc.).

### Skill Attribute Mapping

Each skill has:

- **Primary Attribute** (full bonus)
    
- **Secondary Attribute** (half bonus)
    

Example:

- **Dodging** → Primary: **Physical**, Secondary: **Mental**
    

### Attribute Bonus (Example Formula)

> Tune this, but keep it consistent.

- **Attribute Bonus = floor((Attribute - 5) / 2)**
    

Example table:

- 3–4 → **-1**
    
- 5–6 → **0**
    
- 7–8 → **+1**
    
- 9–10 → **+2**
    
- 11+ → **+3+**
    

### Effective Skill (Used for Checks)

**Effective Skill** =

- Skill Rank
    
- - Primary Attribute Bonus
        
- - Secondary Attribute Bonus (rounded down)
        
- - Situational Modifiers (gear, buffs, terrain, status)
        

---

## Unified Skill Check Mechanic

### Core Check

- Roll **d100**
    
- **Success if**: `Roll ≤ Effective Skill`
    

This is the **single consistent mechanic** used across the game.

### Degrees of Success (Recommended)

- **Critical Success:** `Roll ≤ Effective Skill ÷ 10`
    
- **Success:** `Roll ≤ Effective Skill`
    
- **Failure:** `Roll > Effective Skill`
    
- **Critical Failure:** `Roll ≥ 95`
    

_(Optional: Epic tier can shift critical thresholds.)_

### Difficulty Modifiers

Apply difficulty as a modifier to **Effective Skill** (not the roll):

- **Trivial:** +30
    
- **Easy:** +15
    
- **Standard:** +0
    
- **Hard:** -15
    
- **Extreme:** -30
    
- **Legendary:** -50
    

---

## Skill Advancement Through Use

After a check:

- On **success** → chance to gain skill
    
- On **failure** → smaller chance (learning from mistakes)
    
- Chance decreases as skill increases
    

Example concept:

- **Gain Chance** = `(100 - Skill Rank) × Activity Modifier`
    

_(Exact tuning TBD.)_

---

## Maneuvers

Maneuvers are **special actions and spells** that players learn from **masters** they must seek out throughout the world. They represent trained techniques, secret knowledge, and rare teachings — not generic abilities.

---

## Maneuver Acquisition

### Learning Maneuvers

- Maneuvers are taught by **NPC masters** (fighters, sages, priests, beastspeakers, etc.)
    
- Masters require the player to meet **prerequisites** before teaching:
    
    - Minimum **Level** (tier-gated)
        
    - Minimum **Skill Rank** (relevant skill)
        
    - Sometimes reputation, quest completion, or faction standing
        

Example:

```
Master Requirement:
- Level 6+
- Fighting 35+
- Dodging 25+
```

This reinforces:

- World exploration
    
- Social discovery
    
- Skill mastery
    

---

## Starting Maneuvers

Each new character begins with **two maneuvers**:

1. **Lower-Tier Maneuver (Choice)**
    
    - Chosen by the player at character creation
        
    - Must meet all prerequisites
        
    - Represents basic trained technique
        
2. **Planetary Maneuver (Granted)**
    
    - Granted automatically by the character’s **Planet**
        
    - Always considered a **Lower-Tier maneuver**
        
    - Unique to that planetary influence
        

This ensures:

- Early mechanical identity
    
- Planet choice has immediate impact
    
- No two characters feel identical at level 1
    

---

## Maneuver Tiers

Maneuvers are tiered and generally align with level tiers:

- **Lower Tier Maneuvers** → Levels 1–5
    
- **Mid Tier Maneuvers** → Levels 6–10
    
- **High Tier Maneuvers** → Levels 11–15
    
- **Epic Maneuvers** → Level 16+
    

Masters will **never teach maneuvers above your tier**.

---

## Maneuver Structure

Each maneuver defines:

- Required **Skill(s)**
    
- Scaling **Attribute(s)**
    
- Cost (stamina, mana, focus, etc.)
    
- Cooldown or usage limit
    
- Effects by outcome
    

Example:

```
Shield Bashing
Tier: Lower
Skills: Fighting
Attributes: Physical
Cost: Stamina

Success: Damage + stagger
Critical: Knockdown
Failure: Miss
Critical Failure: Lose balance
```

---

## Maneuver Resolution

Maneuvers use the **same unified skill check system**:

```
Roll d100 ≤ Effective Skill → success
```

- Skills determine **success chance**
    
- Attributes scale **potency, duration, and secondary effects**
    
- No special-case math
    

---

## Maneuver Slots (Recommended)

To encourage meaningful choices:

- Players may **learn many maneuvers**
    
- Players may only **equip a limited number** at once
    

Example:

- Low Tier: 2 active maneuvers
    
- Mid Tier: 3 active maneuvers
    
- High Tier: 4 active maneuvers
    
- Epic Tier: 5+ active maneuvers
    

---

## Design Intent

- Maneuvers are **earned**, not handed out
    
- Masters matter as world content
    
- Planet choice gives immediate flavor
    
- Skill mastery gates power
    
- Epic maneuvers bend rules, not numbers
    

This keeps combat and magic grounded in the world instead of menus.