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

    STATES = ("IDLE", "SEARCHING", "FEEDING", "RESTING", "COMMUNICATING", "DARTING", "FLARING", "SURFACE_BREATH")

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
        self._patrol_pause_timer = 0.0
        self._reverse_timer = 0.0
        self._rest_anchor = None

        # -- World exploration cadence (use full multi-monitor world) --
        self._explore_timer = 0.0
        self._explore_interval = np.random.uniform(9.0, 18.0)

        # -- Surface breathing cadence --
        self._surface_breath_interval = np.random.uniform(30.0, 60.0)
        self._surface_breath_elapsed = 0.0
        self._surface_target = None

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
        self._behavior_variety = np.random.uniform(0.85, 1.15)
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
        """Drop pellets from the surface; clicked position defines where to pour them."""
        x_min, y_min, w, h = self.bounds
        pour_x = float(np.clip(x, x_min + 30, x_min + w - 30))
        pour_y = float(np.clip(y, y_min + 35, y_min + h - 28))
        spawn_y = y_min + 8.0
        for _ in range(max(1, int(count))):
            spread_x = float(np.random.uniform(-10.0, 10.0))
            target_depth = float(np.clip(pour_y + np.random.uniform(-18.0, 18.0), y_min + 55.0, y_min + h - 30.0))
            self._pellets.append({
                "pos": np.array([pour_x + spread_x, spawn_y], dtype=float),
                "vy": np.random.uniform(16.0, 22.0),
                "settle_vy": np.random.uniform(3.2, 6.8),
                "target_depth": target_depth,
                "age": 0.0,
                "life_seconds": 120.0,
            })
        self._feed_nibble_timer = 0.0
        self._pellet_last_drop = time.time()
        self.mood = min(100.0, self.mood + 4.0)
        logger.info(f"Symbolic feed: dropped {count} pellet(s) at x={pour_x:.1f}, target y={pour_y:.1f} (surface start).")

    def update(self):
        now = time.time()
        dt = now - self.last_update
        self.last_update = now
        dt = min(dt, 0.1)

        # Symbolic feeding model: hunger is cosmetic and does not drive urgency.
        self.hunger = max(0.0, min(100.0, self.hunger - 0.2 * dt))

        # Calm mood recovery baseline.
        self.mood = min(100.0, self.mood + 0.12 * dt * self._behavior_variety)
        self._surface_breath_elapsed += dt

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
        """Pellets fall from the surface, settle slowly, and linger ~2 minutes."""
        if not self._pellets:
            return

        x_min, y_min, w, h = self.bounds
        max_y = y_min + h - 22
        kept = []
        for pellet in self._pellets:
            pellet["age"] += dt
            sway = math.sin((pellet["age"] * 2.0) + pellet["pos"][0] * 0.03) * 4.0
            pellet["pos"][0] += sway * dt

            target_depth = pellet.get("target_depth", y_min + h * 0.55)
            if pellet["pos"][1] < target_depth:
                pellet["pos"][1] += pellet.get("vy", 18.0) * dt
            else:
                pellet["pos"][1] += pellet.get("settle_vy", 4.5) * dt

            pellet["pos"][0] = float(np.clip(pellet["pos"][0], x_min + 15, x_min + w - 15))
            pellet["pos"][1] = float(min(pellet["pos"][1], max_y))
            if pellet["age"] < pellet.get("life_seconds", 120.0):
                kept.append(pellet)
        self._pellets = kept

    def _think(self, dt):
        """State machine with natural transitions."""
        if self.state == "IDLE":
            self._idle_timer += dt
            self._explore_timer += dt
            self._hover_phase += dt * 1.8

            # Labyrinth breathing: periodic quick rise to surface and gulp.
            if self._surface_breath_elapsed >= self._surface_breath_interval:
                x_min, y_min, w, _ = self.bounds
                sx = float(np.clip(self.position[0] + np.random.uniform(-80, 80), x_min + 40, x_min + w - 40))
                sy = y_min + 35
                self._surface_target = np.array([sx, sy], dtype=float)
                self.state = "SURFACE_BREATH"
                self._surface_breath_elapsed = 0.0
                self._surface_breath_interval = np.random.uniform(30.0, 60.0)
                return

            if self._explore_timer >= self._explore_interval and not self._pellets:
                self._explore_timer = 0.0
                self._explore_interval = np.random.uniform(9.0, 18.0)
                destination = self._find_valid_target()
                self._build_path_to(destination)
                self.state = "SEARCHING"
                return

            # Occasional behaviors
            if self._idle_timer > 2.5 + np.random.exponential(2.0):
                self._idle_timer = 0.0
                roll = np.random.random()

                pellet_excited = 0.15 if self._pellets else 0.0
                dart_chance = (0.02 + pellet_excited * 0.6) * self._behavior_variety
                flare_gate = 62.0 - pellet_excited * 14.0
                rest_chance = (0.16 - pellet_excited * 0.4) / max(self._behavior_variety, 1e-6)

                if roll < dart_chance and self.mood > 35:
                    # Short, elegant pursuit burst when curious/excited.
                    self.state = "DARTING"
                    self._dart_timer = 0.0
                    dart_dir = np.random.uniform(-1, 1, size=2)
                    dart_dir /= np.linalg.norm(dart_dir) + 1e-6
                    self.target = self.position + dart_dir * np.random.uniform(90, 220)
                    return

                if roll < dart_chance + 0.03 and self.mood < flare_gate:
                    # Occasional display flare when confidence drops.
                    self.state = "FLARING"
                    self._flare_timer = 0.0
                    return

                if roll < dart_chance + 0.03 + max(0.06, rest_chance):
                    # Slow rest drift to preserve natural pacing.
                    self.state = "RESTING"
                    self._rest_timer = 0.0
                    self._patrol_pause_timer = np.random.uniform(5.0, 10.0)
                    self._rest_anchor = self.position.copy()
                    return

                if roll < dart_chance + 0.10:
                    # Brief reverse sweep similar to real betta repositioning.
                    self._reverse_timer = np.random.uniform(0.25, 0.65)

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
                self.state = "IDLE"
                self._idle_timer = 0.0
                self._find_drift_target()

        elif self.state == "FEEDING":
            # Legacy compatibility: feeding is now symbolic and non-blocking.
            self.state = "IDLE"

        elif self.state == "RESTING":
            self._rest_timer += dt
            self.mood = min(100.0, self.mood + 0.5 * dt)
            pause_done = self._rest_timer > max(4.0 + np.random.exponential(2.0), self._patrol_pause_timer)
            if pause_done:
                self.state = "IDLE"
                self._idle_timer = 0.0
                self._patrol_pause_timer = 0.0
                self._rest_anchor = None

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

        elif self.state == "SURFACE_BREATH":
            if self._surface_target is None:
                self.state = "IDLE"
            elif np.linalg.norm(self._surface_target - self.position) < 22.0:
                # Short gulp bob at surface
                self._feed_nibble_timer += dt
                self.velocity *= 0.90
                self.velocity[1] += math.sin(self._feed_nibble_timer * 10.0) * 1.4
                if self._feed_nibble_timer > 1.2:
                    self._feed_nibble_timer = 0.0
                    self.state = "IDLE"
                    self.mood = min(100.0, self.mood + 1.0)
            else:
                self._feed_nibble_timer = 0.0

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

    def _apply_pellet_attraction(self, dt):
        """Non-blocking pellet attraction so fish keeps swimming while interacting."""
        if not self._pellets:
            return

        # Prevent lock-in: very old pellets remain visible but no longer strongly attract.
        active_indices = [
            i for i, p in enumerate(self._pellets)
            if p.get("age", 0.0) < min(85.0, p.get("life_seconds", 120.0) * 0.75)
        ]
        if not active_indices:
            return

        self._feed_nibble_timer += dt
        nearest_idx = min(
            active_indices,
            key=lambda i: np.linalg.norm(self._pellets[i]["pos"] - self.position)
        )
        nearest = self._pellets[nearest_idx]
        dist = np.linalg.norm(nearest["pos"] - self.position)

        # Consume when close enough.
        if dist < 16.0:
            self._pellets.pop(nearest_idx)
            self.mood = min(100.0, self.mood + 1.6)
            self.hunger = max(0.0, self.hunger - 3.0)
            return

        # Avoid hard-lock pursuit from too far away while still keeping nibble behavior nearby.
        if dist > 280.0:
            return

        # Apply gentle steering force without overriding current behavior.
        direction = nearest["pos"] - self.position
        if dist > 1e-6:
            direction = direction / dist
            age_ratio = min(1.0, nearest.get("age", 0.0) / max(nearest.get("life_seconds", 120.0), 1e-6))
            attraction_gain = max(0.30, 1.0 - age_ratio * 0.75)
            desired_speed = min(self._max_speed * 0.44, self._idle_speed + 30.0 + dist * 0.15)
            desired = direction * desired_speed
            steering = desired - self.velocity
            sn = np.linalg.norm(steering)
            max_accel = 72.0
            if sn > max_accel:
                steering = steering / sn * max_accel
            self.velocity += steering * dt * (0.55 * attraction_gain)

            # tiny nibble oscillation while approaching pellets + lateral assess zig-zag.
            self.velocity += np.array([0.0, math.sin(self._feed_nibble_timer * 8.0) * 0.35])
            lateral = np.array([-direction[1], direction[0]])
            self.velocity += lateral * (math.sin(self._feed_nibble_timer * 3.0) * 0.45)

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
        self._yaw_damping = min(1.0, np.linalg.norm(steering) / max(max_accel, 1e-6))
        self.velocity *= (1.0 - drag)

    def _move(self, dt):
        """Physics-based movement with smoother steering and graceful arcs."""
        target_vel = np.array([0.0, 0.0])

        if self.state == "SEARCHING":
            if self._waypoint_idx < len(self._waypoints):
                wp = self._waypoints[self._waypoint_idx]
                self._steer_towards(wp, max_accel=120.0, drag=0.045)

        elif self.state == "SURFACE_BREATH":
            if self._surface_target is not None:
                self._steer_towards(self._surface_target, max_accel=95.0, drag=0.035, desired_speed=min(65.0, self._max_speed * 0.55))

        elif self.state == "FEEDING":
            # Backward-compat fallback; feeding no longer blocks swimming flow.
            self.state = "IDLE"
            self.velocity *= 0.96

        elif self.state == "RESTING":
            self.velocity *= 0.965
            if self._rest_anchor is not None:
                anchor_delta = self._rest_anchor - self.position
                dist_anchor = np.linalg.norm(anchor_delta)
                if dist_anchor > 1e-6:
                    anchor_pull = anchor_delta / dist_anchor * min(35.0, dist_anchor * 0.8)
                    self.velocity += anchor_pull * dt
            sink_rate = 1.6 * math.sin(self._rest_timer * 0.5) + 0.8
            self.velocity[1] += sink_rate * dt
            self.velocity[0] += math.sin(self._rest_timer * 0.8) * 0.7 * dt

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

            if self._reverse_timer > 0.0:
                self._reverse_timer = max(0.0, self._reverse_timer - dt)
                facing = np.array([math.cos(self.facing_angle), math.sin(self.facing_angle)])
                self.velocity += -facing * 12.0 * dt

        # Keep pellet response non-blocking across all states.
        self._apply_pellet_attraction(dt)

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
            "swim_cadence": self._swim_cadence,
            "pellets": [p["pos"].tolist() for p in self._pellets],
        }
