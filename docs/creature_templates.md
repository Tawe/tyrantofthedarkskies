# Creature Templates – Unflooded Sea Region

JSON-style **template definitions** for every creature/NPC-combatant referenced in the random encounter tables.

> **Note:** These are **templates**, not instances. Runtime HP, target, status effects, room position, and encounter_id live in your runtime state tables.

---

## Common Template Schema

Each template uses this consistent shape:

```json
{
  "template_id": "string",
  "name": "string",
  "entity_type": "creature",
  "tier": "low",
  "level_range": [1, 5],
  "role": "minion|brute|boss|artillery|healer|controller",

  "stats": {
    "hp_max": 10,
    "attack": {
      "speed_cost": 1.0,
      "accuracy": 10,
      "damage_min": 1,
      "damage_max": 2,
      "damage_type": "piercing",
      "crit_chance": 0.05
    }
  },

  "skills": {
    "Dodging": 10,
    "Fighting": 10,
    "Climbing": 0,
    "Swimming": 0
  },

  "behaviors": {
    "preferred_range_band": "engaged",
    "pursue": "none|short|long",
    "leash_radius": 1,
    "leash_time": 20,
    "threat_profile": "default|swarm|sniper|healer|controller",
    "morale": {
      "flee_at_hp_pct": 0.0
    }
  },

  "loot": {
    "loot_table_id": "string",
    "xp_value": 10
  },

  "maneuvers": ["maneuver_id_1", "maneuver_id_2"]
}
```

Suggested baseline for **Low Tier** values:

* Minion HP: 4–10
* Brute HP: 18–40
* Artillery HP: 10–22
* Controller HP: 12–26
* Healer HP: 12–24
* Boss HP: 60–120

---

# Unflooded Sea Creatures

## Kelp Flea (Minion)

- **template_id:** kelp_flea
- **role:** minion
- **stats:** hp_max 6, attack speed_cost 0.7, damage 1–2 piercing, crit 0.03
- **skills:** Dodging 14, Fighting 8, Climbing 18
- **behaviors:** pursue short, leash 1/12s, threat_profile swarm
- **loot:** loot_table_id loot_kelp_flea, xp_value 6
- **maneuvers:** swarm_snap, skitter

## Reef Crab (Minion)

- **template_id:** reef_crab
- **role:** minion
- **stats:** hp_max 9, attack speed_cost 1.0, damage 1–3 crushing, crit 0.04
- **skills:** Dodging 8, Fighting 9
- **behaviors:** pursue short, leash 1/14s
- **loot:** loot_reef_crab, xp 8
- **maneuvers:** pinch, shell_brace

## Reef Crab Brute (Brute)

- **template_id:** reef_crab_brute
- **role:** brute
- **stats:** hp_max 34, damage 3–6 crushing
- **loot:** loot_reef_crab_brute, xp 28
- **maneuvers:** crushing_clamp, shell_bulwark

## Rift Wisp (Artillery)

- **template_id:** rift_wisp
- **role:** artillery
- **stats:** hp_max 18, damage 2–5 force, preferred_range_band far, pursue none
- **loot:** loot_rift_wisp, xp 22
- **maneuvers:** wisp_bolt, phase_flicker

## Unflooded Stalker (Brute)

- **template_id:** unflooded_stalker
- **role:** brute
- **stats:** hp_max 38, damage 4–7 slashing
- **loot:** loot_unflooded_stalker, xp 32
- **maneuvers:** ambush_lunge, mauling_bite

## Crabfolk Scout (Minion)

- **template_id:** crabfolk_scout
- **role:** minion
- **stats:** hp_max 10, damage 2–4 piercing
- **loot:** loot_crabfolk_scout, xp 16
- **maneuvers:** net_cast, withdraw

## Ancient Sentinel Fragment (Boss – Rare)

- **template_id:** ancient_sentinel_fragment
- **role:** boss
- **stats:** hp_max 110, damage 6–12 bludgeoning
- **loot:** loot_ancient_sentinel_fragment, xp 140
- **maneuvers:** stone_slam, shard_burst, unyielding

---

# Kelp Plains Creatures

## Kelp Crawler (Controller)

- **template_id:** kelp_crawler
- **role:** controller
- **stats:** hp_max 22, damage 2–4 poison
- **maneuvers:** entangle, drag_under

## Kelp Shade (Controller)

- **template_id:** kelp_shade
- **role:** controller
- **stats:** hp_max 26, damage 2–5 psychic
- **maneuvers:** dread_whisper, veil_step

## Kelp Plains Alpha (Brute)

- **template_id:** kelp_plains_alpha
- **role:** brute
- **stats:** hp_max 44, damage 5–9 slashing
- **maneuvers:** cleaving_rush, howl

## Kelp Leviathan Spawn (Boss – Rare)

- **template_id:** kelp_leviathan_spawn
- **role:** boss
- **stats:** hp_max 120, damage 7–13 crushing
- **maneuvers:** tail_sweep, kelp_crush, bellow

---

# Rift Forest Creatures

## Rift Skitterling (Minion)

- **template_id:** rift_skitterling
- **role:** minion
- **stats:** hp_max 7, damage 1–3 slashing
- **maneuvers:** skitter, pack_bite

## Coral Stalker (Artillery)

- **template_id:** coral_stalker
- **role:** artillery
- **stats:** hp_max 20, damage 2–6 piercing, preferred_range_band far
- **maneuvers:** spine_shot, bleeding_strike

## Rift Warden (Brute)

- **template_id:** rift_warden
- **role:** brute
- **stats:** hp_max 42, damage 4–8 bludgeoning
- **maneuvers:** wardens_bash, hold_the_line

## Rift Warden Mender (Healer)

- **template_id:** rift_warden_mender
- **role:** healer
- **stats:** hp_max 24, damage 2–4 force
- **maneuvers:** mend_flesh, warding_glow

## Rift Forest Hunter (Controller)

- **template_id:** rift_forest_hunter
- **role:** controller
- **stats:** hp_max 30, damage 3–6 poison
- **maneuvers:** hooking_vines, reposition

## Corrupted Guardian (Brute)

- **template_id:** corrupted_guardian
- **role:** brute
- **stats:** hp_max 55, damage 5–10 necrotic
- **maneuvers:** blight_strike, aura_of_rot

## Rift Heart Sentinel (Boss – Rare)

- **template_id:** rift_heart_sentinel
- **role:** boss
- **stats:** hp_max 130, damage 7–14 earth
- **maneuvers:** rift_quake, coral_shards, anchor_roar

---

# Notes

* The **Crabfolk Scouts** are modeled as creatures here for combat consistency; you can also implement them as NPCs with social states.
* "Lost Explorer" and other non-creature encounters are intentionally excluded.
* Loot table IDs are placeholders; define them in your loot system and keep templates stable.
* Full JSON examples for each creature live in `contributions/creatures/*.json` using the Common Template Schema above.
