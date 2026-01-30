# Random Encounter Tables – Unflooded Sea Region

This document defines **random encounter tables** for the early-game wilderness areas around New Cove:

* **Unflooded Sea**
* **Kelp Plains**
* **Rift Forest**

These tables are designed for **Low Tier (1–5)** play and support your encounter-group, role-based combat system.

---

## General Encounter Rules

* Encounters are rolled using a **zone-specific table**.
* Each encounter creates an **encounter group** sharing one `encounter_id`.
* Encounters may be:

  * Combat
  * Social
  * Environmental / exploration
* Weights assume a d100 roll (adjustable).
* Some encounters scale slightly based on party size.

---

## Unflooded Sea – Encounter Table

*A vast, raised ocean floor with coral stone, exposed ruins, and strange tides.*

|   Roll | Encounter                 | Composition         | Notes                           |
| -----: | ------------------------- | ------------------- | ------------------------------- |
|  01–20 | Kelp Fleas                | 3–5 Minions         | Fast pests, swarming behavior   |
|  21–35 | Reef Crabs                | 2 Minions + 1 Brute | Crushing damage, high DR        |
|  36–45 | Rift Wisps                | 1–2 Artillery       | Psychic/Force damage            |
|  46–55 | Unflooded Stalker         | 1 Brute             | Ambush predator                 |
|  56–65 | Crabfolk Scouts           | 2–3 Minions         | May turn social if not attacked |
|  66–75 | Lost Explorer             | 1 NPC               | Injured, quest hook             |
|  76–85 | Shifting Tides            | Environmental       | Forced movement, hazard checks  |
|  86–93 | Buried Relic Site         | Exploration         | Loot roll, no combat            |
| 94–100 | Ancient Sentinel Fragment | 1 Boss (Rare)       | Very dangerous, avoidable      |

---

## Kelp Plains – Encounter Table

*Endless hardened kelp fields that obscure vision and movement.*

|   Roll | Encounter            | Composition              | Notes                     |
| -----: | -------------------- | ------------------------ | ------------------------- |
|  01–15 | Kelp Fleas           | 4–6 Minions              | Appear suddenly from kelp |
|  16–30 | Kelp Crawlers        | 2 Minions + 1 Controller | Entangling maneuvers      |
|  31–45 | Reef Crabs           | 1 Brute + 1–2 Minions    | Territorial               |
|  46–55 | Kelp Shade           | 1 Controller             | Fear and disorientation   |
|  56–65 | Crabfolk Foragers    | 2 NPCs                   | Neutral, trade possible   |
|  66–75 | Kelp Collapse        | Environmental            | Damage + restrained       |
|  76–85 | Forgotten Cache      | Exploration              | Tools, low-tier gear      |
|  86–93 | Kelp Plains Alpha    | 1 Brute                  | Strong variant            |
| 94–100 | Kelp Leviathan Spawn | 1 Boss (Rare)            | Retreat encouraged        |

---

## Rift Forest – Encounter Table

*Jagged coral spires and stone growths create natural choke points and ambush zones.*

|   Roll | Encounter                  | Composition        | Notes                    |
| -----: | -------------------------- | ------------------ | ------------------------ |
|  01–15 | Rift Skitterlings          | 3–5 Minions        | Climbing, flanking       |
|  16–30 | Coral Stalkers             | 2 Artillery        | Bleeding attacks         |
|  31–45 | Rift Wardens               | 1 Brute + 1 Healer | Defensive patrol         |
|  46–55 | Living Coral Growth        | Environmental      | Area denial hazard       |
|  56–65 | Crabfolk Settlement Patrol | 2–4 NPCs           | Social encounter         |
|  66–75 | Echoing Spire              | Exploration        | Lore + skill checks      |
|  76–85 | Rift Forest Hunter         | 1 Controller       | Battlefield manipulation |
|  86–93 | Corrupted Guardian         | 1 Brute            | Necrotic influence       |
| 94–100 | Rift Heart Sentinel        | 1 Boss (Rare)      | Anchors the forest       |

---

## Time-Based Modifiers (Optional)

* **Night:** +10% chance of predators (Brutes, Controllers)
* **Storm Winds:** +10% environmental encounters
* **High Threat Meter:** Reroll benign results once

---

## Design Notes

* Minions dominate early results to keep fights fast
* Rare boss encounters are intentionally avoidable
* Social encounters prevent the wilderness from feeling purely hostile
* Environmental encounters reinforce the strangeness of the Unflooded Sea

---

## Future Expansion Hooks

* Add faction control modifiers
* Add seasonal variations
* Tie specific encounters to quests or world state flags
* Introduce roaming multi-room encounters

---

## Implementation

* Rooms may set a **zone** (e.g. `unflooded_sea`, `kelp_plains`, `rift_forest`) in room JSON. On entry, the server may roll on that zone’s table (with cooldown) and spawn combat encounters as runtime creature instances with a shared `encounter_id`.
* Social, environmental, and exploration entries can be implemented as messages, hazards, or loot hooks; combat compositions are defined in code/data and use creature templates from `contributions/creatures/`.
