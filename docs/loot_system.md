Loot System – Corpses, Loot Tables, Persistence

Purpose

Introduce a reliable loot mechanic so that when a creature dies it becomes lootable (via a corpse entity), and its drops are persisted in room state. This prevents “missed drops” (e.g., the boss trident not appearing) because loot is generated once and stored as an object players can interact with.

⸻

Design Goals
	•	Deterministic once rolled: loot is rolled once on death and stored; it is not re-rolled per command.
	•	Persistent: loot remains available until taken or until the corpse decays.
	•	Supports multiple drop types:
	•	Guaranteed item(s)
	•	Chance-based item(s)
	•	Loot tables (weighted)
	•	Coin drops
	•	Equipment drops (optional later)
	•	Multiplayer-friendly: supports contributor/party ownership windows.
	•	Room cleanliness: corpse decay removes the entity and any remaining loot.

⸻

Core Flow
	1.	Creature reaches 0 HP.
	2.	Server runs generate_loot(creature_template.loot).
	3.	Server spawns a corpse entity into the room state with rolled loot attached.
	4.	Players use loot, loot <corpse>, loot all, or take <item> from <corpse>.
	5.	Corpse decays after a timer (or is removed when empty).

⸻

Data Model

Creature Template: loot block

Add a loot block to creature templates.

"loot": {
  "corpse_template_id": "corpse_humanoid",
  "decay_seconds": 600,
  "generate_on_death": true,

  "guaranteed": [
    { "item_id": "item_id_here", "count": 1 }
  ],

  "tables": [
    { "loot_table_id": "loot_table_id_here", "rolls": 1 }
  ],

  "chance": [
    { "item_id": "rare_item_id_here", "chance": 0.35, "count": 1 }
  ],

  "coins": { "min": 10, "max": 25 }
}

Notes
	•	guaranteed: always included.
	•	tables: each roll picks one entry (weighted) and adds a quantity.
	•	chance: independent chance rolls.
	•	coins: rolled once on death.

⸻

Room State: corpse entity

When a creature dies, spawn an entity in the room’s state.

{
  "entity_id": "corpse_drowned_king_001",
  "entity_type": "corpse",
  "name": "corpse of a crowned skeleton",
  "description": "The bones lie scattered, half-buried in grit. Something glints among the ribs.",
  "source_creature_id": "drowned_king_skeleton",
  "created_at": 123456789,
  "decays_at": 123456789,
  "flags": ["lootable"],

  "ownership": {
    "mode": "contributors",
    "allowed_player_ids": ["p1", "p2"],
    "expires_at": 123456999
  },

  "loot": {
    "rolled": true,
    "coins": 18,
    "items": [
      { "item_id": "gem_seaglass_shard", "count": 2 },
      { "item_id": "trade_scrimshaw_panel", "count": 1 },
      { "item_id": "weapon_coral_trident", "count": 1 }
    ]
  }
}

Key rule: Loot is stored on the corpse, not inferred from a message.

⸻

Loot Tables

Loot tables are reusable, weighted lists.

{
  "loot_table_id": "loot_kings_tomb_tradegoods",
  "entries": [
    { "item_id": "trade_scrimshaw_panel", "weight": 50, "min": 1, "max": 1 },
    { "item_id": "trade_carved_coral_token", "weight": 30, "min": 1, "max": 2 },
    { "item_id": "trade_old_coin_bundle", "weight": 20, "min": 1, "max": 1 }
  ]
}

Table Roll Rules
	•	For each rolls:
	•	Pick exactly one entry by weight.
	•	Roll quantity between min and max.
	•	Add to corpse loot.

⸻

Player Commands

loot

Lists lootable corpses in the room.

Example output:
	•	You see: corpse of a crowned skeleton

loot <corpse>

Shows corpse contents (if allowed).

Example output:
	•	Coins: 18
	•	Items: coral trident, scrimshaw panel, seaglass shard (x2)

loot all

Takes all coins and items from a corpse.

take <item> from <corpse>

Takes a specific item.

Optional aliases
	•	search corpse
	•	rifle corpse

⸻

Multiplayer Ownership

Loot needs a fair access model.

Recommended: Contributors window
	•	Corpse is owned by the player(s) who contributed to the kill for X seconds.
	•	After expiry, corpse becomes free-for-all.

Ownership block:

"ownership": {
  "mode": "contributors",
  "allowed_player_ids": ["p1","p2"],
  "expires_at": 123456999
}

If a non-owner tries to loot during the window:
	•	You hesitate. This kill isn’t yours to claim yet.

⸻

Decay & Cleanup

Decay timer
	•	Default: decay_seconds from creature template.
	•	On decay:
	•	Remove corpse entity.
	•	Any remaining loot is destroyed.

Optional: remove when empty
	•	If corpse has no items and 0 coins, remove it immediately.

⸻

Integration With Encounters

Room encounters should NOT directly drop items

Instead of on_defeat.drops generating items, use:
	•	on_defeat for text/events
	•	Creature template loot for actual drops

Example boss encounter (room JSON):

"static_encounter": {
  "encounter_id": "enc_boss_drowned_king",
  "respawn_seconds": 1800,
  "composition": [
    { "template_id": "drowned_king_skeleton", "count": 1, "role": "boss" }
  ],
  "on_defeat": {
    "text": "The skeleton collapses into stillness. The chamber feels lighter—as if something finally stopped listening."
  }
}


⸻

Fixing the Coral Trident Drop

To ensure the coral trident reliably exists when it drops:
	•	Move its chance roll to the drowned_king_skeleton template:

"chance": [
  { "item_id": "weapon_coral_trident", "chance": 0.35, "count": 1 }
]

Because loot is persisted on the corpse entity, the trident cannot “vanish” due to message timing or state update issues.

⸻

New Systems Required
	1.	Corpse entity type in room state
	2.	Loot generation (guaranteed + table rolls + chance + coins)
	3.	Loot commands (loot, loot all, take from)
	4.	Ownership window (contributors)
	5.	Decay cleanup job

⸻

Authoring Checklist
	•	Every creature template should define loot.
	•	Bosses should have at least one chance rare item.
	•	Encounters should spawn creatures; creatures spawn corpses.
	•	Loot tables should be reusable across zones.