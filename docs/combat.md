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