# Test Adventure: The Sunken King’s Cave

*A small, self-contained test adventure for **Tyrant of the Dark Skies**, designed to exercise NPC scheduling, travel, combat, puzzles, skill checks, secret paths, loot, and return flow.*

---

## Adventure Hook – Old Lorek (Docks)

**Availability:**

* Appears on **The Docks** between **06:00–11:00 (in-game time)**

**NPC:** Old Lorek

* Elderly fisherman / salvager
* Nervous, superstitious, well-liked

### Initial Description (Seen on Enter)

> An old fisherman with a salt-crusted beard sits near the edge of the docks, staring out toward the open sea. His boat rocks gently beside him.

### Conversation Hooks

* **[cave]** – Mentions finding an old cave along the coast
* **[spirits]** – Says he heard whispers and refuses to go inside
* **[boat]** – Offers to take the players there

### Quest Trigger

If prompted correctly, Old Lorek says:

> “I’ll take you there, if you’ve the nerve. But I won’t step foot inside. When you’re done… talk to me again, and I’ll bring you back.”

**Result:**

* Party is transported by boat to **Outside the Cave**

---

## Travel & Return

* Old Lorek **waits outside the cave**
* Players can speak to him at any time to return to the docks
* If players die inside, they awaken back in New Cove with a reputation penalty

---

## Lore Constraints

* The term **“Tidewater Goblin” must never be spoken** in dialogue or descriptions
* The creatures are only referred to as:

  * *the old coastal folk*
  * *the drowned king*
  * *those who once lived where the sea now sleeps*

---

## Cave Layout Overview

1. Outside the Cave
2. Watery Cave (Reef Crabs)
3. Small Alcove (Dead End)
4. The Nest
5. Cave Drawings
6. Tomb Opening (Puzzle Room)
7. King’s Tomb (Boss)
8. Pit Room
9. Coral Idol Chamber

(Secret connections allow alternate routes)

---

## Room Details

### Room 1 – Outside the Cave

**Description:**
A low cave mouth opens along the rocky coast. Shallow pools of salt water collect just inside, and the air smells of rot and old stone.

**NPC:** Old Lorek (waiting)

**Exits:**

* East → Watery Cave

---

### Room 2 – Watery Cave (Reef Crabs)

**Description:**
Shallow pools of salt water dot the cave floor. Something skitters beneath the surface.

**Creatures:**

* 2–3 Reef Crabs (Minions)

**Exits:**

* East → Small Alcove
* North → Cave Drawings
* West → The Nest

---

### Room 3 – Small Alcove (Dead End)

**Description:**
A cramped alcove with a partially collapsed ceiling. Old bones lie scattered among the rocks.

**Interaction:**

* **Search / Awareness check**

**Reward:**

* **Bone Hunting Knife** (low-tier weapon)

**Exits:**

* West → Watery Cave

---

### Room 4 – The Nest

**Description:**
Broken shells and cracked stone form a crude nest. The air vibrates with angry clicks.

**Creatures:**

* 2 Reef Crabs (Minions)
* 1 Mother Crab (Brute)

**After Combat:**

* **Search check** reveals:

  * Seashell Necklace (trade good)

**Exits:**

* North → Pit Room
* East → Watery Cave

---

### Room 5 – Cave Drawings

**Description:**
The cave walls here are etched with crude drawings. Small figures kneel before a larger shape, offering an idol carved from coral.

**Lore:**

* Depicts a king
* Depicts an offering

**Exits:**

* East → Tomb Opening
* South → Watery Cave

---

### Room 6 – Tomb Opening (Puzzle Room)

**Description:**
The rough cave gives way to worked stone. A smooth wall blocks the passage, a circular hollow set at its center.

**Puzzle:**

* Placing the **Coral Idol** opens the wall

**Secret:**

* **Search check** can reveal a hidden door (leads to Coral Idol Chamber)

**Exits:**

* West → Cave Drawings
* North (locked) → King’s Tomb
* Secret East → Coral Idol Chamber

---

### Room 7 – King’s Tomb (Boss)

**Description:**
Stone steps descend into a burial chamber. At its center sits a broken throne. Bones stir.

**Boss:**

* Skeleton King of the Drowned Folk (Boss)

**Rewards:**

* Gems
* Skinshaw Artwork (valuable trade goods)
* **Coral Trident** (first magical weapon)

**Exits:**

* South → Tomb Opening

---

### Room 8 – Pit Room

**Description:**
A wide pit splits the chamber floor. The bottom is lost in shadow.

**Interaction:**

* **Athletics / Agility check** to cross

**Failure:**

* Fall into pit
* Take damage

**At Bottom:**

* Rare Sea Snail (can be caught and sold)

**Escape:**

* **Climbing check** to climb out

**Exits:**

* South → The Nest
* North → Coral Idol Chamber

---

### Room 9 – Coral Idol Chamber

**Description:**
A natural chamber lit by reflected light. A coral idol lies abandoned at the center.

**Item:**

* Coral Idol (quest item)

**Secret:**

* Hidden door back to Tomb Opening

**Exits:**

* South → Pit Room
* Secret West → Tomb Opening

---

## Design Goals Tested

* Time-based NPC availability
* NPC transport
* Multi-path dungeon navigation
* Skill checks (search, climb, cross, awareness)
* Environmental risk
* Secret doors
* Puzzle gating
* Boss encounter
* Meaningful loot
* Return path clarity

---

## Notes for Implementation

* Boss and Mother Crab should use **pursue = none**
* Dungeon resets only after a cooldown
* Coral Idol is non-consumable and persists until used

