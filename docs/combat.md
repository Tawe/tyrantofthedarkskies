# Combat Master System

This document defines the **core combat philosophy, flow, and rules** for the game. Combat is designed to be **tactical, readable, social, and low‑clunk**, suitable for a text‑based MUD while remaining deep and expressive.

Combat is a **shared room-level system**, not a private instance.

---

## Core Design Pillars

- **Decision-driven**, not spam-driven
    
- **Stateful** rather than repetitive
    
- **Readable at a glance**
    
- **Role-expressive** (Brute, Minion, Controller, etc.)
    
- **Drop-in / Drop-out multiplayer friendly**
    
- **Environment-aware**
    

---

## Combat Scope

- Combat exists at the **room level**
    
- All players and NPCs in the room can see the combat state
    
- Players are **never auto-joined** into combat
    

---

## Combat States (Per Entity)

Each combatant may have one or more of the following states:

- **Observing** – In the room, not involved
    
- **Engaged** – Actively fighting a target
    
- **Supporting** – Assisting allies without direct engagement
    
- **Disengaging** – Attempting to leave combat
    
- **Exposed** – Vulnerable to increased damage
    
- **Pinned** – Movement restricted
    
- **Staggered** – Reduced effectiveness
    

States are **explicitly shown** to players.

---

## Turn Structure

Combat proceeds in **rounds**, each composed of clear phases.

### 1. Initiative Phase (once per combat)

- Initiative is rolled when combat begins
    
- Initiative order is **fixed**
    
- New participants are inserted **at the end of the current round**
    

---

### 2. Action Phase

On their turn, a combatant may:

- Perform **one primary action** (attack, maneuver, cast, etc.)
    
- Perform **one minor action** (move, ready, interact)
    

Basic attacks are always available but are **fallback options**.

---

### 3. Reaction Phase

Certain maneuvers or traits allow **reactions**:

- Interrupts
    
- Opportunity attacks
    
- Defensive triggers
    

Reactions are limited to prevent spam.

---

### 4. Resolution Phase

- Damage is applied
    
- States are updated
    
- Death / defeat is checked
    

---

### 5. Summary Phase

At the end of each round, all participants see a concise summary:

```
Round Summary:
- Enemies: 3 remaining
- Player1: wounded
- Player2: stamina low
```

---

## Joining Combat (Multiplayer)

When a player enters a room with active combat:

```
Combat in progress:
- Player1 vs Kelp Flea Minions (3)
You are not yet involved.
```

Players may:

- `join combat`
    
- Attack a target directly
    
- Use support maneuvers on allies
    
- Observe or leave
    

No initiative reset occurs.

---

## Leaving Combat

Players may attempt to disengage:

- Requires a **Disengage action**
    
- May provoke reactions
    
- On success, player enters **Observing** state
    

Leaving the room while engaged carries risk.

---

## Role Expression

Combat roles strongly influence behavior:

- **Minions:** swarm, low awareness
    
- **Brutes:** pressure, soak damage
    
- **Artillery:** reposition, punish exposure
    
- **Healers:** sustain allies, avoid frontline
    
- **Controllers:** manipulate states and terrain
    
- **Bosses:** phases, rule bending
    

---

## Environment & Terrain

Rooms may have **combat tags**:

- `open`
    
- `cramped`
    
- `slick`
    
- `obscured`
    
- `elevated`
    

Maneuvers may reference these tags for bonuses or penalties.

---

## Defense Model (Hit & Mitigation)

Combat defense is split into two clear layers:

1. **Avoidance (Dodging)** – determines whether an attack hits at all
    
2. **Mitigation (Armor Damage Reduction)** – reduces damage **after** a hit occurs, based on damage type
    

### Dodging (Avoidance)

- **Dodging** is the primary mechanic that determines if you are hit by an attack.
    
- Attacks resolve as an **Accuracy vs Dodging** contest (exact formula defined in the Skill Check system).
    
- Maneuvers may:
    
    - Increase or decrease Dodging temporarily
        
    - Convert an incoming hit into a **glancing hit**
        
    - Enable reactions (parries, blocks, counter-steps)
        

**Design intent:** Players can read the outcome cleanly: _miss → hit → crit/glance_, rather than opaque hidden math.

### Armor (Mitigation)

- Armor provides **Damage Reduction (DR)** against **one or more damage types**.
    
- DR is applied **only when an attack hits**.
    
- Different armor types protect against different damage profiles (e.g., heavy plate vs slashing/bludgeoning, leathers vs piercing, etc.).
    
- Some damage types may partially bypass certain armor materials.
    

**Design intent:** Armor choice matters because the world has many damage types; players can prepare for regions and enemies.

---

## Damage & Failure Philosophy

- Failed actions still have **partial impact**
    
- “Nothing happens” turns are avoided
    
- Damage types and resistances matter
    

---

## Targeting & Threat (High-Level)

- Enemies evaluate threat dynamically
    
- Healing, control, and positioning generate threat
    
- Roles bias target selection
    

---

## Experience & Rewards

- EXP is granted for **meaningful participation**
    
- Participation includes damage, healing, and control
    
- Loot is rolled after combat ends
    

---

## Anti-Clunk Safeguards

- No initiative rerolls mid-combat
    
- No real-time spam requirements
    
- Limited reactions per round
    
- Clear combat state visibility
    

---

## Design Intent

Combat should feel like:

> _A shared tactical board game, narrated in text._

Players should understand why outcomes occur, feel agency every turn, and be able to meaningfully help others at any time.

## Autoattack Overview

### Core Rule

- `attack <target>` **starts combat** and enables **autoattack**.
    
- While autoattack is active, the player **does not** need to repeat `attack`.
    
