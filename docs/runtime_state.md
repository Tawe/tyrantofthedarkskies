# Runtime State Requirements

## Purpose

Define how the game stores and manages **runtime world state** (rooms, entities, loot, encounters, combat continuity) while keeping **content files immutable**.

This document focuses on:

- What must be persisted
    
- What may be ephemeral
    
- How state is created, updated, and cleaned up
    
- How state supports spawns, loot, pursuit, and multi-player interaction
    

---

## Definitions

- **Content Template**: Immutable definition (room JSON, creature templates, item templates, encounter/loot tables).
    
- **Runtime State**: Mutable state stored in the database representing “what exists right now.”
    
- **Entity Template**: The blueprint for a creature/NPC/item (stats, skills, modifiers, loot table refs).
    
- **Entity Instance**: A specific spawned entity currently in the world (unique ID, current HP, durability, statuses).
    
- **Room State**: A per-room runtime record used to track active entities, dropped items, timers, and seed.
    
- **Spawn Group**: A rule in a room template that can generate creature instances.
    
- **Loot Group**: A rule in a room template that can generate item instances.
    

---

## Non-Goals

- Full-world continuous simulation when no players are present
    
- Persisting every transient combat tick or message log
    
- Persisting every monster’s life across server restarts (except special cases)
    

---

## High-Level Requirements

### R1 — Content Immutability

Room JSON and entity templates must never be modified at runtime.

### R2 — Runtime Entity Instances

Creatures, NPCs, and dropped items that exist “in the world” must be represented as **entity instances**.

### R3 — Room-Scoped State

Rooms may have runtime state representing current inventory, active encounters, and spawn/loot timers.

### R4 — Lazy State Creation

Room state should be created **on demand** (e.g., on first player entry since reset or when an event requires it).

### R5 — Deterministic Spawn/Loot

Room state must support deterministic or repeatable spawn/loot behavior per reset window (via a room seed).

### R6 — Cleanup and Expiry

Runtime state must support cleanup rules to prevent unbounded database growth.

### R7 — Multi-Player Correctness

Two or more players entering/acting in the same room must see consistent state (same entities, same deaths, same loot).

### R8 — Pursuit and Movement

Runtime state must support entities changing rooms (pursuit, wandering, schedules) without editing room templates.

---

## Data Model Requirements

### 1) Room State

Each room may have a **room_state** record.

**Required fields:**

- `room_id` (string)
    
- `seed` (integer) — used for repeatable rolls per reset
    
- `created_at` (timestamp)
    
- `last_active_at` (timestamp) — updated when players interact in room
    
- `last_reset_at` (timestamp)
    
- `next_reset_at` (timestamp or nullable)
    

**Optional fields:**

- `room_flags_runtime` (json) — dynamic flags (e.g., locked, burning)
    
- `state_version` (int) — optimistic concurrency support
    

**Behavior:**

- Created when a player first enters a room after reset OR when an event requires persistence (combat started, loot dropped).
    
- Updated on significant actions (spawn, death, loot pickup, door state change).
    

---

### 2) Entity Instances

Every active creature/NPC/item that exists right now must be represented as an **entity_instance**.

**Required fields:**

- `instance_id` (uuid/string)
    
- `template_id` (string)
    
- `entity_type` (enum: `creature | npc | item`)
    
- `created_at` (timestamp)
    

**Creature/NPC required fields (if applicable):**

- `tier` (int or enum)
    
- `role` (enum: brute, minion, boss, artillery, healer, controller)
    
- `hp_current`, `hp_max`
    
- `attack_interval` or `speed_cost`
    
- `accuracy` (or primary combat skill)
    

**Item required fields (if applicable):**

- `quantity` (int)
    
- `durability_current` (nullable)
    
- `modifier_id` (nullable)
    

**Optional fields:**

- `status_effects` (json)
    
- `expires_at` (timestamp) — for dropped loot and ephemeral spawns
    
- `owner_player_id` (nullable) — for temporary ownership / loot protection
    
- `spawn_group_id` (nullable)
    
- `loot_group_id` (nullable)
    

---

