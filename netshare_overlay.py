"""
NetShare Overlay — thin module kept for architecture compatibility.

Visual notifications are now handled by NetShareCardManager (netshare_card.py),
which spawns individual glowing post-it cards per notification.

This module is imported by netshare_main.py but does minimal work —
it re-exports NetShareCardManager as the primary notification surface.
"""

from netshare_card import NetShareCardManager  # noqa: F401 — re-export for main

__all__ = ["NetShareCardManager"]
