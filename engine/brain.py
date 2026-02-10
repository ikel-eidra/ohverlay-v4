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

    def __init__(self, config=None):
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
        self._pellets = []
        self._pellet_last_drop = 0.0

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
        # Motion profile (prototype keeps current behavior, realistic_v2 tightens
        # turn limits and uses stronger thrust-to-fin coupling for lifelike motion).
        self.motion_profile = "realistic_v2"
        self._thrust_factor = 0.0
        self._tail_amp_factor = 1.0
        self._tail_freq_factor = 1.0
        self._turn_intensity = 0.0
        self._swim_cadence = 0.0
        self._yaw_damping = 0.0
        self._load_motion_profile(config)

        logger.info("Neural Brain (Behavioral Reactor) initialized.")

    def _load_motion_profile(self, config):
        if not config:
            return
        fish_cfg = config.get("fish") if hasattr(config, "get") and callable(config.get) else {}
        if isinstance(fish_cfg, dict):
            requested = fish_cfg.get("motion_profile", "realistic_v2")
            self.set_motion_profile(requested)

    def set_motion_profile(self, profile):
        profile = (profile or "realistic_v2").lower()
        if profile not in {"prototype", "realistic_v2"}:
            profile = "prototype"
        self.motion_profile = profile

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
        """Backward-compatible symbolic feed action near current position."""
        jitter = np.random.uniform(-45.0, 45.0, size=2)
        drop_pos = self.position + jitter
        self.drop_pellet(float(drop_pos[0]), float(drop_pos[1]), count=3)

    def drop_pellet(self, x, y, count=3):
        """Drop visible pellets. Fish will swim to the drop point and nibble naturally."""
        x_min, y_min, w, h = self.bounds
        px = float(np.clip(x, x_min + 30, x_min + w - 30))
        py = float(np.clip(y, y_min + 30, y_min + h - 30))
        for _ in range(max(1, int(count))):
            spread = np.random.uniform(-12.0, 12.0, size=2)
            self._pellets.append({
                "pos": np.array([px, py]) + spread,
                "vy": np.random.uniform(18.0, 34.0),
                "age": 0.0,
            })
        self.state = "FEEDING"
        self._feed_nibble_timer = 0.0
        self._pellet_last_drop = time.time()
        self.mood = min(100.0, self.mood + 4.0)
        logger.info(f"Symbolic feed: dropped {count} pellet(s) at ({px:.1f}, {py:.1f}).")

    def update(self):
        now = time.time()
        dt = now - self.last_update
        self.last_update = now
        dt = min(dt, 0.1)

        # Symbolic feeding model: hunger is cosmetic and does not drive urgency.
        self.hunger = max(0.0, min(100.0, self.hunger - 0.2 * dt))

        # Calm mood recovery baseline.
        self.mood = min(100.0, self.mood + 0.12 * dt)

        self._update_pellets(dt)

        self._think(dt)
        self._move(dt)
        self._update_facing(dt)
        self._apply_sanctuary_forces(dt)
        self._check_boundaries()
        self._check_modules()

        if self.bubble_system:
            self.bubble_system.update(dt, self.position[0], self.position[1])

    def _update_pellets(self, dt):
        """Pellets sink with slight drift and expire gracefully."""
        if not self._pellets:
            return

        x_min, y_min, w, h = self.bounds
        kept = []
        for pellet in self._pellets:
            pellet["age"] += dt
            sway = math.sin((pellet["age"] * 2.3) + pellet["pos"][0] * 0.03) * 5.5
            pellet["pos"][0] += sway * dt
            pellet["pos"][1] += pellet["vy"] * dt

            # settle near bottom and expire after a short idle time
            max_y = y_min + h - 22
            pellet["pos"][0] = float(np.clip(pellet["pos"][0], x_min + 15, x_min + w - 15))
            pellet["pos"][1] = float(min(pellet["pos"][1], max_y))
            if pellet["age"] < 9.0:
                kept.append(pellet)
        self._pellets = kept

    def _think(self, dt):
        """State machine with natural transitions."""
        if self.state == "IDLE":
            self._idle_timer += dt
            self._hover_phase += dt * 1.8

            # Pellets trigger focused feeding search.
            if self._pellets:
                self.state = "FEEDING"
                self._feed_nibble_timer = 0.0
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
            if self._pellets:
                self.state = "FEEDING"
                self._feed_nibble_timer = 0.0
                return
            # Follow waypoints for curved path
            if self._waypoint_idx < len(self._waypoints):
                current_wp = self._waypoints[self._waypoint_idx]
                dist = np.linalg.norm(current_wp - self.position)
                if dist < 20:
                    self._waypoint_idx += 1
            else:
                self.state = "IDLE"

        elif self.state == "FEEDING":
            self._feed_nibble_timer += dt
            if not self._pellets:
                self.state = "IDLE"
                self._feed_nibble_timer = 0.0
                return

            nearest_idx = min(
                range(len(self._pellets)),
                key=lambda i: np.linalg.norm(self._pellets[i]["pos"] - self.position)
            )
            nearest = self._pellets[nearest_idx]
            if np.linalg.norm(nearest["pos"] - self.position) < 18.0:
                self._pellets.pop(nearest_idx)
                self.mood = min(100.0, self.mood + 1.6)
                self.hunger = max(0.0, self.hunger - 3.0)

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

    def _steer_towards(self, target, max_accel=130.0, drag=0.06, desired_speed=None):
        direction = target - self.position
        dist = np.linalg.norm(direction)
        if dist < 1e-6:
            self.velocity *= (1.0 - drag)
            return

        direction /= dist
        if desired_speed is None:
            desired_speed = min(self._cruise_speed + dist * 0.35, self._max_speed)
        desired = direction * desired_speed
        steering = desired - self.velocity
        steer_norm = np.linalg.norm(steering)
        if steer_norm > max_accel:
            steering = steering / steer_norm * max_accel

        self.velocity += steering * 0.033
        self.velocity *= (1.0 - drag)

    def _move(self, dt):
        """Physics-based movement with smoother steering and graceful arcs."""
        target_vel = np.array([0.0, 0.0])

        if self.state == "SEARCHING":
            if self._waypoint_idx < len(self._waypoints):
                wp = self._waypoints[self._waypoint_idx]
                self._steer_towards(wp, max_accel=120.0, drag=0.045)

        elif self.state == "FEEDING":
            if self._pellets:
                nearest = min(self._pellets, key=lambda p: np.linalg.norm(p["pos"] - self.position))
                desired = min(self._max_speed * 0.55, 75.0 + np.linalg.norm(nearest["pos"] - self.position) * 0.25)
                self._steer_towards(nearest["pos"], max_accel=145.0, drag=0.07, desired_speed=desired)
                nibble_freq = math.sin(self._feed_nibble_timer * 7.0)
                self.velocity += np.array([0.0, nibble_freq * 1.0])
            else:
                self.velocity *= 0.92

        elif self.state == "RESTING":
            self.velocity *= 0.97
            sink_rate = 3.0 * math.sin(self._rest_timer * 0.5) + 2.0
            self.velocity[1] += sink_rate * dt
            self.velocity[0] += math.sin(self._rest_timer * 0.8) * 1.0 * dt

        elif self.state == "DARTING":
            self._steer_towards(self.target, max_accel=220.0, drag=0.015, desired_speed=self._dart_speed)

        elif self.state == "FLARING":
            self.velocity *= 0.93
            hover_x = math.sin(self._flare_timer * 3.0) * 2.0
            hover_y = math.cos(self._flare_timer * 2.5) * 1.5
            self.velocity += np.array([hover_x, hover_y]) * dt

        elif self.state == "COMMUNICATING":
            self.velocity *= 0.90

        else:  # IDLE
            if self._idle_drift_target is not None:
                direction = self._idle_drift_target - self.position
                dist = np.linalg.norm(direction)
                if dist < 12:
                    self._idle_drift_target = None
                else:
                    self._steer_towards(self._idle_drift_target, max_accel=70.0, drag=0.11, desired_speed=self._idle_speed)
            else:
                hover_x = math.sin(self._hover_phase) * 0.6
                hover_y = math.sin(self._hover_phase * 0.7 + 0.5) * 0.5
                self._hover_offset = np.array([hover_x, hover_y])
                self.velocity = self.velocity * 0.97 + self._hover_offset * 0.3

        self.position += self.velocity * dt

        speed = np.linalg.norm(self.velocity)
        if speed > self._max_speed:
            self.velocity = self.velocity / speed * self._max_speed
            speed = self._max_speed

        speed_norm = min(speed / max(self._max_speed, 1e-6), 1.0)
        accel_mag = min(np.linalg.norm(target_vel - self.velocity) / max(self._max_speed, 1e-6), 1.0)
        self._swim_cadence = self._swim_cadence * 0.9 + speed_norm * 0.1
        thrust_base = 0.5 * speed_norm + 0.35 * accel_mag + 0.15 * self._swim_cadence
        if self.motion_profile == "realistic_v2":
            self._thrust_factor = min(1.0, thrust_base * 1.24)
            self._tail_amp_factor = 0.78 + self._thrust_factor * 1.05
            self._tail_freq_factor = 0.82 + self._thrust_factor * 1.0 + self._yaw_damping * 0.08
        else:
            self._thrust_factor = thrust_base
            self._tail_amp_factor = 0.9 + self._thrust_factor * 0.6
            self._tail_freq_factor = 0.9 + self._thrust_factor * 0.5

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

        # Turn-rate model (realistic_v2: tighter at slow speed, wider at high speed).
        if self.motion_profile == "realistic_v2":
            speed_ratio = min(speed / max(self._max_speed, 1e-6), 1.0)
            # Slow fish can pivot more, high-speed fish turn wider and slower.
            effective_turn = self.turn_speed * (1.30 - 0.68 * speed_ratio) * (0.92 + self._yaw_damping * 0.22)
        else:
            # Prototype behavior preserved.
            effective_turn = self.turn_speed * (0.5 + min(speed / 100.0, 1.5))

        effective_turn = max(0.35, effective_turn)
        max_turn = effective_turn * dt

        if abs(diff) < max_turn:
            self.facing_angle = self.target_angle
        elif diff > 0:
            self.facing_angle += max_turn
        else:
            self.facing_angle -= max_turn

        # Renderer hint: normalized turn intensity for fin/body reactions.
        self._turn_intensity = min(abs(diff) / math.pi, 1.0)

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
            "motion_profile": self.motion_profile,
            "thrust_factor": self._thrust_factor,
            "tail_amp_factor": self._tail_amp_factor,
            "tail_freq_factor": self._tail_freq_factor,
            "turn_intensity": self._turn_intensity,
            "pellets": [p["pos"].tolist() for p in self._pellets],
        }