- Re-issuing `attack` while autoattacking should either:
    
    - do nothing (“You are already attacking.”), or
        
    - switch targets (“You turn your focus to the Kelp Flea.”)
        
- Players may still use **maneuvers** at any time (subject to costs, cooldowns, range, and prerequisites).
    

### States

- **Autoattacking:** ticking basic attacks against current target
    
- **Paused:** no valid target (out of range, unreachable, target dead)
    
- **Stopped:** combat ended (no hostiles) or player disengaged / left room
    

---

## Attack Ticker (BAT + Speed)

Combat is driven by a repeating **attack ticker** (a timer) per combatant.

### Base Attack Tick

Define a global constant:

- **BAT (Base Attack Tick):** the default time between basic attacks using a standard weapon.
    

Recommended starting value:

- **BAT = 3.0 seconds (in-game seconds)**
    
    - With your time ratio (3×), that’s **1 real second** per BAT second.
        

### Weapon Speed Modifies BAT

Weapons already define `speed_cost` (lower = faster, higher = slower).

- **Player basic attack interval**:
    
    - `attack_interval = BAT × weapon.speed_cost`
        

Examples:

- Dagger (`speed_cost 0.7`) → interval = 2.1s
    
- Longsword (`speed_cost 1.0`) → interval = 3.0s
    
- Warhammer (`speed_cost 1.4`) → interval = 4.2s
    

### Creature/NPC Attack Profile

NPCs/Creatures have their own baseline attack values:

- `attack_interval` (direct) **or** `speed_cost` (to be applied to BAT)
    
- `accuracy` (or a combat skill like **Fighting**)
    
- `damage_min`, `damage_max`
    
- `damage_type`
    
- `crit_chance`
    

They may also have:

- `natural_weapon_tag` (bite, claw, sting)
    
- `preferred_range_band` (Engaged / Near / Far)
    

---

## Basic Attack vs Maneuvers

### Basic Attack

- Happens automatically on the attack ticker
    
- Uses weapon damage profile (or unarmed profile)
    
- Uses hit check (Accuracy vs Dodging)
    
- Applies armor DR by damage type
    

### Maneuvers

- Explicit player choice
    
- May consume resources / have cooldowns
    
- Do **not** disable autoattack unless the maneuver says so
    

Optional rule (recommended):

- Maneuvers can have an **action_cost** that delays the next autoattack tick by a small amount (e.g., +0.5–1.5s) to avoid “free” stacking.
    

---

## Unarmed Attack

Every character can fight unarmed.

### Unarmed Profile (Baseline)

- `damage_min: 1`
    
- `damage_max: 2`
    
- `damage_type: bludgeoning`
    
- `crit_chance: 0.10`
    
- `speed_cost: 0.8`
    
- `durability: n/a`
    

Unarmed uses the same rules:

- Hit check via Dodging
    
- Armor DR applies
    
- Maneuvers may enhance unarmed (future: martial schools)
    

---

## Starting & Stopping Combat

### Starting Combat

Combat starts when:

- A player uses `attack <target>`
    
- A hostile NPC attacks the player
    
- A maneuver that deals damage is used
    

### Ending Combat (Stop Conditions)

Combat stops for a player when:

- No hostile entities remain engaged with them **in the same room**, **or**
    
- The player successfully **disengages**, **or**
    
- The player changes rooms (see below)
    

When combat stops:

- Autoattack = off
    
- target cleared (or kept as “last target” for convenience)
    

---

## Leaving the Room During Combat

You have two viable designs; choose one globally for consistency.

### Option A (Simple): Leaving Ends Combat

- If the player changes rooms, combat ends immediately.
    
- Hostiles do not follow.
    

Pros: simplest, very MUD-classic Cons: encourages “exit kiting”

### Option B (Recommended): Disengage + Pursuit

Leaving a room while in combat requires a **Disengage** step.

#### Disengage

- Command: `disengage` (or `withdraw`)
    
- Resolves as a check (e.g., **Dodging** vs enemy **Fighting** or a flat difficulty)
    
- Success:
    
    - player shifts range to **Far** and gains a **Flee Window** (e.g., 3–5 seconds)
        
- Failure:
    
    - player remains Engaged and cannot exit this tick
        

#### Flee Window

- During the flee window, `move <dir>` is allowed.
    
- If the window expires, the player must disengage again.
    

#### Pursuit

Creatures can follow based on a **pursuit tag**:

- `pursue: none` (won’t follow)
    
- `pursue: short` (follows 1 room)
    
- `pursue: long` (follows multiple rooms)
    

Pursuit can be modified by role:

- Brute: short
    
- Minion: short/none
    
- Artillery: none
    
- Boss: long (only if designed)
    

Room flags can block pursuit:

- `safe` rooms prevent hostile entry
    
- `no_pursuit` prevents following
    

---

## Multi-Player Joining Combat (Compatibility)

When a second player enters a room with an active fight:

- They enter at **Far** range by default
    
- They can choose to:
    
    - `attack <target>` (starts autoattack)
        
    - use a maneuver
        
    - `advance` (close distance)
        

Enemies decide whether to switch targets using their AI template and threat rules.

---

## Messaging (Text Clarity)

- On attack start:
    
    - “You square up with Kelp Flea and begin attacking.”
        
- On autoattack tick:
    
    - “You slash the Kelp Flea for 4 (reduced by armor).”
        
- On target swap:
    
    - “You turn your attention to Kelp Flea #2.”
        
- On disengage success:
    
    - “You slip free and create distance!”
        
- On flee:
    
    - “You sprint east, leaving the fight behind.”
        
- On pursuit:
    
    - “A Kelp Flea skitters after you!”