---

## Summary

This adventure introduces players to:

* Exploration
* Combat
* Problem solving
* Reward-driven risk

All within a compact, replayable structure suitable for early testing.


## Rooms 
[
  {
    "room_id": "cave_outside",
    "name": "Outside the Cave",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "coastal",
    "description": "A low cave mouth opens along the rocky coast. Dark water pools in the stone, and the air smells of salt and old rot. An old skiff bobs nearby, its rope tied to a jagged post.",
    "exits": {
      "east": "cave_watery_entry"
    },
    "items": [],
    "npcs": ["old_lorek_outside"],
    "flags": ["public"],
    "combat_tags": [],
    "interactables": [
      {
        "object_id": "lorek_return",
        "name": "Old Lorek's skiff",
        "keywords": ["lorek", "skiff", "boat", "return"],
        "examine_text": "Old Lorek waits by the skiff, refusing to look into the cave for long.",
        "actions": {
          "talk": {
            "keywords": ["back", "return", "docks", "new cove"],
            "result": { "travel_to_room_id": "docks" }
          }
        }
      }
    ]
  },

  {
    "room_id": "cave_watery_entry",
    "name": "Watery Cave",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "sheltered",
    "description": "Shallow pools of salt water dot the cave floor. The stone is slick, and faint skittering echoes from the dark. Broken shell fragments crunch underfoot.",
    "exits": {
      "west": "cave_nest",
      "north": "cave_drawings",
      "east": "cave_small_alcove",
      "west_return": "cave_nest"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous"],
    "combat_tags": ["wilderness"],
    "static_encounter": {
      "encounter_id": "enc_watery_reef_crabs",
      "respawn_seconds": 900,
      "composition": [
        { "template_id": "reef_crab", "count": 2, "role": "minion" },
        { "template_id": "reef_crab", "count": 1, "role": "minion", "variant": "skittery" }
      ]
    }
  },

  {
    "room_id": "cave_small_alcove",
    "name": "Small Alcove",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "A cramped alcove with a partially collapsed ceiling. Old bones lie scattered among stones worn smooth by long-vanished water.",
    "exits": {
      "west": "cave_watery_entry"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "interactables": [
      {
        "object_id": "bone_pile",
        "name": "bone pile",
        "keywords": ["bones", "bone", "pile", "remains"],
        "examine_text": "Cracked ribs and small skull fragments. Something sharper is buried beneath.",
        "actions": {
          "search": {
            "check": { "skill": "Searching", "difficulty": 10 },
            "on_success": {
              "text": "You sift the bones and uncover a crude hunting knife, its handle wrapped in dried cord.",
              "gives_item": "weapon_bone_hunting_knife"
            },
            "on_fail": {
              "text": "You dig through the bones but find only splinters and dust."
            },
            "once_per_player": true
          }
        }
      }
    ]
  },

  {
    "room_id": "cave_drawings",
    "name": "Cave Drawings",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "The cave walls here are etched with crude drawings. Small figures kneel before a larger shape seated on a broken throne, offering an idol carved from coral.",
    "exits": {
      "south": "cave_watery_entry",
      "east": "cave_tomb_opening"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "interactables": [
      {
        "object_id": "drawings",
        "name": "cave drawings",
        "keywords": ["drawings", "etchings", "wall", "art"],
        "examine_text": "The figures are thin and angular. The idol is drawn again and again. The seated shape is crowned, its mouth open as if in a silent command.",
        "actions": {
          "examine": true
        }
      }
    ]
  },

  {
    "room_id": "cave_tomb_opening",
    "name": "Tomb Opening",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "The rough cave walls smooth into worked stone. A fitted stone wall blocks the way, a circular hollow set at its center like a missing keystone.",
    "exits": {
      "west": "cave_drawings",
      "north": "cave_kings_tomb_locked"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "puzzle": {
      "puzzle_id": "pzl_coral_idol_door",
      "locked_exit": "north",
      "requires_item": "quest_coral_idol",
      "on_solve": {
        "text": "The coral idol clicks into place. Stone grinds and the wall slides open, revealing stairs descending into darkness.",
        "unlocks_exit_to": { "north": "cave_kings_tomb" }
      }
    },
    "interactables": [
      {
        "object_id": "stone_hollow",
        "name": "circular hollow",
        "keywords": ["hollow", "circle", "socket", "hole", "wall"],
        "examine_text": "A perfectly carved recess. Something round and coral-shaped would fit snugly.",
        "actions": {
          "place": {
            "accepts_item": "quest_coral_idol",
            "triggers_puzzle_id": "pzl_coral_idol_door"
          }
        }
      },
      {
        "object_id": "hidden_seam_to_idol",
        "name": "worked stone seam",
        "keywords": ["seam", "stone", "wall", "draft"],
        "examine_text": "A faint seam runs along the wall. The air is cooler here, like it slips through from somewhere else.",
        "actions": {
          "search": {
            "check": { "skill": "Searching", "difficulty": 13 },
            "on_success": {
              "text": "You find a concealed door in the worked stone.",
              "reveals_exit": { "east": "cave_coral_idol_chamber" }
            },
            "on_fail": { "text": "You find nothing but cold stone." }
          }
        }
      }
    ]
  },

  {
    "room_id": "cave_kings_tomb",
    "name": "King's Tomb",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "Stone steps descend into a burial chamber. A broken throne sits against the far wall. The air is stale—until bone begins to scrape against stone.",
    "exits": {
      "south": "cave_tomb_opening"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": ["boss_room"],
    "static_encounter": {
      "encounter_id": "enc_boss_drowned_king",
      "respawn_seconds": 1800,
      "composition": [
        { "template_id": "drowned_king_skeleton", "count": 1, "role": "boss" }
      ],
      "on_defeat": {
        "drops": [
          { "loot_table_id": "loot_kings_tomb_gems", "rolls": 1 },
          { "loot_table_id": "loot_kings_tomb_tradegoods", "rolls": 1 },
          { "item_id": "weapon_coral_trident", "chance": 0.35 }
        ],
        "text": "The skeleton collapses into stillness. The chamber feels lighter—as if something finally stopped listening."
      }
    }
  },

  {
    "room_id": "cave_nest",
    "name": "The Nest",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "Broken shells and cracked stone form a crude nest. The air vibrates with angry clicks, and something larger shifts in the dark.",
    "exits": {
      "east": "cave_watery_entry",
      "north": "cave_pit_room"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "static_encounter": {
      "encounter_id": "enc_nest_crabs",
      "respawn_seconds": 1200,
      "composition": [
        { "template_id": "reef_crab", "count": 2, "role": "minion" },
        { "template_id": "reef_crab_brute", "count": 1, "role": "brute", "variant": "mother" }
      ]
    },
    "interactables": [
      {
        "object_id": "nest_debris",
        "name": "nest debris",
        "keywords": ["nest", "debris", "shells", "bones"],
        "examine_text": "Shell fragments, kelp strands, and bits of drift. Something glints within.",
        "actions": {
          "search": {
            "requires_encounter_defeated": "enc_nest_crabs",
            "check": { "skill": "Searching", "difficulty": 11 },
            "on_success": {
              "text": "You find a seashell necklace tangled in kelp strands.",
              "gives_item": "trinket_seashell_necklace"
            },
            "on_fail": { "text": "You find nothing but cracked shell and grit." },
            "once_per_player": true
          }
        }
      }
    ]
  },

  {
    "room_id": "cave_pit_room",
    "name": "Pit Room",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "A wide pit splits the chamber floor. The far side is reachable—but the stone looks slick, and the drop disappears into shadow.",
    "exits": {
      "south": "cave_nest",
      "north": "cave_coral_idol_chamber"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "hazard": {
      "hazard_id": "hz_cross_pit",
      "check": { "skill": "Dodging", "difficulty": 12 },
      "on_fail": {
        "text": "Your footing slips. You tumble into the pit.",
        "damage": { "type": "falling", "min": 4, "max": 8 },
        "move_to_room_id": "cave_pit_bottom"
      }
    },
    "interactables": [
      {
        "object_id": "pit_edge",
        "name": "pit edge",
        "keywords": ["pit", "edge", "gap"],
        "examine_text": "A slick, treacherous jump. You could try to cross it—or you could fall.",
        "actions": {
          "cross": { "triggers_hazard_id": "hz_cross_pit" }
        }
      }
    ]
  },

  {
    "room_id": "cave_pit_bottom",
    "name": "Pit Bottom",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "The pit floor is damp and cold. Old shells and silt gather here. Something slow and glossy clings to the stone.",
    "exits": {},
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "interactables": [
      {
        "object_id": "rare_snail",
        "name": "rare sea snail",
        "keywords": ["snail", "sea snail", "rare snail"],
        "examine_text": "A rare sea snail, its shell patterned like ink in water.",
        "actions": {
          "take": {
            "gives_item": "trade_rare_sea_snail",
            "once_per_player": true
          }
        }
      },
      {
        "object_id": "pit_wall",
        "name": "pit wall",
        "keywords": ["wall", "climb", "stone"],
        "examine_text": "The wall is slick but climbable with effort.",
        "actions": {
          "climb": {
            "check": { "skill": "Climbing", "difficulty": 12 },
            "on_success": { "text": "You haul yourself back up to the edge of the pit.", "move_to_room_id": "cave_pit_room" },
            "on_fail": { "text": "You slip and fail to gain purchase." }
          }
        }
      }
    ]
  },

  {
    "room_id": "cave_coral_idol_chamber",
    "name": "Coral Idol Chamber",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "A natural chamber lit by reflected light. In the center lies a coral idol, abandoned as if dropped in haste long ago.",
    "exits": {
      "south": "cave_pit_room"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "interactables": [
      {
        "object_id": "coral_idol",
        "name": "coral idol",
        "keywords": ["idol", "coral", "offering"],
        "examine_text": "A coral carving worn smooth by time. It feels oddly warm when you touch it.",
        "actions": {
          "take": {
            "gives_item": "quest_coral_idol",
            "once_per_player": true
          }
        }
      },
      {
        "object_id": "secret_door_to_opening",
        "name": "stone panel",
        "keywords": ["panel", "stone", "secret", "door"],
        "examine_text": "One panel looks slightly misaligned. There’s a gap thin as a fingernail.",
        "actions": {
          "search": {
            "check": { "skill": "Searching", "difficulty": 13 },
            "on_success": {
              "text": "You find a hidden passage and slip through.",
              "move_to_room_id": "cave_tomb_opening"
            },
            "on_fail": { "text": "You find nothing but smooth stone." }
          }
        }
      }
    ]
  }
]


##rooms 
[
  {
    "room_id": "cave_outside",
    "name": "Outside the Cave",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "coastal",
    "description": "A low cave mouth opens along the rocky coast. Dark water pools in the stone, and the air smells of salt and old rot. An old skiff bobs nearby, its rope tied to a jagged post.",
    "exits": {
      "east": "cave_watery_entry"
    },
    "items": [],
    "npcs": ["old_lorek_outside"],
    "flags": ["public"],
    "combat_tags": [],
    "interactables": [
      {
        "object_id": "lorek_return",
        "name": "Old Lorek's skiff",
        "keywords": ["lorek", "skiff", "boat", "return"],
        "examine_text": "Old Lorek waits by the skiff, refusing to look into the cave for long.",
        "actions": {
          "talk": {
            "keywords": ["back", "return", "docks", "new cove"],
            "result": { "travel_to_room_id": "docks" }
          }
        }
      }
    ]
  },

  {
    "room_id": "cave_watery_entry",
    "name": "Watery Cave",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "sheltered",
    "description": "Shallow pools of salt water dot the cave floor. The stone is slick, and faint skittering echoes from the dark. Broken shell fragments crunch underfoot.",
    "exits": {
      "west": "cave_nest",
      "north": "cave_drawings",
      "east": "cave_small_alcove"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous"],
    "combat_tags": ["wilderness"],
    "static_encounter": {
      "encounter_id": "enc_watery_reef_crabs",
      "respawn_seconds": 900,
      "composition": [
        { "template_id": "reef_crab", "count": 2, "role": "minion" },
        { "template_id": "reef_crab", "count": 1, "role": "minion", "variant": "skittery" }
      ]
    }
  },

  {
    "room_id": "cave_small_alcove",
    "name": "Small Alcove",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "A cramped alcove with a partially collapsed ceiling. Old bones lie scattered among stones worn smooth by long-vanished water.",
    "exits": {
      "west": "cave_watery_entry"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "interactables": [
      {
        "object_id": "bone_pile",
        "name": "bone pile",
        "keywords": ["bones", "bone", "pile", "remains"],
        "examine_text": "Cracked ribs and small skull fragments. Something sharper is buried beneath.",
        "actions": {
          "search": {
            "check": { "skill": "Investigating", "difficulty": 10 },
            "on_success": {
              "text": "You sift the bones and uncover a crude hunting knife, its handle wrapped in dried cord.",
              "gives_item": "weapon_bone_hunting_knife"
            },
            "on_fail": {
              "text": "You dig through the bones but find only splinters and dust."
            },
            "once_per_player": true
          }
        }
      }
    ]
  },

  {
    "room_id": "cave_drawings",
    "name": "Cave Drawings",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "The cave walls here are etched with crude drawings. Small figures kneel before a larger shape seated on a broken throne, offering an idol carved from coral.",
    "exits": {
      "south": "cave_watery_entry",
      "east": "cave_tomb_opening"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "interactables": [
      {
        "object_id": "drawings",
        "name": "cave drawings",
        "keywords": ["drawings", "etchings", "wall", "art"],
        "examine_text": "The figures are thin and angular. The idol is drawn again and again. The seated shape is crowned, its mouth open as if in a silent command.",
        "actions": {
          "examine": true
        }
      }
    ]
  },

  {
    "room_id": "cave_tomb_opening",
    "name": "Tomb Opening",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "The rough cave walls smooth into worked stone. A fitted stone wall blocks the way, a circular hollow set at its center like a missing keystone.",
    "exits": {
      "west": "cave_drawings",
      "north": "cave_kings_tomb_locked"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "puzzle": {
      "puzzle_id": "pzl_coral_idol_door",
      "locked_exit": "north",
      "requires_item": "quest_coral_idol",
      "on_solve": {
        "text": "The coral idol clicks into place. Stone grinds and the wall slides open, revealing stairs descending into darkness.",
        "unlocks_exit_to": { "north": "cave_kings_tomb" }
      }
    },
    "interactables": [
      {
        "object_id": "stone_hollow",
        "name": "circular hollow",
        "keywords": ["hollow", "circle", "socket", "hole", "wall"],
        "examine_text": "A perfectly carved recess. Something round and coral-shaped would fit snugly.",
        "actions": {
          "place": {
            "accepts_item": "quest_coral_idol",
            "triggers_puzzle_id": "pzl_coral_idol_door"
          }
        }
      },
      {
        "object_id": "hidden_seam_to_idol",
        "name": "worked stone seam",
        "keywords": ["seam", "stone", "wall", "draft"],
        "examine_text": "A faint seam runs along the wall. The air is cooler here, like it slips through from somewhere else.",
        "actions": {
          "search": {
            "check": { "skill": "Investigating", "difficulty": 13 },
            "on_success": {
              "text": "You find a concealed door in the worked stone.",
              "reveals_exit": { "east": "cave_coral_idol_chamber" }
            },
            "on_fail": { "text": "You find nothing but cold stone." }
          }
        }
      }
    ]
  },

  {
    "room_id": "cave_kings_tomb",
    "name": "King's Tomb",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "Stone steps descend into a burial chamber. A broken throne sits against the far wall. The air is stale—until bone begins to scrape against stone.",
    "exits": {
      "south": "cave_tomb_opening"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": ["boss_room"],
    "static_encounter": {
      "encounter_id": "enc_boss_drowned_king",
      "respawn_seconds": 1800,
      "composition": [
        { "template_id": "drowned_king_skeleton", "count": 1, "role": "boss" }
      ],
      "on_defeat": {
        "drops": [
          { "loot_table_id": "loot_kings_tomb_gems", "rolls": 1 },
          { "loot_table_id": "loot_kings_tomb_tradegoods", "rolls": 1 },
          { "item_id": "weapon_coral_trident", "chance": 0.35 }
        ],
        "text": "The skeleton collapses into stillness. The chamber feels lighter—as if something finally stopped listening."
      }
    }
  },

  {
    "room_id": "cave_nest",
    "name": "The Nest",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "Broken shells and cracked stone form a crude nest. The air vibrates with angry clicks, and something larger shifts in the dark.",
    "exits": {
      "east": "cave_watery_entry",
      "north": "cave_pit_room"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "static_encounter": {
      "encounter_id": "enc_nest_crabs",
      "respawn_seconds": 1200,
      "composition": [
        { "template_id": "reef_crab", "count": 2, "role": "minion" },
        { "template_id": "reef_crab_brute", "count": 1, "role": "brute", "variant": "mother" }
      ]
    },
    "interactables": [
      {
        "object_id": "nest_debris",
        "name": "nest debris",
        "keywords": ["nest", "debris", "shells", "bones"],
        "examine_text": "Shell fragments, kelp strands, and bits of drift. Something glints within.",
        "actions": {
          "search": {
            "requires_encounter_defeated": "enc_nest_crabs",
            "check": { "skill": "Investigating", "difficulty": 11 },
            "on_success": {
              "text": "You find a seashell necklace tangled in kelp strands.",
              "gives_item": "trinket_seashell_necklace"
            },
            "on_fail": { "text": "You find nothing but cracked shell and grit." },
            "once_per_player": true
          }
        }
      }
    ]
  },

  {
    "room_id": "cave_pit_room",
    "name": "Pit Room",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "A wide pit splits the chamber floor. The far side is reachable—but the stone looks slick, and the drop disappears into shadow.",
    "exits": {
      "south": "cave_nest",
      "north": "cave_coral_idol_chamber"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "hazard": {
      "hazard_id": "hz_cross_pit",
      "check": { "skill": "Dodging", "difficulty": 12 },
      "on_fail": {
        "text": "Your footing slips. You tumble into the pit.",
        "damage": { "type": "falling", "min": 4, "max": 8 },
        "move_to_room_id": "cave_pit_bottom"
      }
    },
    "interactables": [
      {
        "object_id": "pit_edge",
        "name": "pit edge",
        "keywords": ["pit", "edge", "gap"],
        "examine_text": "A slick, treacherous jump. You could try to cross it—or you could fall.",
        "actions": {
          "cross": { "triggers_hazard_id": "hz_cross_pit" }
        }
      }
    ]
  },

  {
    "room_id": "cave_pit_bottom",
    "name": "Pit Bottom",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "The pit floor is damp and cold. Old shells and silt gather here. Something slow and glossy clings to the stone.",
    "exits": {},
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "interactables": [
      {
        "object_id": "rare_snail",
        "name": "rare sea snail",
        "keywords": ["snail", "sea snail", "rare snail"],
        "examine_text": "A rare sea snail, its shell patterned like ink in water.",
        "actions": {
          "take": {
            "gives_item": "trade_rare_sea_snail",
            "once_per_player": true
          }
        }
      },
      {
        "object_id": "pit_wall",
        "name": "pit wall",
        "keywords": ["wall", "climb", "stone"],
        "examine_text": "The wall is slick but climbable with effort.",
        "actions": {
          "climb": {
            "check": { "skill": "Climbing", "difficulty": 12 },
            "on_success": {
              "text": "You haul yourself back up to the edge of the pit.",
              "move_to_room_id": "cave_pit_room"
            },
            "on_fail": { "text": "You slip and fail to gain purchase." }
          }
        }
      }
    ]
  },

  {
    "room_id": "cave_coral_idol_chamber",
    "name": "Coral Idol Chamber",
    "region_id": "sunken_kings_cave",
    "weather_exposure": "indoor",
    "description": "A natural chamber lit by reflected light. In the center lies a coral idol, abandoned as if dropped in haste long ago.",
    "exits": {
      "south": "cave_pit_room"
    },
    "items": [],
    "npcs": [],
    "flags": ["dangerous", "dark"],
    "combat_tags": [],
    "interactables": [
      {
        "object_id": "coral_idol",
        "name": "coral idol",
        "keywords": ["idol", "coral", "offering"],
        "examine_text": "A coral carving worn smooth by time. It feels oddly warm when you touch it.",
        "actions": {
          "take": {
            "gives_item": "quest_coral_idol",
            "once_per_player": true
          }
        }
      },
      {
        "object_id": "secret_door_to_opening",
        "name": "stone panel",
        "keywords": ["panel", "stone", "secret", "door"],
        "examine_text": "One panel looks slightly misaligned. There’s a gap thin as a fingernail.",
        "actions": {
          "search": {
            "check": { "skill": "Investigating", "difficulty": 13 },
            "on_success": {
              "text": "You find a hidden passage and slip through.",
              "move_to_room_id": "cave_tomb_opening"
            },
            "on_fail": { "text": "You find nothing but smooth stone." }
          }
        }
      }
    ]
  }
]

## Items

Item JSON – Sunken King’s Cave Adventure

This document defines the item JSON used in the Sunken King’s Cave test adventure. Items are split into weapons, quest items, trade goods, and trinkets. Prices are not embedded here and are handled by shops or buyers.

⸻

Weapons

Bone Hunting Knife

{
  "item_id": "weapon_bone_hunting_knife",
  "name": "Bone Hunting Knife",
  "category": "weapon",
  "weapon_template": "dagger",
  "modifier": "bone",
  "damage": { "min": 2, "max": 3 },
  "damage_type": "piercing",
  "crit_rate": 0.1,
  "speed": 1.3,
  "durability": 25,
  "tags": ["crude", "light", "starter"],
  "base_value": 35,
  "description": "A crude knife carved from bone and lashed with dried cord. Poorly balanced, but sharp enough to draw blood."
}


⸻

Coral Trident (Magical)

{
  "item_id": "weapon_coral_trident",
  "name": "Coral Trident",
  "category": "weapon",
  "weapon_template": "spear",
  "modifier": "coral",
  "damage": { "min": 5, "max": 8 },
  "damage_type": "piercing",
  "crit_rate": 0.15,
  "speed": 0.9,
  "durability": 60,
  "magic": {
    "element": "water",
    "effect": "On critical hit, applies [Soaked] reducing target Dodging by 1 for 2 rounds."
  },
  "tags": ["magical", "ancient", "two_handed"],
  "base_value": 1200,
  "description": "A trident grown from living coral, warm to the touch. It hums faintly, as if remembering the sea."
}


⸻

Quest Items

Coral Idol

{
  "item_id": "quest_coral_idol",
  "name": "Coral Idol",
  "category": "quest",
  "quest_bound": true,
  "base_value": 0,
  "tags": ["idol", "ancient", "ritual"],
  "description": "A smooth coral idol worn by time. It radiates a subtle warmth, as if meant to be returned somewhere important."
}


⸻

Trade Goods

Rare Sea Snail

{
  "item_id": "trade_rare_sea_snail",
  "name": "Rare Sea Snail",
  "category": "trade",
  "tags": ["rare", "creature", "coastal"],
  "base_value": 220,
  "description": "A rare sea snail prized by collectors and alchemists for its patterned shell."
}


⸻

Tomb Gems

{
  "item_id": "trade_tomb_gems",
  "name": "Ancient Tomb Gems",
  "category": "trade",
  "stackable": true,
  "tags": ["gem", "ancient"],
  "base_value": 180,
  "description": "Dull gemstones worked long ago, still valuable despite the age etched into them."
}


⸻

Skinshaw Artwork

{
  "item_id": "trade_skinshaw_art",
  "name": "Skinshaw Artwork",
  "category": "trade",
  "tags": ["art", "ancient", "cultural"],
  "base_value": 260,
  "description": "Artwork etched and dyed into cured hide, depicting forgotten rituals and figures."
}


⸻

Trinkets

Seashell Necklace

{
  "item_id": "trinket_seashell_necklace",
  "name": "Seashell Necklace",
  "category": "trinket",
  "tags": ["jewelry", "coastal"],
  "base_value": 75,
  "description": "A necklace strung from polished seashells. Simple, but charming."
}


⸻

Design Notes
	•	Weapons reference templates + material modifiers
	•	Quest items are flagged quest_bound and not sellable by default
	•	Trade goods gain value based on faction demand
	•	Trinkets are flavor items that can influence dialogue or reputation later

This item set is intentionally small and readable — perfect for validating:
	•	loot drops
	•	inventory handling
	•	durability
	•	selling & reputation modifiers

⸻

Next logical expansions: armor items, repair kits, alchemy reagents, and creature drops.

## NPCs/Creatures
[
  {
    "entity_id": "old_lorek_docks",
    "type": "npc",
    "name": "Old Lorek",
    "tier": "low",
    "level": 2,
    "role": "civilian",
    "faction_id": "new_cove_town",
    "default_outlook": 0,

    "spawn_rules": {
      "room_id": "docks",
      "schedule": { "start_hour": 6, "end_hour": 11 },
      "days": "all"
    },

    "description_on_enter": "An old fisherman with a salt-crusted beard sits near the edge of the docks, staring out toward the open sea. His small skiff rocks gently beside him.",

    "attributes": {
      "physical": 1,
      "mental": 2,
      "spiritual": 1,
      "social": 3
    },

    "skills": {
      "Persuading": 3,
      "Bargaining": 2,
      "Remembering": 2,
      "Investigating": 1,
      "Fighting": 1,
      "Dodging": 1
    },

    "maneuvers": [],

    "dialogue": {
      "greeting": [
        "Old Lorek squints at you. \"You look like the sort that doesn't scare easy.\"",
        "\"If you're here for work, there's plenty. If you're here for trouble, take it elsewhere.\""
      ],
      "keywords": {
        "cave": [
          "\"Found a cave along the coast. Low mouth. Smells wrong. Like the sea remembers it.\"",
          "\"I won't step inside. Something in there ain't for men like me.\""
        ],
        "spirits": [
          "\"Call 'em spirits if you want. Whispers. Cold spots. The feeling of being watched.\"",
          "\"I heard something move where nothing should.\""
        ],
        "boat": [
          "\"Aye… I could take you. But I'm not risking my hide for nothing.\"",
          "He grips the rope hard. \"You want me to row you there… you'll have to convince me.\""
        ]
      }
    },

    "interactions": [
      {
        "interaction_id": "lorek_take_to_cave",
        "verb": "talk",
        "keywords": ["boat", "cave", "take", "row", "coast"],
        "once_per_player": true,

        "gating": {
          "requires_flag_not_set": "quest_sunken_cave_unlocked"
        },

        "skill_challenge": {
          "skill": "Persuading",
          "difficulty": 10,
          "on_success": {
            "set_player_flag": "quest_sunken_cave_unlocked",
            "text": "Old Lorek exhales slowly. \"Fine. Fine. You’ve got that look in your eyes. I’ll take you… but I’m not going in.\"",
            "next_options": [
              { "text": "Travel with Old Lorek now", "action": { "travel_to_room_id": "cave_outside" } },
              { "text": "Not yet", "action": { "do_nothing": true } }
            ]
          },
          "on_fail": {
            "text": "Old Lorek shakes his head. \"No. Not today. I've got a bad feeling.\""
          }
        }
      },

      {
        "interaction_id": "lorek_take_to_cave_after_unlock",
        "verb": "talk",
        "keywords": ["travel", "boat", "go", "cave"],
        "gating": {
          "requires_player_flag": "quest_sunken_cave_unlocked"
        },
        "action": {
          "text": "Old Lorek nods once. \"Alright then. Get in. I’ll drop you at the mouth.\"",
          "travel_to_room_id": "cave_outside"
        }
      }
    ]
  },

  {
    "entity_id": "old_lorek_outside",
    "type": "npc",
    "name": "Old Lorek",
    "tier": "low",
    "level": 2,
    "role": "civilian",
    "faction_id": "new_cove_town",
    "default_outlook": 0,

    "spawn_rules": {
      "room_id": "cave_outside",
      "schedule": { "start_hour": 0, "end_hour": 24 },
      "days": "all"
    },

    "description_on_enter": "Old Lorek stands by his skiff, avoiding the cave mouth as if it might look back.",

    "attributes": {
      "physical": 1,
      "mental": 2,
      "spiritual": 1,
      "social": 3
    },

    "skills": {
      "Persuading": 3,
      "Bargaining": 2,
      "Remembering": 2
    },

    "dialogue": {
      "greeting": [
        "\"I’ll wait here. Don’t ask me to come in.\"",
        "\"When you're ready… you say the word, and we go back.\""
      ],
      "keywords": {
        "return": [
          "\"Back to the docks? Good. I don’t like this place.\""
        ]
      }
    },

    "interactions": [
      {
        "interaction_id": "lorek_return_to_docks",
        "verb": "talk",
        "keywords": ["back", "return", "docks", "new cove"],
        "action": {
          "text": "Old Lorek helps you into the skiff and rows away from the cave without looking back.",
          "travel_to_room_id": "docks"
        }
      }
    ]
  }
]

{
  "template_id": "reef_crab",
  "name": "Reef Crab",
  "type": "creature",
  "tier": "low",
  "level": 1,
  "role": "minion",
  "faction_id": "wildlife",
  "outlook_matrix_default": -1,

  "stats": {
    "hp": 6,
    "attack": 3,
    "attack_speed": 1.2,
    "dodge": 1
  },

  "damage": {
    "type": "crushing",
    "min": 1,
    "max": 2
  },

  "attributes": {
    "physical": 2,
    "mental": 0,
    "spiritual": 0,
    "social": 0
  },

  "skills": {
    "Fighting": 2,
    "Dodging": 2,
    "Tracking": 1
  },

  "maneuvers": [
    {
      "maneuver_id": "pinching",
      "name": "Pinching",
      "learned": false,
      "cooldown_seconds": 6,
      "effect": "Deals light crushing damage."
    }
  ],

  "ai": {
    "style": "swarm",
    "targeting": "lowest_hp",
    "flee_threshold": 0,
    "pursue_rooms": 0
  },

  "exp_value": 6,
  "loot": {
    "table_id": "loot_reef_crab_common",
    "rolls": 1
  }
}

{
  "template_id": "reef_crab_brute",
  "name": "Reef Crab Matron",
  "type": "creature",
  "tier": "low",
  "level": 3,
  "role": "brute",
  "faction_id": "wildlife",
  "outlook_matrix_default": -2,

  "stats": {
    "hp": 38,
    "attack": 6,
    "attack_speed": 0.9,
    "dodge": 1
  },

  "damage": {
    "type": "crushing",
    "min": 3,
    "max": 6
  },

  "attributes": {
    "physical": 4,
    "mental": 0,
    "spiritual": 0,
    "social": 0
  },

  "skills": {
    "Fighting": 4,
    "Dodging": 1
  },

  "maneuvers": [
    {
      "maneuver_id": "shell_slam",
      "name": "Shell Slamming",
      "learned": false,
      "cooldown_seconds": 10,
      "effect": "Heavy crushing damage. Small chance to stagger."
    }
  ],

  "ai": {
    "style": "brute",
    "targeting": "highest_threat",
    "flee_threshold": 0,
    "pursue_rooms": 0
  },

  "exp_value": 45,
  "loot": {
    "table_id": "loot_mother_crab",
    "rolls": 1
  }
}

{
  "template_id": "drowned_king_skeleton",
  "name": "The Drowned King",
  "type": "creature",
  "tier": "low",
  "level": 5,
  "role": "boss",
  "faction_id": "ancient_dead",
  "outlook_matrix_default": -6,

  "stats": {
    "hp": 120,
    "attack": 10,
    "attack_speed": 1.0,
    "dodge": 2
  },

  "resistances": {
    "cold": 0.25,
    "necrotic": 0.5,
    "poison": 1.0
  },

  "damage": {
    "type": "slashing",
    "min": 6,
    "max": 12
  },

  "attributes": {
    "physical": 5,
    "mental": 2,
    "spiritual": 3,
    "social": 0
  },

  "skills": {
    "Fighting": 6,
    "Dodging": 2,
    "Intimidating": 4,
    "Warding": 2
  },

  "maneuvers": [
    {
      "maneuver_id": "kingly_curse",
      "name": "Kingly Cursing",
      "learned": false,
      "cooldown_seconds": 14,
      "effect": "Applies a fear-like debuff (lower Dodging by 1 for 2 rounds)."
    },
    {
      "maneuver_id": "bone_rush",
      "name": "Bone Rushing",
      "learned": false,
      "cooldown_seconds": 10,
      "effect": "A heavy strike that deals extra damage if target is below half HP."
    }
  ],

  "ai": {
    "style": "boss",
    "phases": [
      {
        "name": "Awakening",
        "hp_percent_min": 51,
        "behavior": "aggressive"
      },
      {
        "name": "Rage of the Throne",
        "hp_percent_min": 0,
        "behavior": "uses_maneuvers_more"
      }
    ],
    "targeting": "highest_threat",
    "flee_threshold": 0,
    "pursue_rooms": 0
  },

  "exp_value": 220,
  "loot": {
    "table_id": "loot_drowned_king_boss",
    "rolls": 2,
    "guaranteed": ["trade_tomb_gems"],
    "chance_items": [
      { "item_id": "weapon_coral_trident", "chance": 0.35 },
      { "item_id": "trade_skinshaw_art", "chance": 0.6 }
    ]
  }
}


### **1️⃣ NPC Skill-Gated Interaction System**

  

You already do keyword dialogue — this adds **skill checks inside dialogue**.

  

**Required features**

- NPC interaction can trigger:
    
    - a skill check (Persuading)
        
    - success/failure outcomes
        
    
- Must support:
    
    - once_per_player
        
    - player_flag or world_flag
        
    
- Must not repeat once passed
    

  

**Used by**

- Old Lorek persuasion gate
    
- (Later: bribery, intimidation, ritual checks)
    

  

✅ You already designed this _implicitly_ — now it’s formal.

---

### **2️⃣ Player Flags / Quest State**

  

You need **persistent per-player state**.

  

**Required features**

- Set / check boolean flags:
    
    - quest_sunken_cave_unlocked
        
    
- Persist across sessions
    
- Usable in:
    
    - NPC interactions
        
    - Room access
        
    - Dialogue branching
        
    

  

**Used by**

- Old Lorek’s “only persuade once”
    
- Re-entering the cave later without re-rolling
    

  

This is _not_ a quest log — just lightweight state.

---

### **3️⃣ Room Runtime State (You Already Started This)**

  

You correctly identified this earlier.

  

**Required features**

- Separate **room template JSON** from **room_state**
    
- room_state tracks:
    
    - spawned creatures
        
    - remaining loot
        
    - puzzle solved state
        
    - encounter cooldowns
        
    

  

**Used by**

- Crab encounters
    
- Boss death persistence
    
- Idol taken / door opened
    
- Preventing re-looting bones, nests, idol
    

  

This is the backbone of persistence.

---

### **4️⃣ Puzzle / Item-Gated Exits**

  

You need exits that are **conditionally available**.

  

**Required features**

- Exit can be:
    
    - locked
        
    - unlocked by item placement
        
    - unlocked by flag
        
    
- Puzzle resolution updates room_state
    

  

**Used by**

- Coral idol door
    
- Secret passages
    

  

You’ve already modeled this in JSON — engine support is the missing piece.

---

## **2. Systems You Need to Extend (Not New)**

  

These exist conceptually but need one more layer.

---

### **5️⃣ Combat Encounter Lifecycle**

  

You already have combat — this adds **encounter ownership and cleanup**.

  

**Required extensions**

- Static encounter instance:
    
    - spawns creatures
        
    - tracks “defeated”
        
    
- On defeat:
    
    - remove creatures from room_state
        
    - roll loot once
        
    - start respawn timer
        
    
- Encounter must not respawn while players are inside
    

  

**Used by**

- Reef crab rooms
    
- Mother crab nest
    
- Skeleton King boss
    

  

Without this, farming/exploits happen instantly.

---

### **6️⃣ Environmental Hazards System**

  

This is _combat-adjacent_, not combat.

  

**Required features**

- Skill check tied to:
    
    - movement (cross)
        
    - interaction
        
    
- On failure:
    
    - damage
        
    - forced movement
        
    
- Non-hostile, non-combat
    

  

**Used by**

- Pit crossing
    
- Falling damage
    
- Climbing out
    

  

This system will get reused everywhere (bridges, cliffs, ice, fire).

---

### **7️⃣ Secret Detection System**

  

You already have Investigating — this system defines **hidden things**.

  

**Required features**

- Interactable marked as hidden
    
- Revealed via skill check
    
- Once revealed:
    
    - becomes permanent for that player or room_state
        
    

  

**Used by**

- Secret doors
    
- Hidden bone knife
    
- Hidden idol passage
    

---

## **3. Optional but Very Smart Systems (Soon, Not Now)**

  

You _don’t_ need these immediately — but this adventure will hint that you want them.

---

### **8️⃣ NPC Transport / Escort Abstraction**

  

Right now, Old Lorek teleports you.

  

Later, you’ll want:

- timed travel
    
- ambush chance
    
- weather effects
    
- group boarding
    

  

For now:

- instant travel is fine
    
- but isolate this as a **transport action**, not generic teleport
    

---

### **9️⃣ Time-Based NPC Scheduling**

  

You already planned this — this adventure _uses it for real_.

  

**Required**

- NPC spawn windows by in-game time
    
- NPC despawns outside window
    
- Interaction should fail gracefully if missed
    

  

This makes New Cove feel alive.

---

### **🔟 Soft Fail & Recovery Rules**

  

Not a system, but a rule set.

  

Examples:

- If players leave mid-dungeon → encounter resets later
    
- If they die → wake in town, dungeon persists
    
- If idol is dropped → returns to room_state
    

  

Write these rules once — they prevent edge-case hell.