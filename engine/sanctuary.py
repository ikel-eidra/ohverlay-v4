"""
Sanctuary Zone (Invisible Boundary) Engine.
Defines no-swim zones where the fish is repelled via force fields.
Users can designate monitors or rectangular regions as sanctuary zones.
"""

import numpy as np
from utils.logger import logger


class SanctuaryZone:
    """A rectangular region the fish cannot enter."""

    def __init__(self, x, y, w, h, label=""):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = label

    def contains(self, px, py):
        return (self.x <= px <= self.x + self.w and
                self.y <= py <= self.y + self.h)

    def to_dict(self):
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h, "label": self.label}

    @staticmethod
    def from_dict(d):
        return SanctuaryZone(d["x"], d["y"], d["w"], d["h"], d.get("label", ""))


class SanctuaryEngine:
    """Manages sanctuary zones and computes repulsion forces."""

    def __init__(self, config=None):
        self.enabled = False
        self.zones = []
        self.repulsion_strength = 200.0
        self.repulsion_margin = 80  # pixels outside the zone where repulsion begins
        self._load_config(config)

    def _load_config(self, config):
        if not config:
            return
        scfg = config.get("sanctuary") if hasattr(config, "get") and callable(config.get) else {}
        if not isinstance(scfg, dict):
            return
        self.enabled = scfg.get("enabled", self.enabled)
        self.repulsion_strength = scfg.get("repulsion_strength", self.repulsion_strength)
        self.repulsion_margin = scfg.get("repulsion_margin", self.repulsion_margin)
        for zd in scfg.get("zones", []):
            self.zones.append(SanctuaryZone.from_dict(zd))
        logger.info(f"Sanctuary engine: enabled={self.enabled}, zones={len(self.zones)}")

    def toggle(self):
        """Toggle sanctuary mode on/off."""
        self.enabled = not self.enabled
        logger.info(f"Sanctuary mode {'ON' if self.enabled else 'OFF'}")
        return self.enabled

    def add_zone(self, x, y, w, h, label=""):
        """Add a new sanctuary zone."""
        zone = SanctuaryZone(x, y, w, h, label)
        self.zones.append(zone)
        logger.info(f"Sanctuary zone added: {label} ({x},{y} {w}x{h})")
        return zone

    def add_monitor_zone(self, geometry, label=""):
        """Add a full monitor as a sanctuary zone from a QRect geometry."""
        return self.add_zone(geometry.x(), geometry.y(),
                             geometry.width(), geometry.height(), label)

    def remove_zone(self, index):
        """Remove a sanctuary zone by index."""
        if 0 <= index < len(self.zones):
            removed = self.zones.pop(index)
            logger.info(f"Sanctuary zone removed: {removed.label}")

    def clear_zones(self):
        """Remove all sanctuary zones."""
        self.zones.clear()
        logger.info("All sanctuary zones cleared.")

    def compute_repulsion(self, pos_x, pos_y):
        """
        Compute repulsion force vector for a given position.
        Returns (fx, fy) force vector pushing fish away from sanctuary zones.
        """
        if not self.enabled or not self.zones:
            return 0.0, 0.0

        total_fx = 0.0
        total_fy = 0.0
        margin = self.repulsion_margin

        for zone in self.zones:
            # Expanded zone including margin
            ex = zone.x - margin
            ey = zone.y - margin
            ew = zone.w + 2 * margin
            eh = zone.h + 2 * margin

            # Check if fish is within the expanded zone
            if not (ex <= pos_x <= ex + ew and ey <= pos_y <= ey + eh):
                continue

            # Compute closest point on zone boundary
            cx = max(zone.x, min(pos_x, zone.x + zone.w))
            cy = max(zone.y, min(pos_y, zone.y + zone.h))

            # Distance from fish to closest boundary point
            dx = pos_x - cx
            dy = pos_y - cy
            dist = max(1.0, np.sqrt(dx * dx + dy * dy))

            # If inside the zone itself, push out strongly
            if zone.contains(pos_x, pos_y):
                # Find nearest edge and push toward it
                dists_to_edges = [
                    (pos_x - zone.x, -1, 0),       # left edge
                    (zone.x + zone.w - pos_x, 1, 0),  # right edge
                    (pos_y - zone.y, 0, -1),         # top edge
                    (zone.y + zone.h - pos_y, 0, 1),  # bottom edge
                ]
                min_edge = min(dists_to_edges, key=lambda e: e[0])
                force = self.repulsion_strength * 3.0
                total_fx += min_edge[1] * force
                total_fy += min_edge[2] * force
            else:
                # In margin zone: gentle repulsion that increases as fish approaches
                penetration = max(0.0, margin - dist) / margin
                force = self.repulsion_strength * penetration * penetration
                if dist > 0:
                    total_fx += (dx / dist) * force
                    total_fy += (dy / dist) * force

        return total_fx, total_fy

    def is_in_sanctuary(self, pos_x, pos_y):
        """Check if a position is inside any sanctuary zone."""
        if not self.enabled:
            return False
        return any(zone.contains(pos_x, pos_y) for zone in self.zones)

    def get_zones_as_dicts(self):
        """Serialize zones for config persistence."""
        return [z.to_dict() for z in self.zones]
