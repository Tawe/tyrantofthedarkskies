Weather System

This document defines the regional weather system for Tyrant of the Dark Skies. The goal is to make the world feel alive and reactive without introducing per-room simulation overhead or clunky mechanics.

Weather is designed to be:
	•	Regional, not per-room
	•	Mostly atmospheric, with light mechanical impact
	•	Predictable enough to plan around, but not static

⸻

Design Goals
	•	Avoid per-room weather state
	•	Ensure multiple players in nearby areas experience the same conditions
	•	Allow weather to influence combat, exploration, and durability subtly
	•	Keep descriptions readable and non-repetitive

⸻

Core Concept: Regional Weather

Weather is tracked per region (also called zones).

Examples of regions:
	•	new_cove_town
	•	unflooded_sea
	•	kelp_plains
	•	rift_forest

Each room belongs to exactly one region and inherits that region’s current weather.

⸻

Room-Level Requirements

Each room must define:

"region_id": "unflooded_sea",
"weather_exposure": "outdoor"

Weather Exposure Values
	•	indoor – weather not visible or impactful
	•	sheltered – weather visible, reduced impact
	•	outdoor – full visual and mechanical impact
	•	coastal – weather amplified by wind and salt

⸻

Weather State Model

Weather is stored in a region_weather table.

Required Fields
	•	region_id
	•	weather_type (e.g., clear, fog, squall)
	•	intensity (0–3)
	•	started_at
	•	next_change_at
	•	seed (optional, for deterministic rolls)

Only one active weather state exists per region at a time.

⸻

Weather Update Rules

Weather updates occur when:
	•	A player enters a room in the region AND now >= next_change_at
	•	A scheduled world tick runs

Weather never updates continuously per room.

⸻

Weather Rendering Rules

Weather is not baked into room descriptions.

Instead, when a room is rendered, the current regional weather is appended as an overlay line.

Example

A cold fog crawls over the kelp flats, muffling sound and swallowing distant shapes.

Overlay lines should:
	•	Be short
	•	Change only when the weather changes
	•	Respect weather_exposure

⸻

Mechanical Effects (Lightweight)

Weather effects should be subtle and situational.

Examples

Weather	Effect
Fog	−Accuracy for ranged attacks at Far range
High Wind	Harder to maintain Far range
Squall	Increased disengage failure chance
Cold Snap	Minor stamina drain outdoors
Salt Rain	Increased armor/weapon durability loss

Effects scale with intensity.

⸻

Weather Transitions

Each region defines a weather transition table.

Example:

{
  "clear": { "clear": 50, "fog": 30, "wind": 20 },
  "fog": { "fog": 40, "clear": 40, "squall": 20 },
  "squall": { "wind": 50, "clear": 50 }
}

Transitions are rolled when the weather changes.

⸻

Encounter & AI Integration

Weather may influence:
	•	Encounter roll weights
	•	Creature behavior (ambush preference, disengage likelihood)
	•	Visibility-based maneuvers

Weather effects must never hard-lock player action.

⸻

Persistence Rules
	•	Weather persists even if no players are present
	•	Weather state is stored until explicitly changed
	•	Server restarts must restore weather from the database

⸻

Messaging Rules

Players should be notified when weather changes only if they are present in the region.

Example:

The wind rises suddenly, whipping the kelp plains into motion.

⸻

Design Constraints
	•	Weather must never override room safety flags
	•	Indoor rooms suppress mechanical effects
	•	Weather descriptions must avoid repetition fatigue

⸻

Future Extensions (Optional)
	•	Seasonal weather patterns
	•	Magical anomalies
	•	Weather-linked quests
	•	Player-crafted shelters or wards

⸻

Summary

The weather system:
	•	Is regional, persistent, and lightweight
	•	Enhances atmosphere without overwhelming mechanics
	•	Integrates naturally with combat, durability, and exploration

It should feel like the world is breathing — not simulating every gust.