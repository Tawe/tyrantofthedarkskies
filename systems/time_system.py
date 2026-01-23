"""World time system for tracking in-game time and schedules."""

import time
import threading
from datetime import datetime

class WorldTime:
    """Manages the global in-game clock.
    
    Time ratio: 1 real second = 3 in-game seconds
    This means 1 real day = 3 in-game days (1 in-game day = 8 real hours)
    """
    
    TIME_RATIO = 3  # 1 real second = 3 in-game seconds
    
    def __init__(self, start_epoch=None):
        """Initialize world time.
        
        Args:
            start_epoch: Starting world_seconds value (defaults to 0 or server start)
        """
        self.start_real_time = time.time()
        self.start_world_seconds = start_epoch if start_epoch is not None else 0
        self.lock = threading.Lock()
    
    def get_world_seconds(self):
        """Get current world time in seconds since epoch."""
        with self.lock:
            real_elapsed = time.time() - self.start_real_time
            world_elapsed = int(real_elapsed * self.TIME_RATIO)
            return self.start_world_seconds + world_elapsed
    
    def set_world_seconds(self, world_seconds):
        """Set world time to a specific value (admin function)."""
        with self.lock:
            self.start_world_seconds = world_seconds
            self.start_real_time = time.time()
    
    def get_day_number(self):
        """Get current day number (days since epoch)."""
        world_seconds = self.get_world_seconds()
        return world_seconds // 86400  # 86400 seconds per day
    
    def get_hour(self):
        """Get current hour (0-23)."""
        world_seconds = self.get_world_seconds()
        return (world_seconds % 86400) // 3600
    
    def get_minute(self):
        """Get current minute (0-59)."""
        world_seconds = self.get_world_seconds()
        return (world_seconds % 3600) // 60
    
    def get_second(self):
        """Get current second (0-59)."""
        world_seconds = self.get_world_seconds()
        return world_seconds % 60
    
    def get_day_part(self):
        """Get current day part (Dawn, Morning, Afternoon, Dusk, Night)."""
        hour = self.get_hour()
        if 5 <= hour < 8:
            return "Dawn"
        elif 8 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 20:
            return "Dusk"
        else:  # 20:00-04:59
            return "Night"
    
    def get_time_string(self, include_exact=False):
        """Get formatted time string for display.
        
        Args:
            include_exact: If True, include exact time (HH:MM) in parentheses
        
        Returns:
            Formatted time string like "It is Morning, 2 bells past sunrise."
        """
        day_part = self.get_day_part()
        hour = self.get_hour()
        minute = self.get_minute()
        day_number = self.get_day_number()
        
        # Create friendly time description
        if day_part == "Dawn":
            bells = hour - 5
            if bells == 0:
                time_desc = "sunrise"
            else:
                time_desc = f"{bells} bell{'s' if bells > 1 else ''} past sunrise"
        elif day_part == "Morning":
            bells = hour - 8
            if bells == 0:
                time_desc = "early morning"
            else:
                time_desc = f"{bells} bell{'s' if bells > 1 else ''} past dawn"
        elif day_part == "Afternoon":
            bells = hour - 12
            if bells == 0:
                time_desc = "midday"
            else:
                time_desc = f"{bells} bell{'s' if bells > 1 else ''} past noon"
        elif day_part == "Dusk":
            bells = hour - 17
            if bells == 0:
                time_desc = "sunset"
            else:
                time_desc = f"{bells} bell{'s' if bells > 1 else ''} past sunset"
        else:  # Night
            if hour >= 20:
                bells = hour - 20
            else:
                bells = hour + 4  # 0-4 hours past midnight
            if bells == 0:
                time_desc = "deep night"
            else:
                time_desc = f"{bells} bell{'s' if bells > 1 else ''} into the night"
        
        result = f"It is {day_part}, {time_desc}."
        
        # Add day number
        result += f" (Day {day_number})"
        
        # Add exact time if requested
        if include_exact:
            result += f" ({hour:02d}:{minute:02d})"
        
        # Add flavor text based on day part
        flavor = {
            "Dawn": "The sky lightens in the east.",
            "Morning": "The town stirs to life.",
            "Afternoon": "The day is in full swing.",
            "Dusk": "Shadows lengthen as daylight fades.",
            "Night": "The docks are lit by lanterns."
        }
        result += f"\n{flavor.get(day_part, '')}"
        
        return result
    
    def parse_time(self, time_string):
        """Parse a time string (HH:MM) into minutes since midnight.
        
        Args:
            time_string: Time in format "HH:MM" or "H:MM"
        
        Returns:
            Minutes since midnight (0-1439), or None if invalid
        """
        try:
            parts = time_string.split(":")
            if len(parts) != 2:
                return None
            hour = int(parts[0])
            minute = int(parts[1])
            if 0 <= hour < 24 and 0 <= minute < 60:
                return hour * 60 + minute
        except (ValueError, AttributeError):
            pass
        return None
    
    def is_time_in_range(self, start_time, end_time):
        """Check if current time is within a time range.
        
        Args:
            start_time: Start time string (HH:MM) or minutes since midnight
            end_time: End time string (HH:MM) or minutes since midnight
        
        Returns:
            True if current time is in range (handles wraparound for overnight ranges)
        """
        current_minutes = self.get_hour() * 60 + self.get_minute()
        
        # Parse if strings
        if isinstance(start_time, str):
            start_minutes = self.parse_time(start_time)
            if start_minutes is None:
                return False
        else:
            start_minutes = start_time
        
        if isinstance(end_time, str):
            end_minutes = self.parse_time(end_time)
            if end_minutes is None:
                return False
        else:
            end_minutes = end_time
        
        # Handle wraparound (e.g., 22:00 to 06:00)
        if start_minutes > end_minutes:
            # Overnight range
            return current_minutes >= start_minutes or current_minutes < end_minutes
        else:
            # Same-day range
            return start_minutes <= current_minutes < end_minutes


