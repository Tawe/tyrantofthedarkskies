Room UX Style Guide – Descriptions, Exits, Secrets

This canvas captures the updated approach to room text so the MUD feels immersive without leaking map knowledge.

⸻

The Core Problem

Current exit labels are revealing information the character should not know yet:
	•	Naming destinations the player hasn’t visited (e.g., “Toward the drawings”, “To a small alcove”)
	•	Turning the exit list into an omniscient minimap

This breaks immersion and makes exploration feel disjointed.

⸻

Core Principle

Room descriptions communicate sensory intent and risk.
Exits communicate only what the character can be certain about.

What players should learn from a room description
	•	What the place feels like (tone)
	•	What seems dangerous
	•	What directions suggest (without spoilers)

What players should learn from exits
	•	Only that a route exists in that direction
	•	Sometimes: that attempting the route involves an obvious action (cross, climb, swim)

⸻

Rule 1 — Exits Should Not Spoil Unseen Areas

Default exit format:
	•	Exits: [West] [North] [East] [Out]

Avoid:
	•	Exits: [North] (Toward the drawings)
	•	Exits: [East] (To a small alcove)

Those labels leak knowledge the character doesn’t yet have.

⸻

Rule 2 — Put Directional Hints in the Room Description

Instead of labeling exits, add subtle, diegetic clues inside the description.

Example: Watery Cave (improved)

Watery Cave
Shallow pools of salt water dot the cave floor. The stone is slick, and faint skittering echoes from the dark. Broken shell fragments crunch underfoot.

Among the wet rocks, reef crabs click and scuttle, their shells scraping against stone.

To one side, the cave narrows into a low, shadowed recess.
Farther ahead, the passage slopes deeper, where the air feels older and still.
Another route opens wider, where the stone walls look smoother, marked by strange scratches.
Behind you, pale daylight spills in from the cave mouth.

Exits: [West] [North] [East] [Out]

Why this works
	•	Players infer meaning instead of being told
	•	No spoiler words (“drawings”, “alcove”)
	•	Still guides choice through sensory hints

⸻

Rule 3 — When Exit Labels Should Explain Mechanics

Only add exit labels when:
	1.	The action is obvious and visible in the room (pit, ledge, water)
	2.	The danger is not “map knowledge” but a present obstacle

Example: Pit Room

Pit Room
A wide pit splits the chamber floor. The far side is reachable, but the stone near the edge is slick, and the drop disappears into shadow.

Exits:
[South]
[North] (Attempt to cross the pit)

This is not a spoiler; it’s a warning about an immediate hazard.

⸻

Rule 4 — Secret Exits Must Never Appear Until Discovered

Behavior
	•	Secret exits are NOT listed in Exits initially
	•	Secret exits are revealed only via:
	•	Investigating results
	•	An explicit discovery message

Description foreshadowing (subtle)

Add hints like:
	•	“The stone is colder in one spot.”
	•	“A thin draft touches your cheek.”
	•	“One panel looks slightly misaligned.”

On discovery

Print a clear system message:
	•	A hidden passage is revealed to the east.

Then (and only then) the exit appears.

⸻

Rule 5 — NPC Hinting Follows the Same Philosophy

Avoid raw mechanical hints like:
	•	“Try persuading him.”

Use diegetic phrasing that suggests the correct action:
	•	“I won’t row out there for just anyone,” he mutters.

Then seed bracket keywords naturally:
	•	[cave], [spirits], [boat]

⸻

Implementation Notes (Engine)

Exits
	•	Default: render directions only
	•	Optional: render labels only for visible hazards

Secret Exits
	•	Use hidden_exits or interactable-based reveals_exit
	•	Do not render hidden exits until state says discovered

Directional Hinting
	•	Add a short “direction hint paragraph” in room descriptions
	•	Do not name destination rooms until visited

⸻

Quick Checklist for Every Room
	•	Does the room description hint at each direction without spoilers?
	•	Are exits listed without naming unseen locations?
	•	Are hazard exits clearly labeled with the action (cross, climb, swim)?
	•	Are secret exits absent until discovered?
	•	Do NPCs hint through tone and keywords, not explicit system instructions?

⸻

Next Suggested Pass

Apply this style guide to every room in Sunken King’s Cave:
	•	Rewrite descriptions to include directional hints
	•	Strip destination labels from exits
	•	Add explicit hazard labels only where appropriate (pit crossing)
	•	Ensure secrets only appear after discovery