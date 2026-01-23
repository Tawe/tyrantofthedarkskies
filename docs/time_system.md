# World Time System

This document defines the **global in-game clock**, how it maps to real time, and how it drives **shop hours**, **NPC schedules**, and world simulation.

---

## Time Ratio

**Goal:** 1 real day = 3 in-game days

That means:

- **1 real hour = 3 in-game hours**
    
- **1 real minute = 3 in-game minutes**
    
- **1 real second = 3 in-game seconds**
    

Equivalently:

- **1 in-game day = 8 real hours**
    

---

## Canonical Time Unit

The world clock is stored as a single integer:

- `world_seconds` = total in-game seconds since epoch (server start or a fixed lore epoch)
    

All other calendar values are derived from this.

Derived values:

- `day_number`
    
- `hour` (0–23)
    
- `minute` (0–59)
    
- `second` (0–59)
    

---

## Calendar & Day Parts

A day is divided into readable parts for player messaging:

- **Dawn** (05:00–07:59)
    
- **Morning** (08:00–11:59)
    
- **Afternoon** (12:00–16:59)
    
- **Dusk** (17:00–19:59)
    
- **Night** (20:00–04:59)
    

These labels are used by NPC dialogue and signage.

---

## Player Commands

### `time`

Shows an in-world friendly time readout:

- “It is **Morning**, 2 bells past sunrise.”
    
- “It is **Night**, the docks are lit by lanterns.”
    

(Optional) display exact clock:

- “(08:23)” for players who prefer precision.
    

---

## Store Hours

Stores do not simulate activity while closed; they **gate interactions**.

A store defines:

- `open_time` (HH:MM)
    
- `close_time` (HH:MM)
    
- optional: `closed_days` / `festival_days`
    
- optional: exceptions (quest/event overrides)
    

When closed:

- the shopkeeper may be absent OR present but refuses service
    
- buy/sell/repair commands are unavailable
    

**Recommended town default:**

- Shops open: **08:00**
    
- Shops close: **18:00**
    

---

## NPC Scheduling Model (Lazy Presence)

NPCs can appear in rooms based on schedules without expensive global simulation.

### Key idea

- **NPC schedules are the source of truth**
    
- Rooms **resolve presence on demand** (on enter / look)
    

This is called **lazy scheduling**.

### NPC schedule structure

Each NPC defines a list of time blocks mapping to rooms:

- 06:00–08:00 → home
    
- 08:00–18:00 → workplace
    
- 18:00–22:00 → tavern
    
- 22:00–06:00 → home
    

When a player enters a room, the game checks which NPCs are scheduled there at the current time and shows them.

---

## Rooms & Time Checks

Rooms do not “own” NPCs; they **display NPCs whose schedules place them there**.

Implementation concept:

- `present_npcs(room_id, world_time)` returns a list of NPC IDs
    

To keep this efficient:

- Maintain an index of **candidate NPCs per room** (NPCs that could ever be present there)
    

---

## Live Rooms (Optional Tick Updates)

Rooms with players inside can receive periodic updates:

- NPC enters/leaves due to schedule boundary
    
- shop opens/closes
    
- ambient changes (lanterns lit, tide-wind shifts)
    

Suggested update cadence:

- Every **30–60 real seconds** (90–180 in-game seconds)
    

---

## Schedule Safety Rules

NPC schedule changes should be deferred if the NPC is:

- in combat
    
- mid-transaction
    
- mid-dialogue
    

When deferred:

- set `schedule_deferred_until_free = true`
    
- apply the next schedule change when safe
    

---

## Messaging Patterns (Immersion)

When visible schedule changes occur in an occupied room:

- “Jalia pulls down the shutters and begins counting coins.”
    
- “A guard patrol enters from the west, boots thudding on the planks.”
    
- “The lanterns along the dock flare brighter as night settles in.”
    

---

## Performance Guidelines

- Do not simulate all NPC movement every tick
    
- Resolve schedules **only** when:
    
    - a player enters / looks
        
    - a room is occupied (live room updates)
        
    - a globally important NPC requires it
        

---

## Future Extensions

- Seasons and weather
    
- Moon phases (ties to your star signs)
    
- Holy days (affects temples, factions, market prices)
    
- Time-based regional events and spawns