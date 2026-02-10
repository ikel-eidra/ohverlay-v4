"""
Multi-fish schooling engine using Boids algorithm.
Manages multiple fish with realistic flocking behavior:
  - Separation: don't crowd neighbors
  - Alignment: steer toward average heading
  - Cohesion: steer toward center of mass
  - Realistic turning (NO somersaults - fish turn in arcs only)
  - Species-specific behavior parameters
  - Optimized for 16-32GB RAM (max ~12 fish, O(n^2) checks are fine)
"""

import math
import numpy as np
import time
from utils.logger import logger


class SchoolFish:
    """Individual fish within a school."""

    def __init__(self, fish_id, position, species="neon_tetra"):
        self.fish_id = fish_id
        self.species = species
        self.position = np.array(position, dtype=float)
        self.velocity = np.random.uniform(-20, 20, size=2)

        # Facing angle with smooth interpolation (prevents somersaults)
        self.facing_angle = math.atan2(self.velocity[1], self.velocity[0])
        self._target_angle = self.facing_angle

        # Per-fish variation
        self._speed_mult = 0.85 + np.random.random() * 0.3
        self._phase_offset = np.random.uniform(0, math.pi * 2)

        # State
        self.state = "SCHOOLING"
        self.mood = 80 + np.random.random() * 20
        self.hunger = np.random.random() * 10

    def get_state(self):
        return {
            "position": self.position.tolist(),
            "velocity": self.velocity.tolist(),
            "hunger": self.hunger,
            "mood": self.mood,
            "state": self.state,
            "facing_angle": self.facing_angle,
        }


# Species behavior profiles
SPECIES_PARAMS = {
    "neon_tetra": {
        "max_speed": 100,
        "cruise_speed": 45,
        "separation_radius": 25,
        "alignment_radius": 80,
        "cohesion_radius": 120,
        "separation_weight": 2.5,
        "alignment_weight": 1.2,
        "cohesion_weight": 0.8,
        "turn_speed": 3.0,      # radians/sec - how fast they can turn
        "wander_strength": 8,
        "school_tight": True,   # tetras school tightly
    },
    "discus": {
        "max_speed": 65,
        "cruise_speed": 28,
        "separation_radius": 50,   # discus need more space
        "alignment_radius": 100,
        "cohesion_radius": 160,
        "separation_weight": 3.0,
        "alignment_weight": 0.8,
        "cohesion_weight": 0.6,
        "turn_speed": 2.0,      # discus turn slower (big body)
        "wander_strength": 5,
        "school_tight": False,  # discus are more independent
    },
    "betta": {
        "max_speed": 80,
        "cruise_speed": 35,
        "separation_radius": 80,   # territorial!
        "alignment_radius": 60,
        "cohesion_radius": 100,
        "separation_weight": 5.0,  # strongly territorial
        "alignment_weight": 0.3,
        "cohesion_weight": 0.2,
        "turn_speed": 2.5,
        "wander_strength": 12,
        "school_tight": False,
    },
}


