"""Data models package.

This package contains core game data models:
- player: Player class
"""

try:
    from .player import Player
    __all__ = ['Player']
except ImportError:
    __all__ = []
