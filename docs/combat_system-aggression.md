Combat System – Aggression Types & Autoattack Trigger

Purpose

Support two broad classes of enemies:
	1.	Aggressive enemies that attack players on sight
	2.	Passive enemies that only fight if the player initiates (or provokes them)

If an enemy attacks a player, the player’s autoattack should automatically begin.

⸻

Creature Aggression Model

Creature Template Fields

Add an aggression block to every creature/NPC template that can participate in combat.

"aggression": {
  "type": "aggressive",
  "radius_rooms": 0,
  "initial_threat": 10
}

Field definitions
	•	type
	•	"aggressive" – attacks players on sight (after a short delay)
	•	"passive" – will not attack unless provoked
	•	radius_rooms
	•	0 – only engages players in the same room
	•	(future) 1+ – can engage across adjacent rooms (patrol/hearing)
	•	initial_threat
	•	starting threat value applied when the creature chooses a target

⸻

Engagement Rules

On Player Enter Room

When a player enters a room, the server evaluates each creature in the room.

A creature may auto-engage if:
	•	creature is alive and can fight
	•	room is not flagged safe (or safe rules allow combat)
	•	aggression.type == "aggressive"
	•	player is a valid target (not ignored by faction/outlook rules)

Recommended engage delay: 1 tick (or ~1–2 seconds)
	•	This provides a readable warning moment before damage lands.

Messaging pattern
	1.	Warning cue:

	•	“A reef crab swivels toward you, claws clicking.”

	2.	Engage cue:

	•	“The reef crab attacks you!”

⸻

Autoattack Trigger Requirement

If a creature attacks a player

When the first hostile attack lands or combat is initiated by a creature:
	•	player enters combat state
	•	player autoattack begins immediately if not already running

Key rule:
	•	Incoming aggression should not require the player to type attack.

Messaging pattern
	•	“The reef crab attacks you!”
	•	“You ready your weapon and fight back.”

⸻

Target Selection Rules (Multi-enemy)

To avoid chaotic target switching:

If player has no current autoattack target
	•	set autoattack_target = attacker

If player already has a target
	•	do not switch targets automatically
	•	add attacker to engaged_by list

This prevents “target thrash” during multi-mob fights.

⸻

Combat State Tracking

Per Player (minimum)
	•	in_combat: bool
	•	autoattack_enabled: bool
	•	autoattack_target_entity_id: string|null
	•	autoattack_next_tick: timestamp
	•	engaged_by: [entity_id] (enemies currently attacking player)

Per Creature (minimum)
	•	in_combat: bool
	•	target_player_id: string|null
	•	attack_next_tick: timestamp
	•	aggression.type

⸻

Combat Initiation (Both Directions)

Player initiates

attack <target>:
	•	sets both parties to combat state
	•	starts player autoattack immediately
	•	creature targets the player

Creature initiates (aggressive)
	•	creature targets player and attacks
	•	player autoattack begins automatically

⸻

Safe Rooms

If a room has safe flag:
	•	aggressive creatures should not auto-engage
	•	optionally block all combat initiation in safe rooms

Recommended rule:
	•	Safe rooms disallow auto-engage and block hostile action commands.

⸻

Unarmed Fallback

If player is unarmed when autoattack begins:
	•	use the unarmed attack template
	•	player still fights back automatically

⸻

Leaving Combat via Movement

On room exit by a player:
	•	either stop combat immediately (simple model)
	•	or allow enemies with can_follow=true to chase (future)

⸻

Minimal Template Examples

Aggressive creature

"aggression": { "type": "aggressive", "radius_rooms": 0 }

Passive creature

"aggression": { "type": "passive" }


⸻

Implementation Hooks (Suggested)
	•	on_player_enter_room(player_id, room_id)
	•	scan room entities for aggressive creatures
	•	schedule engage after 1 tick
	•	on_creature_attack(creature_id, player_id)
	•	if player not autoattacking → start autoattack
	•	start_autoattack(player_id, target_entity_id)
	•	compute interval via weapon speed / unarmed speed
	•	set autoattack_next_tick