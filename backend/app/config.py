"""
Backward-compatibility bridge for app.config.
Points to app.core.config.
"""
from app.core.config import settings, Settings

__all__ = ["settings", "Settings"]
