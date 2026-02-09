"""
Behavioral AI engine for the Betta fish.
Realistic fish movement with:
  - Smooth turning arcs (fish don't snap-turn)
  - Acceleration/deceleration curves
  - Body inertia and momentum
  - Idle hovering with micro-movements
  - Occasional burst-dart behavior
  - Flaring display when mood drops
  - Gentle sinking when resting
  - Smooth approach and nibble during feeding
  - Natural wandering paths (not straight lines)
"""

import numpy as np
import math
import time
from utils.logger import logger


class BehavioralReactor:
    """The fish's brain: realistic behavior, smooth movement, environmental awareness."""

    STATES = ("IDLE", "SEARCHING", "FEEDING", "RESTING", "COMMUNICATING", "DARTING", "FLARING")

    def __init__(self):
        self.hunger = 0.0
        self.mood = 100.0
        self.position = np.array([100.0, 100.0])
        self.velocity = np.array([0.0, 0.0])
        self.target = np.array([100.0, 100.0])
        self.last_update = time.time()

        self.state = "IDLE"
        self.bounds = [0, 0, 1920, 1080]

        # Smooth facing angle (fish turns gradually)
        self.facing_angle = 0.0
        self.target_angle = 0.0
        self.turn_speed = 2.5  # radians/sec

        # Sanctuary engine reference
        self.sanctuary = None
        # Bubble system reference
        self.bubble_system = None
        # Communication modules
        self.modules = []

        # -- Idle behavior --
        self._idle_timer = 0.0
        self._idle_drift_target = None
        self._hover_offset = np.array([0.0, 0.0])
        self._hover_phase = np.random.uniform(0, math.pi * 2)

        # -- Resting --
        self._rest_timer = 0.0

        # -- Darting (burst speed) --
        self._dart_timer = 0.0
        self._dart_duration = 0.4

        # -- Flaring (display) --
        self._flare_timer = 0.0
        self._flare_duration = 3.0

        # -- Feeding --
        self._feed_nibble_timer = 0.0

        # -- Communication --
        self._comm_timer = 0.0
        self._comm_duration = 2.0
        self._last_module_check = time.time()
        self._module_check_interval = 10.0

        # -- Wandering path (curved, not straight) --
        self._waypoints = []
        self._waypoint_idx = 0

        # -- Speed parameters --
        self._max_speed = 180.0
        self._cruise_speed = 55.0
        self._idle_speed = 20.0
        self._dart_speed = 350.0

        logger.info("Neural Brain (Behavioral Reactor) initialized.")

    def set_bounds(self, x, y, w, h):
        self.bounds = [x, y, w, h]
        logger.info(f"Aquarium bounds set to: {self.bounds}")

    def set_sanctuary(self, sanctuary):
        self.sanctuary = sanctuary

    def set_bubble_system(self, bubble_system):
        self.bubble_system = bubble_system

    def add_module(self, module):
        self.modules.append(module)

    def feed(self):
        self.hunger = max(0.0, self.hunger - 30.0)
        self.mood = min(100.0, self.mood + 20.0)
        self.state = "FEEDING"
        self._feed_nibble_timer = 0.0
        logger.info("Fish fed manually! Hunger decreased, mood boosted.")

    def update(self):
        now = time.time()
        dt = now - self.last_update
        self.last_update = now
        dt = min(dt, 0.1)

        # Passive hunger increase
        self.hunger = min(100.0, self.hunger + 0.3 * dt)

        # Mood dynamics
        if self.hunger > 70:
            self.mood = max(0.0, self.mood - 1.5 * dt)
        elif self.hunger < 30:
            self.mood = min(100.0, self.mood + 0.3 * dt)
        else:
            self.mood = min(100.0, self.mood + 0.1 * dt)

        self._think(dt)
        self._move(dt)
        self._update_facing(dt)
        self._apply_sanctuary_forces(dt)
        self._check_boundaries()
        self._check_modules()

        if self.bubble_system:
            self.bubble_system.update(dt, self.position[0], self.position[1])

    def _think(self, dt):
        """State machine with natural transitions."""
        if self.state == "IDLE":
            self._idle_timer += dt
            self._hover_phase += dt * 1.8

            # Hunger triggers searching
            if self.hunger > 30:
                self.state = "SEARCHING"
                self._generate_wandering_path(self._find_valid_target())
                self._idle_timer = 0.0
                return

            # Occasional behaviors
            if self._idle_timer > 2.5 + np.random.exponential(2.0):
                self._idle_timer = 0.0
                roll = np.random.random()

                if roll < 0.03 and self.mood > 40:
                    # Rare dart burst
                    self.state = "DARTING"
                    self._dart_timer = 0.0
                    dart_dir = np.random.uniform(-1, 1, size=2)
                    dart_dir /= np.linalg.norm(dart_dir) + 1e-6
                    self.target = self.position + dart_dir * np.random.uniform(100, 250)
                    return

                if roll < 0.06 and self.mood < 60:
                    # Flare display when mood is low
                    self.state = "FLARING"
                    self._flare_timer = 0.0
                    return

                if roll < 0.20:
                    # Rest
                    self.state = "RESTING"
                    self._rest_timer = 0.0
                    return

                # Default: gentle drift
                self._find_drift_target()

        elif self.state == "SEARCHING":
            # Follow waypoints for curved path
            if self._waypoint_idx < len(self._waypoints):
                current_wp = self._waypoints[self._waypoint_idx]
                dist = np.linalg.norm(current_wp - self.position)
                if dist < 20:
                    self._waypoint_idx += 1
            else:
                # Reached final destination
                if self.hunger > 20:
                    self.state = "FEEDING"
                    self._feed_nibble_timer = 0.0
                else:
                    self.state = "IDLE"

        elif self.state == "FEEDING":
            self._feed_nibble_timer += dt
            self.hunger = max(0.0, self.hunger - 6.0 * dt)
            if self.hunger <= 0:
                self.state = "IDLE"
                self.mood = min(100.0, self.mood + 10.0)
            elif self._feed_nibble_timer > 4.0:
                # Move to a new nibble spot
                self._feed_nibble_timer = 0.0
                if np.random.random() < 0.4:
                    self._generate_wandering_path(self._find_valid_target())
                    self.state = "SEARCHING"

        elif self.state == "RESTING":
            self._rest_timer += dt
            self.mood = min(100.0, self.mood + 0.5 * dt)
            if self._rest_timer > 4.0 + np.random.exponential(2.0):
                self.state = "IDLE"
                self._idle_timer = 0.0

        elif self.state == "DARTING":
            self._dart_timer += dt
            if self._dart_timer > self._dart_duration:
                self.state = "IDLE"
                self._dart_timer = 0.0

        elif self.state == "FLARING":
            self._flare_timer += dt
            self.velocity *= 0.95  # Nearly stop during flare
            if self._flare_timer > self._flare_duration:
                self.state = "IDLE"
                self._flare_timer = 0.0
                self.mood = min(100.0, self.mood + 5.0)

        elif self.state == "COMMUNICATING":
            self._comm_timer += dt
            if self._comm_timer > self._comm_duration:
                self.state = "IDLE"
                self._comm_timer = 0.0

    def _generate_wandering_path(self, destination):
        """Generate a curved path with 2-3 intermediate waypoints for natural movement."""
        self._waypoints = []
        self._waypoint_idx = 0

        direction = destination - self.position
        dist = np.linalg.norm(direction)

        if dist < 30:
            self._waypoints = [destination]
            return

        # Number of waypoints based on distance
        num_wp = max(1, min(4, int(dist / 150)))

        for i in range(num_wp):
            t = (i + 1) / (num_wp + 1)
            # Point along straight line
            base = self.position + direction * t
            # Add perpendicular offset for curve
            perp = np.array([-direction[1], direction[0]])
            perp_norm = np.linalg.norm(perp)
            if perp_norm > 0:
                perp /= perp_norm
            offset = perp * np.random.uniform(-dist * 0.2, dist * 0.2)
            wp = base + offset
            self._waypoints.append(wp)

        self._waypoints.append(destination)

    def _find_valid_target(self):
        """Pick a random target within bounds, avoiding sanctuary zones."""
        x_min, y_min, w, h = self.bounds
        for _ in range(20):
            tx = np.random.uniform(x_min + 60, x_min + w - 60)
            ty = np.random.uniform(y_min + 60, y_min + h - 60)
            if self.sanctuary and self.sanctuary.is_in_sanctuary(tx, ty):
                continue
            return np.array([tx, ty])
        return self.position + np.random.uniform(-80, 80, size=2)

    def _find_drift_target(self):
        """Gentle nearby drift for idle hovering."""
        offset = np.random.uniform(-150, 150, size=2)
        candidate = self.position + offset
        x_min, y_min, w, h = self.bounds
        candidate[0] = np.clip(candidate[0], x_min + 40, x_min + w - 40)
        candidate[1] = np.clip(candidate[1], y_min + 40, y_min + h - 40)

        if self.sanctuary and self.sanctuary.is_in_sanctuary(candidate[0], candidate[1]):
            candidate = self.position - offset
            candidate[0] = np.clip(candidate[0], x_min + 40, x_min + w - 40)
            candidate[1] = np.clip(candidate[1], y_min + 40, y_min + h - 40)

        self._idle_drift_target = candidate

    def _move(self, dt):
        """Physics-based movement with smooth acceleration and realistic inertia."""
        target_vel = np.array([0.0, 0.0])

        if self.state == "SEARCHING":
            if self._waypoint_idx < len(self._waypoints):
                wp = self._waypoints[self._waypoint_idx]
                direction = wp - self.position
                dist = np.linalg.norm(direction)
                if dist > 1:
                    direction /= dist
                    # Slow down when approaching waypoint
                    approach_speed = min(self._cruise_speed + (self.mood / 100.0) * 80.0,
                                         dist * 2.0)
                    target_vel = direction * approach_speed
            # Smooth acceleration (fish don't start/stop instantly)
            self.velocity = self.velocity * 0.92 + target_vel * 0.08

        elif self.state == "FEEDING":
            # Gentle nibble movements: small random impulses
            nibble_freq = math.sin(self._feed_nibble_timer * 4.0)
            if abs(nibble_freq) > 0.8:
                impulse = np.random.uniform(-8, 8, size=2)
                self.velocity = self.velocity * 0.85 + impulse * 0.15
            else:
                self.velocity *= 0.94

        elif self.state == "RESTING":
            # Slow drift with gentle sine-wave sinking
            self.velocity *= 0.97
            sink_rate = 3.0 * math.sin(self._rest_timer * 0.5) + 2.0
            self.velocity[1] += sink_rate * dt
            # Tiny lateral drift
            self.velocity[0] += math.sin(self._rest_timer * 0.8) * 1.0 * dt

        elif self.state == "DARTING":
            # Burst speed toward target
            direction = self.target - self.position
            dist = np.linalg.norm(direction)
            if dist > 1:
                direction /= dist
                target_vel = direction * self._dart_speed
            # Quick acceleration for dart
            self.velocity = self.velocity * 0.7 + target_vel * 0.3

        elif self.state == "FLARING":
            # Nearly stationary, slight puff-up hover
            self.velocity *= 0.93
            hover_x = math.sin(self._flare_timer * 3.0) * 2.0
            hover_y = math.cos(self._flare_timer * 2.5) * 1.5
            self.velocity += np.array([hover_x, hover_y]) * dt

        elif self.state == "COMMUNICATING":
            self.velocity *= 0.92

        elif self.state == "IDLE":
            if self._idle_drift_target is not None:
                direction = self._idle_drift_target - self.position
                dist = np.linalg.norm(direction)
                if dist > 12:
                    direction /= dist
                    # Very gentle movement
                    drift_speed = self._idle_speed + (self.mood / 100.0) * 25.0
                    # Slow down as we approach
                    drift_speed = min(drift_speed, dist * 0.8)
                    target_vel = direction * drift_speed
                    self.velocity = self.velocity * 0.96 + target_vel * 0.04
                else:
                    self._idle_drift_target = None
                    self.velocity *= 0.97
            else:
                # Micro-hover: gentle figure-8 idle motion
                hover_x = math.sin(self._hover_phase) * 0.8
                hover_y = math.sin(self._hover_phase * 0.7 + 0.5) * 0.5
                self._hover_offset = np.array([hover_x, hover_y])
                self.velocity = self.velocity * 0.97 + self._hover_offset * 0.3

        # Apply velocity
        self.position += self.velocity * dt

        # Global speed cap
        speed = np.linalg.norm(self.velocity)
        if speed > self._max_speed:
            self.velocity = self.velocity / speed * self._max_speed

    def _update_facing(self, dt):
        """Smooth facing angle update - fish turn gradually, not instantly."""
        speed = np.linalg.norm(self.velocity)
        if speed > 2.0:
            self.target_angle = math.atan2(self.velocity[1], self.velocity[0])

        # Smooth angle interpolation (shortest path)
        diff = self.target_angle - self.facing_angle
        # Normalize to [-pi, pi]
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi

        # Turn rate scales with speed (faster = tighter turns)
        effective_turn = self.turn_speed * (0.5 + min(speed / 100.0, 1.5))
        max_turn = effective_turn * dt

        if abs(diff) < max_turn:
            self.facing_angle = self.target_angle
        elif diff > 0:
            self.facing_angle += max_turn
        else:
            self.facing_angle -= max_turn

    def _apply_sanctuary_forces(self, dt):
        if not self.sanctuary:
            return
        fx, fy = self.sanctuary.compute_repulsion(self.position[0], self.position[1])
        if abs(fx) > 0.1 or abs(fy) > 0.1:
            self.velocity[0] += fx * dt
            self.velocity[1] += fy * dt
            speed = np.linalg.norm(self.velocity)
            if speed > 300:
                self.velocity = self.velocity / speed * 300

    def _check_boundaries(self):
        x_min, y_min, w, h = self.bounds
        margin = 30
        bounce_factor = 0.4

        # Soft boundary: gradual repulsion before hitting edge
        soft_margin = 80
        repulsion_strength = 50.0

        px, py = self.position
        # Soft repulsion from edges
        if px < x_min + soft_margin:
            force = (1.0 - (px - x_min) / soft_margin) * repulsion_strength
            self.velocity[0] += force * 0.033
        elif px > x_min + w - soft_margin:
            force = (1.0 - (x_min + w - px) / soft_margin) * repulsion_strength
            self.velocity[0] -= force * 0.033

        if py < y_min + soft_margin:
            force = (1.0 - (py - y_min) / soft_margin) * repulsion_strength
            self.velocity[1] += force * 0.033
        elif py > y_min + h - soft_margin:
            force = (1.0 - (y_min + h - py) / soft_margin) * repulsion_strength
            self.velocity[1] -= force * 0.033

        # Hard boundary clamp
        if px < x_min + margin:
            self.position[0] = x_min + margin
            self.velocity[0] = abs(self.velocity[0]) * bounce_factor
        elif px > x_min + w - margin:
            self.position[0] = x_min + w - margin
            self.velocity[0] = -abs(self.velocity[0]) * bounce_factor

        if py < y_min + margin:
            self.position[1] = y_min + margin
            self.velocity[1] = abs(self.velocity[1]) * bounce_factor
        elif py > y_min + h - margin:
            self.position[1] = y_min + h - margin
            self.velocity[1] = -abs(self.velocity[1]) * bounce_factor

    def _check_modules(self):
        now = time.time()
        if now - self._last_module_check < self._module_check_interval:
            return
        self._last_module_check = now

        if not self.bubble_system or not self.modules:
            return

        for module in self.modules:
            if not hasattr(module, 'check'):
                continue
            try:
                messages = module.check()
                for msg, category in messages:
                    self.bubble_system.queue_message(msg, category)
            except Exception as e:
                logger.warning(f"Module check error: {e}")

    def get_state(self):
        return {
            "position": self.position.tolist(),
            "velocity": self.velocity.tolist(),
            "hunger": self.hunger,
            "mood": self.mood,
            "state": self.state,
            "facing_angle": self.facing_angle,
            "is_flaring": self.state == "FLARING",
        }
