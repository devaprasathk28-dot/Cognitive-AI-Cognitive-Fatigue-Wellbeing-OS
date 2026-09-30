"""
GLOBAL ANIMATION LOCK
Single source of truth for disabling ALL animations project-wide.
"""

_ACTIVE_ANIMATION = False

def set_animation_lock(enabled: bool):
    """
    Toggle global animation lock.
    enabled=True: animations ON
    enabled=False: ALL animations skipped instantly
    """
    global _ACTIVE_ANIMATION
    _ACTIVE_ANIMATION = enabled

def animations_enabled() -> bool:
    """Check if animations are globally allowed."""
    return _ACTIVE_ANIMATION