class NPCScheduler:
    """Manages NPC schedules and lazy presence resolution."""
    
    def __init__(self, world_time):
        """Initialize NPC scheduler.
        
        Args:
            world_time: WorldTime instance
        """
        self.world_time = world_time
        self.npc_schedules = {}  # {npc_id: [{"start": "HH:MM", "end": "HH:MM", "room_id": "..."}, ...]}
        self.room_npc_index = {}  # {room_id: set(npc_ids)} - NPCs that could be in this room
        self.deferred_changes = {}  # {npc_id: {"deferred": True, "reason": "..."}}
    
    def add_npc_schedule(self, npc_id, schedule_blocks):
        """Add schedule for an NPC.
        
        Args:
            npc_id: NPC identifier
            schedule_blocks: List of dicts with "start", "end", "room_id" keys
                Example: [{"start": "08:00", "end": "18:00", "room_id": "shop"}]
        """
        self.npc_schedules[npc_id] = schedule_blocks
        
        # Update room index
        for block in schedule_blocks:
            room_id = block.get("room_id")
            if room_id:
                if room_id not in self.room_npc_index:
                    self.room_npc_index[room_id] = set()
                self.room_npc_index[room_id].add(npc_id)
    
    def get_present_npcs(self, room_id, npc_check_func=None):
        """Get list of NPC IDs that should be present in a room at current time.
        
        Args:
            room_id: Room identifier
            npc_check_func: Optional function to check if NPC can change schedule
                Function signature: (npc_id) -> bool
                Returns True if NPC can change schedule, False if deferred
        
        Returns:
            List of NPC IDs that are scheduled to be in this room
        """
        present = []
        
        # Check all NPCs that could be in this room
        candidate_npcs = self.room_npc_index.get(room_id, set())
        
        for npc_id in candidate_npcs:
            # Skip if change is deferred
            if npc_id in self.deferred_changes:
                continue
            
            # Check if NPC is in a state that prevents schedule changes
            if npc_check_func and not npc_check_func(npc_id):
                # Defer the change
                self.defer_schedule_change(npc_id, "busy")
                continue
            
            schedule = self.npc_schedules.get(npc_id, [])
            for block in schedule:
                if block.get("room_id") == room_id:
                    start = block.get("start")
                    end = block.get("end")
                    if self.world_time.is_time_in_range(start, end):
                        present.append(npc_id)
                        break  # NPC can only be in one place at a time
        
        return present
    
    def defer_schedule_change(self, npc_id, reason):
        """Defer an NPC's schedule change (e.g., if in combat or mid-transaction).
        
        Args:
            npc_id: NPC identifier
            reason: Reason for deferral (e.g., "combat", "transaction", "dialogue")
        """
        self.deferred_changes[npc_id] = {
            "deferred": True,
            "reason": reason
        }
    
    def clear_deferral(self, npc_id):
        """Clear a deferred schedule change for an NPC.
        
        Args:
            npc_id: NPC identifier
        """
        if npc_id in self.deferred_changes:
            del self.deferred_changes[npc_id]
    
    def is_deferred(self, npc_id):
        """Check if an NPC has a deferred schedule change.
        
        Args:
            npc_id: NPC identifier
        
        Returns:
            True if deferred
        """
        return npc_id in self.deferred_changes


class StoreHours:
    """Manages store open/close hours."""
    
    def __init__(self, world_time):
        """Initialize store hours manager.
        
        Args:
            world_time: WorldTime instance
        """
        self.world_time = world_time
        self.store_hours = {}  # {store_id: {"open_time": "HH:MM", "close_time": "HH:MM", "closed_days": [], "festival_days": []}}
    
    def set_store_hours(self, store_id, open_time, close_time, closed_days=None, festival_days=None):
        """Set hours for a store.
        
        Args:
            store_id: Store identifier (usually room_id or NPC_id)
            open_time: Opening time (HH:MM)
            close_time: Closing time (HH:MM)
            closed_days: List of day numbers when closed (optional)
            festival_days: List of day numbers when open extra hours (optional)
        """
        self.store_hours[store_id] = {
            "open_time": open_time,
            "close_time": close_time,
            "closed_days": closed_days or [],
            "festival_days": festival_days or []
        }
    
    def is_store_open(self, store_id):
        """Check if a store is currently open.
        
        Args:
            store_id: Store identifier
        
        Returns:
            True if store is open
        """
        hours = self.store_hours.get(store_id)
        if not hours:
            return True  # Default to open if no hours set
        
        # Check if today is a closed day
        day_number = self.world_time.get_day_number()
        if day_number in hours.get("closed_days", []):
            return False
        
        # Check if within open hours
        open_time = hours.get("open_time", "08:00")
        close_time = hours.get("close_time", "18:00")
        
        return self.world_time.is_time_in_range(open_time, close_time)
    
    def get_store_status(self, store_id):
        """Get status message for a store.
        
        Args:
            store_id: Store identifier
        
        Returns:
            Status string like "Open" or "Closed (opens at 08:00)"
        """
        if self.is_store_open(store_id):
            return "Open"
        
        hours = self.store_hours.get(store_id, {})
        open_time = hours.get("open_time", "08:00")
        return f"Closed (opens at {open_time})"