class FishSchool:
    """Manages a school of fish with Boids flocking behavior."""

    def __init__(self, bounds, species="neon_tetra", count=6):
        self.bounds = list(bounds)  # [x, y, w, h]
        self.species = species
        self.params = SPECIES_PARAMS.get(species, SPECIES_PARAMS["neon_tetra"])
        self.fish = []
        self.last_update = time.time()

        # Sanctuary reference
        self.sanctuary = None

        # School roaming target so groups explore the full monitor, not one corner.
        x_min, y_min, w, h = self.bounds
        self._school_target = np.array([x_min + w * 0.5, y_min + h * 0.5], dtype=float)
        self._school_target_changed_at = time.time()
        self._school_target_interval = 8.0

        # Spawn fish
        self._spawn_fish(count)
        logger.info(f"School created: {count} {species}")

    def _spawn_fish(self, count):
        """Spawn fish in a loose cluster."""
        x_min, y_min, w, h = self.bounds
        cx = x_min + w * 0.5
        cy = y_min + h * 0.5

        self.fish = []
        for i in range(count):
            # Spawn in a cluster near center
            px = cx + np.random.uniform(-150, 150)
            py = cy + np.random.uniform(-100, 100)
            px = np.clip(px, x_min + 60, x_min + w - 60)
            py = np.clip(py, y_min + 60, y_min + h - 60)

            fish = SchoolFish(i, [px, py], self.species)
            self.fish.append(fish)

    def set_count(self, count):
        """Change the number of fish."""
        count = max(1, min(12, count))
        current = len(self.fish)

        if count > current:
            # Add more fish near existing school center
            center = self._get_school_center()
            for i in range(count - current):
                px = center[0] + np.random.uniform(-80, 80)
                py = center[1] + np.random.uniform(-60, 60)
                fish = SchoolFish(current + i, [px, py], self.species)
                self.fish.append(fish)
        elif count < current:
            self.fish = self.fish[:count]

    def set_sanctuary(self, sanctuary):
        self.sanctuary = sanctuary

    def _pick_school_target(self):
        """Pick a new roaming target across the full available monitor space."""
        x_min, y_min, w, h = self.bounds
        margin_x = max(80, min(220, w * 0.08))
        margin_y = max(80, min(180, h * 0.10))

        for _ in range(20):
            tx = np.random.uniform(x_min + margin_x, x_min + w - margin_x)
            ty = np.random.uniform(y_min + margin_y, y_min + h - margin_y)
            if self.sanctuary and self.sanctuary.is_in_sanctuary(tx, ty):
                continue
            self._school_target = np.array([tx, ty], dtype=float)
            self._school_target_changed_at = time.time()
            return

        self._school_target = np.array([x_min + w * 0.5, y_min + h * 0.5], dtype=float)
        self._school_target_changed_at = time.time()

    def update(self):
        """Update all fish with Boids flocking."""
        now = time.time()
        dt = now - self.last_update
        self.last_update = now
        dt = min(dt, 0.1)

        if not self.fish:
            return

        params = self.params

        if now - self._school_target_changed_at > self._school_target_interval:
            self._pick_school_target()

        positions = np.array([f.position for f in self.fish])
        velocities = np.array([f.velocity for f in self.fish])
        n = len(self.fish)

        for i, fish in enumerate(self.fish):
            # --- Boids forces ---
            separation = np.array([0.0, 0.0])
            alignment = np.array([0.0, 0.0])
            cohesion = np.array([0.0, 0.0])
            sep_count = 0
            align_count = 0
            coh_count = 0

            for j in range(n):
                if i == j:
                    continue
                diff = positions[j] - fish.position
                dist = np.linalg.norm(diff)

                if dist < 1:
                    continue

                # Separation
                if dist < params["separation_radius"]:
                    separation -= diff / (dist * dist)
                    sep_count += 1

                # Alignment
                if dist < params["alignment_radius"]:
                    alignment += velocities[j]
                    align_count += 1

                # Cohesion
                if dist < params["cohesion_radius"]:
                    cohesion += positions[j]
                    coh_count += 1

            # Normalize and weight
            force = np.array([0.0, 0.0])

            if sep_count > 0:
                force += separation * params["separation_weight"]

            if align_count > 0:
                avg_vel = alignment / align_count
                force += (avg_vel - fish.velocity) * params["alignment_weight"] * 0.1

            if coh_count > 0:
                center = cohesion / coh_count
                toward_center = center - fish.position
                force += toward_center * params["cohesion_weight"] * 0.01

            # Wander force (prevents fish from getting stuck)
            wander_angle = fish._phase_offset + now * 0.5
            wander = np.array([
                math.cos(wander_angle) * params["wander_strength"],
                math.sin(wander_angle * 0.7) * params["wander_strength"] * 0.6
            ])
            force += wander

            # Global roaming target keeps school moving across the whole monitor.
            to_target = self._school_target - fish.position
            d_target = np.linalg.norm(to_target)
            if d_target > 1.0:
                force += (to_target / d_target) * (8.0 if params["school_tight"] else 5.0)
            if d_target < 120:
                # Gradually pick a fresh area once school reaches current target.
                self._school_target_changed_at -= dt * 4.0

            # Boundary avoidance (soft repulsion)
            x_min, y_min, w, h = self.bounds
            margin = 100
            px, py = fish.position

            if px < x_min + margin:
                force[0] += (1.0 - (px - x_min) / margin) * 40
            elif px > x_min + w - margin:
                force[0] -= (1.0 - (x_min + w - px) / margin) * 40

            if py < y_min + margin:
                force[1] += (1.0 - (py - y_min) / margin) * 40
            elif py > y_min + h - margin:
                force[1] -= (1.0 - (y_min + h - py) / margin) * 40

            # Sanctuary avoidance
            if self.sanctuary:
                sx, sy = self.sanctuary.compute_repulsion(px, py)
                force[0] += sx * 0.5
                force[1] += sy * 0.5

            # Apply force to velocity with smooth acceleration
            fish.velocity += force * dt
            fish.velocity *= 0.97  # Drag

            # Speed limits
            speed = np.linalg.norm(fish.velocity)
            max_spd = params["max_speed"] * fish._speed_mult
            if speed > max_spd:
                fish.velocity = fish.velocity / speed * max_spd
            elif speed < 3.0:
                # Minimum speed - fish don't hover still (except betta)
                if fish.velocity[0] == 0 and fish.velocity[1] == 0:
                    fish.velocity = np.random.uniform(-5, 5, size=2)

            # --- REALISTIC TURNING (no somersaults!) ---
            self._update_facing(fish, dt)

            # Apply position
            fish.position += fish.velocity * dt

            # Hard boundary clamp
            fish.position[0] = np.clip(fish.position[0], x_min + 30, x_min + w - 30)
            fish.position[1] = np.clip(fish.position[1], y_min + 30, y_min + h - 30)

    def _update_facing(self, fish, dt):
        """
        Smooth facing angle - fish ONLY turn in arcs, never somersault.
        The key insight: fish always take the SHORTEST angular path to
        their target direction. They never spin 360 degrees.
        """
        speed = np.linalg.norm(fish.velocity)
        if speed > 2.0:
            fish._target_angle = math.atan2(fish.velocity[1], fish.velocity[0])

        # Calculate shortest angular difference
        diff = fish._target_angle - fish.facing_angle

        # Normalize to [-pi, pi] - THIS prevents somersaults
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi

        # Turn rate: faster fish can turn tighter
        turn_speed = self.params["turn_speed"]
        effective_turn = turn_speed * (0.4 + min(speed / 80.0, 1.2))
        max_turn = effective_turn * dt

        if abs(diff) < max_turn:
            fish.facing_angle = fish._target_angle
        elif diff > 0:
            fish.facing_angle += max_turn
        else:
            fish.facing_angle -= max_turn

        # Also steer velocity toward facing direction (fish swim forward)
        # This prevents sideways sliding
        if speed > 5.0:
            facing_dir = np.array([math.cos(fish.facing_angle), math.sin(fish.facing_angle)])
            fish.velocity = fish.velocity * 0.85 + facing_dir * speed * 0.15

    def _get_school_center(self):
        """Get the center of mass of the school."""
        if not self.fish:
            return np.array([self.bounds[0] + self.bounds[2] / 2,
                            self.bounds[1] + self.bounds[3] / 2])
        positions = np.array([f.position for f in self.fish])
        return positions.mean(axis=0)

    def get_all_states(self):
        """Get render state for all fish."""
        return [fish.get_state() for fish in self.fish]
