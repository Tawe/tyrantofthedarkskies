Micro-Quest Implementation – Landar, Shovel, Dig Mound, Amulet

Goal

Add a small optional loop to test shovel + dig:
	1.	Player hears rumor from Landar (Black Anchor booths)
	2.	Player buys Shovel from Jalia’s Goods
	3.	Player goes to Unflooded Sea, finds a mound
	4.	Player uses dig mound (requires shovel equipped + Physical check)
	5.	On success: player uncovers a small sack containing Amulet of the Forgotten Sea God

⸻

1) Add NPC: Landar to Black Anchor Booths

1.1 Update room JSON: black_anchor_booths
	•	Add the NPC id to npcs.

"npcs": ["hooded_patron", "magitium_agent", "landar_booths"]

1.2 Create NPC JSON: landar_booths

Requirements
	•	Name: Landar
	•	Race: Sharah
	•	Uses emote + say dialogue structure
	•	Primary hint includes keywords: [unflooded sea] [mound] [shovel] [dig]
	•	She does not want to dig it up herself

Suggested dialogue flow
	•	Greeting seeds: [unflooded sea] and [shovel]
	•	[unflooded sea] → leads to [mound]
	•	[mound] → leads to [dig]
	•	[shovel] → points to Jalia (no direct teleport / no quest terminal vibes)

Optional
	•	1–2 ambient lines about silt, kelp plains, or things moving out there.

⸻

2) Add Item: Shovel

2.1 Create item JSON: tool_shovel_basic

Requirements
	•	Category: tool
	•	Equippable in a tool slot (commonly hands)
	•	Must be detectable via tags: "tags": ["tool", "shovel"]
	•	Include base_price

Recommended fields
	•	item_id, name, category, slot, weight, base_price, tags, description
	•	Optional future-proof: durability

⸻

3) Add Shovel to Jalia’s Shop

3.1 Ensure shovel exists in global item list
	•	Add tool_shovel_basic to your items JSON.

3.2 Add to Jalia store inventory

Add a store-specific entry (price lives in store config, not the base item):

{ "item_id": "tool_shovel_basic", "price": 35, "stock": { "min": 1, "max": 3 } }

Notes:
	•	Keep the shovel price accessible for early testers.
	•	Stock should not hit 0 during early testing.

⸻

4) Add the Mound to the Unflooded Sea Room

4.1 Update unflooded_sea room description

Add a subtle hint (not a spoiler), e.g.:
	•	“A low rise of silt sits oddly intact…”
	•	“One mound looks recently disturbed…”

4.2 Add interactable: mound_of_silt

Interactable requirements
	•	Keywords: ["mound", "silt", "pile", "disturbed"]
	•	examine_text hints at digging without tutorial tone
	•	Hint is best placed on examine, not directly in room description

Example examine hint:
	•	“The silt here is packed and recently turned. With a [shovel], you could try to [dig mound].”

⸻

5) Finding the Mound (Soft Discovery)

5.1 Design rule

Use Investigation to improve clarity, not to gate content.
	•	The mound should be subtly hinted in the room description so all players have a lead.
	•	Investigation reveals stronger confirmation and better direction.

5.2 Room description hint (always visible)

Update unflooded_sea.description to include a subtle, non-spoiler clue, e.g.:
	•	“The silt isn’t uniform here. One low rise looks recently disturbed, as if the ground never quite settled.”

5.3 Investigation action (optional)

Add an Investigation-based action that can be invoked via:
	•	investigate area
	•	investigate silt
	•	investigate mound

On success (clear confirmation):
	•	“Looking closer, you spot tool marks beneath the silt. Someone buried something here recently. With a shovel, you could dig this mound.”

On fail (remain vague, do not deny existence):
	•	“The silt shifts under your boots, but the ground here is hard to read.”

5.4 Once-per-player guidance

The Investigation success message can be shown once per player (optional), but the mound remains interactable regardless.

⸻

6) Implement the dig Mechanic

6.1 Command format
	•	Primary: dig mound
	•	Optional aliases: dig silt, dig pile

6.2 Requirements

To resolve a dig attempt:
	•	Player is in unflooded_sea
	•	Player targets a valid mound interactable
	•	Player has a shovel equipped (tag check)
	•	Player passes a Physical check

6.3 Physical check

Since you don’t have a Digging skill, use a direct attribute check for this test.
	•	Suggested difficulty: 10–12 (early-friendly)

6.4 One-time reward per player

Reward should be once per player.
	•	Store via player flag, e.g. found_mound_treasure = true
	•	If flag already set: “You’ve already dug this spot up.”

⸻

6) Reward Items

6.1 Optional container: small sack

If containers are supported, spawn a sack with the amulet inside.
	•	item_id: container_small_sack
	•	category: container

6.2 Magical item: Amulet of the Forgotten Sea God

Create a new equippable item.
	•	item_id: magic_amulet_forgotten_sea_god
	•	category: accessory (or equipment)
	•	slot: neck
	•	Description: ancient / saltworn / half-remembered deity

Suggested simple effect (keep tiny for early game)
	•	Passive: +1 Spiritual OR +1 Warding
	•	Or: purely flavor for now (if you want to avoid balance changes)

⸻

7) Recommended Player-Facing Text

Landar rumor line
	•	“I saw someone bury something in the [unflooded sea] last night… near a [mound]. Not my problem. Someone with a [shovel] could [dig] it up.”

Dig attempt – no shovel equipped
	•	“You scrape at the packed silt with your hands. You’ll need a shovel to do this properly.”

Dig success
	•	“Your shovel bites into the silt. After a few heavy scoops, you strike cloth-wrapped leather. You uncover a small sack.”

Dig fail
	•	“You dig, but the silt collapses back in. You’ll need stronger effort to get deeper.”

⸻

8) Systems / Files Touched Checklist
	•	black_anchor_booths room JSON (add landar_booths)
	•	New NPC: landar_booths.json
	•	New item: tool_shovel_basic.json
	•	Jalia store inventory: add shovel (store price + stock)
	•	unflooded_sea room JSON:
	•	description hint
	•	mound interactable
	•	Command / interaction system:
	•	implement dig command
	•	shovel-equipped validation (tag-based)
	•	Physical check
	•	per-player completion flag
	•	New item: magic_amulet_forgotten_sea_god.json
	•	Optional: container_small_sack.json

⸻

Acceptance Tests
	1.	Landar appears in Black Anchor booths and hints via keywords.
	2.	Jalia sells a shovel.
	3.	Player equips shovel.
	4.	Player goes to Unflooded Sea and can look mound.
	5.	dig mound without shovel fails with hint.
	6.	dig mound with shovel triggers Physical check.
	7.	On success, player receives sack/amulet.
	8.	Second attempt by same player is blocked by flag.