"""Game systems package.

This package contains core game systems:
- combat: Combat mechanics
- time: World time system
- quest: Quest management
- character_creation: Character creation flow
"""

try:
    from .combat_system import CombatManager
    from .time_system import WorldTime, NPCScheduler, StoreHours
    from .quest_system import QuestManager
    from . import character_creation
    __all__ = ['CombatManager', 'WorldTime', 'NPCScheduler', 'StoreHours', 'QuestManager', 'character_creation']
except ImportError:
    __all__ = []
