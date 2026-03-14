"""
OVL - The Ohverlay Language
============================
A domain-specific language for defining desktop overlays.

Just as CSS styles web pages, OVL defines overlays.
Just as HTML structures content, OVL structures animations.

Example:
  ─────────────────────────────────
  @overlay "Neon Jellyfish"
    type: ambient
    size: 800 x 600

    @creature jellyfish
      style: wireframe
      glow: cyan 0.8
      count: 3
      movement: float, drift
      speed: slow

    @particles bubbles
      count: 50
      color: cyan
      opacity: 0.3
      rise: true

    @behavior
      on idle: drift slowly
      on stressed: pulse gently
      on break: flare display
  ─────────────────────────────────

The OVL compiler converts .ovl files into:
  - Standalone HTML5 Canvas overlays
  - PySide6 widget overlays
  - Factory-deployable overlay packages

File extension: .ovl
MIME type: text/x-ovl
"""

OVL_VERSION = "1.0.0"
OVL_FILE_EXTENSION = ".ovl"
