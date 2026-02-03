NPC Dialogue System – Emote, Tone, Volume

Purpose

This system defines how NPC dialogue is structured, rendered, and extended in Tyrant of the Dark Skies. It separates what an NPC does (emote) from what an NPC says (spoken text), allowing for cleaner presentation, better immersion, and future extensibility.

This system applies to:
	•	NPC greetings
	•	Keyword-based dialogue
	•	Ambient NPC chatter
	•	Event-driven NPC responses

⸻

Core Design Principles
	1.	Actions and speech are separate
	•	NPCs do things (emotes)
	•	NPCs say things (dialogue)
	2.	Dialogue text contains no action verbs
	•	All physical or expressive behavior lives in emote
	3.	The engine controls presentation
	•	Content authors do not embed quotation marks
	•	The renderer decides formatting (“says:”, line breaks, etc.)
	4.	Minimal now, extensible later
	•	tone and volume are optional
	•	They do not affect mechanics yet, but are future-proof hooks

⸻

Dialogue Object Schema

{
  "emote": "string (optional)",
  "say": "string (required)",
  "tone": "string (optional)",
  "volume": "string (optional)"
}

Field Definitions

emote
	•	Describes a visible action or physical cue
	•	Rendered as a separate sentence or clause
	•	Never contains spoken words

Examples:
	•	“nods west”
	•	“leans closer”
	•	“raises his voice over the din”
	•	“folds his arms”

⸻

say
	•	The spoken dialogue text
	•	May include keyword brackets (e.g. [work], [rumors])
	•	Contains no quotation marks

Examples:
	•	“Guild board’s through there. Easy jobs vanish fast.”
	•	“If you want a [drink], speak up.”

⸻

tone (optional)
	•	Describes emotional or social intent
	•	Currently informational only
	•	Reserved for future systems (reaction modifiers, social checks, AI voice)

Suggested values:
	•	“neutral”
	•	“gruff”
	•	“amused”
	•	“annoyed”
	•	“quiet”
	•	“threatening”

⸻

volume (optional)
	•	Describes how loudly the NPC speaks
	•	Useful for crowd scenes and stealth contexts
	•	Currently informational only

Suggested values:
	•	“normal”
	•	“quiet”
	•	“loud”
	•	“shout”

⸻

Rendering Guidelines (Engine-Side)

The engine is responsible for formatting output. Example renderings:

Standard

Bram nods west.
Bram says: Guild board’s through there. Easy jobs vanish fast.

Combined (optional style)

Bram nods west and says: Guild board’s through there. Easy jobs vanish fast.

With Tone/Volume (future)

Bram leans in and says quietly: That’s not something you ask loudly.

Content authors do not control this formatting.

⸻

Usage Examples

Greeting

{
  "emote": "sizes you up",
  "say": "If you want a [drink], speak up. If you want [food], pay first."
}


⸻

Keyword Response

{
  "key": "work",
  "text": {
    "emote": "nods west",
    "say": "Guild board’s through there. Easy jobs vanish fast. The good ones come with [rumors]."
  }
}


⸻

Ambient Line

{
  "emote": "raises his voice over the din",
  "say": "Last call for [drink]!"
}


⸻

Hard Rules (Authoring)
	•	❌ Do not include quotation marks in say
	•	❌ Do not embed actions in dialogue text
	•	❌ Do not rely on formatting characters (”—”, quotes, italics)
	•	✅ Use emote for all physical behavior
	•	✅ Use say only for spoken words
	•	✅ Use brackets for keyword discovery

⸻

Benefits

This system:
	•	Eliminates nested-quote bugs
	•	Improves readability in a text-only medium
	•	Makes NPCs feel alive without bloating text
	•	Provides a clean path to future AI-driven NPC behavior

⸻

Adoption Recommendation

All new NPC content must use this structure.

Existing NPCs should be refactored opportunistically when touched.

This document is the authoritative reference for NPC dialogue going forward.