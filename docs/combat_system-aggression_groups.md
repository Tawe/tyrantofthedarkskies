# Pack Aggression (Group Combat)

## Overview

When a player attacks a creature, all other creatures in the same group automatically join combat against that player. This creates "pack" behavior — hit one, fight them all.

## Grouping Keys

Creatures are grouped by one of two keys (checked in order):

1. **`spawn_group_id`** — Assigned to creatures spawned together from a spawn definition.
2. **`encounter_id`** — Assigned to creatures spawned as part of a random encounter.

If a creature has neither key, it has no pack and is treated as a solo combatant.

## Flow

1. Player issues `attack <creature>` command.
2. `attack_command` in `commands/combat.py` starts combat via `CombatManager.start_combat()`.
3. Immediately after, if the player was not already in combat and the target is an `InstanceCombatTarget`, `CombatManager.alert_pack()` is called.
4. `alert_pack()` scans `runtime_state.get_entities_in_room(room_id)` for entities sharing the same group key as the attacked creature.
5. Each qualifying packmate (alive, not already in combat, not the attacked creature) joins combat targeting the attacker.
6. The player receives a message for each packmate: `"{name} rushes to defend its packmate!"`

## Guard Conditions

`alert_pack()` skips creatures that are:
- The attacked creature itself (matched by `instance_id`)
- Dead (`hp_current <= 0`)
- Already in combat (name present in `combat.combatants`)
- Not in the same group (different `spawn_group_id`/`encounter_id`)

## Files

- `systems/combat_system.py` — `InstanceCombatTarget.encounter_id`, `CombatManager.alert_pack()`
- `commands/combat.py` — Hook after combat initiation
