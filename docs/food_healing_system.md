Food & Healing System

This document defines how food and potions restore health in Tyrant of the Dark Skies. The goal is to:
	•	Encourage preparation and downtime
	•	Avoid spammy instant healing
	•	Give potions clear, powerful identity
	•	Fit naturally with your time, combat, and death systems

⸻

Design Philosophy
	1.	Food sustains, potions save
	2.	Healing should feel intentional, not automatic
	3.	Combat should not revolve around potion spam
	4.	Recovery over time reinforces pacing and world simulation

⸻

Health Regeneration Overview

There are three ways to recover health:
	1.	Natural regeneration (very slow)
	2.	Food-based regeneration (slow but reliable)
	3.	Potions (fast, powerful, limited)

⸻

1) Natural Regeneration (Baseline)
	•	All characters regenerate a very small amount of HP over time
	•	Example:
	•	+1 HP every 10 minutes (in-game time)

This is intentionally weak.

Purpose:
	•	Prevents being stuck at 1 HP forever
	•	Not sufficient after combat

⸻

2) Food-Based Healing (Sustain)

Core Rule

Food grants regeneration over time, not burst healing.

Food does not heal instantly.

⸻

How Food Works

When food is consumed:
	•	A Regeneration Effect is applied
	•	Effect lasts a fixed duration
	•	Heals small HP ticks periodically

Example effect:

Well Fed
+1 HP every 2 minutes
Duration: 20 minutes


⸻

Stacking Rules
	•	Only one food regeneration effect may be active at a time
	•	Eating again:
	•	Refreshes duration
	•	Does NOT stack healing rate

This prevents food spam.

⸻

Example Food Tiers

Food Type	Effect	Duration	Notes
Rations	+1 HP / 2 min	20 min	Basic sustain
Hot Meal	+1 HP / 1 min	30 min	Tavern food
Hearty Stew	+2 HP / 1 min	30 min	Rare / expensive

Food effects pause if the character is at full HP.

⸻

3) Potion-Based Healing (Burst)

Core Rule

Potions restore large amounts of HP instantly.

They are meant for:
	•	Emergencies
	•	Combat recovery
	•	Boss fights

⸻

Potion Use Rules
	•	Potions can be used:
	•	In combat
	•	Out of combat
	•	Using a potion:
	•	Consumes an action
	•	Does not interrupt autoattack

⸻

Potion Cooldown

To prevent spam:
	•	After drinking a potion, apply:
	•	Potion Sickness (short cooldown)

Example:

Potion Sickness
Cannot drink another potion for 30 seconds


⸻

Example Potion Values

Potion	Heal	Notes
Simple Healing Potion	20–30 HP	Early game
Strong Healing Potion	45–60 HP	Mid game
Major Healing Potion	80–100 HP	Rare

Potions ignore food stacking rules.

⸻

4) Interaction with Combat System
	•	Food regeneration continues during combat
	•	Food healing is intentionally slow so it does not replace potions
	•	Potions provide immediate survivability

This creates meaningful choices:
	•	Eat before danger
	•	Drink when things go wrong

⸻

5) Interaction with Death System

On death recovery:
	•	Food effects are cleared
	•	Potion sickness is cleared

Players wake up hungry, not buffed.

⸻

6) Messaging (Important for Clarity)

On Eating
	•	“You eat the rations. You feel steadier.”

On Healing Tick
	•	“You regain a small amount of health.”

On Potion Use
	•	“Warmth floods your chest as the potion takes effect.”

Avoid numeric spam in chat logs.

⸻

7) Why This System Works
	•	Reinforces preparation
	•	Makes taverns matter
	•	Makes potions valuable without dominance
	•	Avoids clunky regen mechanics
	•	Easy to tune with just a few numbers

⸻

Summary
	•	Food = slow, sustained healing over time
	•	Potions = fast, powerful emergency healing
	•	Natural regen = minimal safety net

Together, they create a clear, readable healing ecosystem.