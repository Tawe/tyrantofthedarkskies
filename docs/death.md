# **Death & Defeat System**

  

This document defines how **death** works in _Tyrant of the Dark Skies_. The goal is to make death:

- Meaningful but not punitive
    
- Consistent with the tone of a harsh frontier world
    
- Technically simple to implement
    
- Supportive of learning and experimentation
    

  

Death should feel like a **setback**, not a failure state.

---

## **Core Design Principles**

1. **Death is a state change, not a game over**
    
2. Players should always understand _why_ they died
    
3. Recovery should be predictable and fair
    
4. Repeated reckless death should have escalating consequences
    
5. The world should persist even if the player dies
    

---

## **Definitions**

- **Defeat**: Player HP reaches 0
    
- **Death State**: Temporary liminal state between life and recovery
    
- **Recovery**: The process of returning the player to the world
    

---

## **When a Player Is Defeated**

  

### **Trigger**

- Player HP ≤ 0
    

  

### **Immediate Effects**

- Combat ends for the player
    
- Player can no longer act
    
- A clear message is shown:
    
    > _Your vision darkens as your strength fails._
    

---

## **Death State**

  

### **Duration**

- Very brief (1–2 seconds real time)
    
- No player input required
    

  

### **Messaging**

  

Use evocative but restrained text:

- “Cold spreads through your limbs.”
    
- “The world slips away.”
    

  

This reinforces tone without delay.

---

## **Recovery Location**

  

### **Default Rule**

- Player awakens at a **safe anchor location**
    

  

Examples:

- New Cove (Temple of Lumeris)
    
- Last major settlement visited
    

  

This is **not** the exact death location.

---

## **Recovery State**

  

Upon recovery:

- HP restored to **25–40%**
    
- All combat effects cleared
    
- Autoattack disabled
    

  

The player is alive, but vulnerable.

---

## **Death Consequences**

  

### **1) Time Loss (Primary Consequence)**

- A chunk of in-game time passes (e.g., 2–6 hours)
    
- World state continues advancing
    
- Shops may close, NPCs may move
    

  

This makes death _matter_ without touching XP.

---

### **2) Equipment Wear (Secondary)**

- Equipped items lose durability
    
- Heavier armor degrades more
    
- Broken items remain but are ineffective
    

  

This reinforces the repair economy.

---

### **3) Temporary Weakness (Optional, Light)**

  

Optional debuff for a short duration:

- Shaken: −1 to all skill checks for 10 minutes
    

  

This fades naturally and is never permanent.

---

## **What Does NOT Happen on Death**

- ❌ No XP loss
    
- ❌ No level loss
    
- ❌ No permanent stat damage
    
- ❌ No corpse runs required
    

  

The game encourages learning, not punishment.

---

## **Death in Dungeons**

  

### **Inside Dungeons or Dangerous Areas**

- Player awakens in nearest **safe settlement**
    
- Dungeon state persists:
    
    - Defeated enemies remain defeated
        
    - Loot already taken stays gone
        
    - Unfinished encounters may reset later
        
    

  

This prevents death loops while preserving tension.

---

## **Group Combat & Death**

  

### **If One Player Dies**

- Combat continues for others
    
- Dead player is removed from encounter
    

  

### **If Entire Group Dies**

- Group recovers together
    
- Shared time loss applies
    

---

## **Edge Cases**

  

### **Death by Environment (Pits, Drowning)**

- Same rules apply
    
- Death message references the cause
    

  

### **Logging Out While Defeated**

- Player recovers immediately on next login
    
- No additional penalty
    

---

## **NPC & Creature Death**

  

### **NPC / Creature Death**

- Entity removed from room state
    
- Loot rolled once
    
- Respawn timers begin
    

  

No corpse persistence required initially.

---

## **Future Extensions (Not Required Now)**

- Rare resurrection mechanics
    
- Death-related story hooks
    
- Religious or faction-based recovery modifiers
    

---

## **Summary**

  

Death in _Tyrant of the Dark Skies_:

- Resets position
    
- Advances time
    
- Wears gear
    
- Teaches caution
    

  

But never locks players out of progress.

  

This keeps the game challenging, fair, and humane.