### 3) Entity Position

Entity location is stored separately as **entity_position**.

**Required fields:**

- `instance_id`
    
- `room_id`
    
- `updated_at`
    

**Optional fields:**

- `range_band` (enum: engaged, near, far) — room-local combat positioning
    
- `engaged_target_id` (nullable)
    
- `leash_room_id` (nullable)
    

**Behavior:**

- Updated whenever the entity moves rooms or changes range band.
    

---

### 4) Spawn and Loot Timers

Room state must track whether spawns/loot are eligible.

**Required capabilities:**

- Track per `spawn_id`:
    
    - `last_spawn_at`
        
    - `next_spawn_at`
        
    - `alive_count`
        
- Track per `loot_id`:
    
    - `last_loot_roll_at`
        
    - `next_loot_roll_at`
        

This can be represented as:

- a `room_spawn_state` table, or
    
- a JSON field in `room_state` (less queryable but simpler).
    

---

## Runtime Behavior Requirements

### B1 — Room Entry Resolution

On player entering a room:

1. Load room template
    
2. Load (or create) `room_state`
    
3. Resolve scheduled NPC presence (if schedule-based)
    
4. Check spawn/loot timers and generate instances if eligible
    
5. Return final room view (entities + items)
    

### B2 — Entity Death

When a creature/NPC dies:

- Remove it from the active world by deleting its `entity_position` (and optionally its instance)
    
- Generate loot drops as item instances with positions in the room
    
- Update spawn group counters/timers
    

### B3 — Loot Pickup

When a player picks up loot:

- Validate the item instance exists in room
    
- Transfer ownership to player inventory
    
- Remove or update the item instance in room state
    

### B4 — Expiration / Cleanup

The system must expire:

- Dropped items after a configured duration (e.g., 30–120 minutes)
    
- Random encounter creatures after a configured duration if not engaged
    

Rooms with no players for a configured duration should be eligible for cleanup:

- Delete `room_state` if it contains no non-expired entities
    
- Or keep minimal timer-only state if needed
    

### B5 — Reset Rules

Rooms should support reset windows:

- A reset defines when ambient loot and baseline spawns become eligible again
    
- Reset should refresh room seed
    
- Reset should not duplicate entities already alive
    

---

## Random Encounters Requirements

### E1 — Encounter Triggers

Random encounters must be triggered by:

- room entry, movement, time spent, or noisy actions
    

### E2 — Encounter Instance Tracking

Random encounters must create entity instances tagged with an `encounter_id`.

### E3 — Anti-Farm Protections

Encounters must support:

- player cooldowns
    
- zone threat meters
    
- encounter caps per time window
    

---

## Pursuit Requirements

### P1 — Disengage Gate (Recommended)

If a player is engaged and attempts to move rooms:

- require a **Disengage** action or maneuver
    

### P2 — Pursuit Modes

Creatures must support pursuit tags:

- `none`, `short` (1 room), `long` (multi-room for X time)
    

### P3 — Leash Rules

Creatures must not pursue indefinitely:

- `leash_room_id` and `leash_radius` OR
    
- `leash_time`
    

### P4 — Safe Room Rules

Room flags must be able to block pursuit:

- `safe`
    
- `no_pursuit`
    

---

## Concurrency & Consistency Requirements

### C1 — Atomic Updates

Actions that affect shared state (death, loot pickup) must be atomic.

### C2 — Multi-Player Visibility

All players in a room must see consistent state changes within one tick.

### C3 — Duplicate Spawn Prevention

Spawn logic must prevent double-spawning when two players enter simultaneously.

---

## Observability Requirements

### O1 — Debugging Support

Store:

- room seed
    
- spawn group timers
    
- encounter IDs
    

Provide admin/debug commands:

- `state room <room_id>`
    
- `state entity <instance_id>`
    
- `spawn now <spawn_id>`
    

---

## Open Decisions

- Database choice and indexing strategy (Postgres vs SQLite)
    
- How “always-on” rooms behave when no players are online
    
- Whether to store spawn state as normalized tables or JSON blobs
    
- Combat state persistence rules during disconnects