"""
Behavioral AI engine for the Betta fish.
Manages state machine, movement, hunger/mood, sanctuary awareness,
and triggers for the bubble communication system.
"""

import numpy as np
import time
from utils.logger import logger


class BehavioralReactor:
    """The fish's brain: handles state, movement, and environmental awareness."""

    STATES = ("IDLE", "SEARCHING", "FEEDING", "RESTING", "COMMUNICATING")

    def __init__(self):
        self.hunger = 0.0       # 0 to 100
        self.mood = 100.0       # 0 to 100
        self.position = np.array([100.0, 100.0])  # Global coordinates
        self.velocity = np.array([0.0, 0.0])
        self.target = np.array([100.0, 100.0])
        self.last_update = time.time()

        self.state = "IDLE"
        self.bounds = [0, 0, 1920, 1080]

        # Sanctuary engine reference (set externally)
        self.sanctuary = None

        # Bubble system reference (set externally)
        self.bubble_system = None

        # Communication modules (set externally)
        self.modules = []

        # Idle drift behavior
        self._idle_timer = 0.0
        self._idle_drift_target = None
        self._rest_timer = 0.0

        # Communication state
        self._comm_timer = 0.0
        self._comm_duration = 2.0  # Pause for bubble delivery
        self._last_module_check = time.time()
        self._module_check_interval = 10.0  # Check modules every 10s

        logger.info("Neural Brain (Behavioral Reactor) initialized.")

    def set_bounds(self, x, y, w, h):
        self.bounds = [x, y, w, h]
        logger.info(f"Aquarium bounds set to: {self.bounds}")

    def set_sanctuary(self, sanctuary):
        """Attach the sanctuary engine for boundary awareness."""
        self.sanctuary = sanctuary

    def set_bubble_system(self, bubble_system):
        """Attach the bubble system for communication."""
        self.bubble_system = bubble_system

    def add_module(self, module):
        """Register a communication module (health, love notes, etc.)."""
        self.modules.append(module)

    def feed(self):
        """Manually feed the fish (reduces hunger, boosts mood)."""
        self.hunger = max(0.0, self.hunger - 30.0)
        self.mood = min(100.0, self.mood + 20.0)
        self.state = "FEEDING"
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
        self._apply_sanctuary_forces(dt)
        self._check_boundaries()
        self._check_modules()

        # Update bubble system
        if self.bubble_system:
            self.bubble_system.update(dt, self.position[0], self.position[1])

    def _think(self, dt):
        """State machine logic."""
        if self.state == "IDLE":
            self._idle_timer += dt

            # Hunger triggers search
            if self.hunger > 30:
                self.state = "SEARCHING"
                self._find_new_target()
                self._idle_timer = 0.0
                return

            # Occasional drift for lifelike behavior
            if self._idle_timer > 3.0:
                self._idle_timer = 0.0
                if np.random.random() < 0.4:
                    self._find_drift_target()
                elif np.random.random() < 0.15:
                    self.state = "RESTING"
                    self._rest_timer = 0.0

        elif self.state == "SEARCHING":
            dist = np.linalg.norm(self.target - self.position)
            if dist < 15:
                if self.hunger > 20:
                    self.state = "FEEDING"
                else:
                    self.state = "IDLE"

        elif self.state == "FEEDING":
            self.hunger = max(0.0, self.hunger - 8.0 * dt)
            if self.hunger <= 0:
                self.state = "IDLE"
                self.mood = min(100.0, self.mood + 10.0)
            elif np.random.random() < 0.03:
                self._find_new_target()
                self.state = "SEARCHING"

        elif self.state == "RESTING":
            self._rest_timer += dt
            self.mood = min(100.0, self.mood + 0.5 * dt)
            if self._rest_timer > 5.0:
                self.state = "IDLE"
                self._idle_timer = 0.0

        elif self.state == "COMMUNICATING":
            self._comm_timer += dt
            if self._comm_timer > self._comm_duration:
                self.state = "IDLE"
                self._comm_timer = 0.0

    def _find_new_target(self):
        """Pick a random target within bounds, avoiding sanctuary zones."""
        x_min, y_min, w, h = self.bounds
        for _ in range(20):  # Try up to 20 times to find a valid target
            tx = np.random.uniform(x_min + 50, x_min + w - 50)
            ty = np.random.uniform(y_min + 50, y_min + h - 50)
            if self.sanctuary and self.sanctuary.is_in_sanctuary(tx, ty):
                continue
            self.target = np.array([tx, ty])
            return
        # Fallback: use current position with small offset
        self.target = self.position + np.random.uniform(-100, 100, size=2)

    def _find_drift_target(self):
        """Find a gentle nearby drift target for idle behavior."""
        offset = np.random.uniform(-200, 200, size=2)
        candidate = self.position + offset
        x_min, y_min, w, h = self.bounds
        candidate[0] = np.clip(candidate[0], x_min + 30, x_min + w - 30)
        candidate[1] = np.clip(candidate[1], y_min + 30, y_min + h - 30)

        if self.sanctuary and self.sanctuary.is_in_sanctuary(candidate[0], candidate[1]):
            # Try opposite direction
            candidate = self.position - offset
            candidate[0] = np.clip(candidate[0], x_min + 30, x_min + w - 30)
            candidate[1] = np.clip(candidate[1], y_min + 30, y_min + h - 30)

        self._idle_drift_target = candidate

    def _move(self, dt):
        """Movement physics based on current state."""
        if self.state == "SEARCHING":
            direction = self.target - self.position
            norm = np.linalg.norm(direction)
            if norm > 0:
                direction /= norm
                speed = 40.0 + (self.mood / 100.0) * 120.0
                target_vel = direction * speed
                self.velocity = self.velocity * 0.92 + target_vel * 0.08
            else:
                self.velocity *= 0.92

        elif self.state == "FEEDING":
            # Gentle nibble jitter
            self.velocity = np.random.uniform(-5, 5, size=2)

        elif self.state == "RESTING":
            # Very slow drift downward (settling)
            self.velocity *= 0.96
            self.velocity[1] += 2.0 * dt  # Gentle sink

        elif self.state == "COMMUNICATING":
            # Pause movement, face forward
            self.velocity *= 0.9

        elif self.state == "IDLE":
            if self._idle_drift_target is not None:
                direction = self._idle_drift_target - self.position
                norm = np.linalg.norm(direction)
                if norm > 10:
                    direction /= norm
                    drift_speed = 25.0 + (self.mood / 100.0) * 40.0
                    target_vel = direction * drift_speed
                    self.velocity = self.velocity * 0.95 + target_vel * 0.05
                else:
                    self._idle_drift_target = None
                    self.velocity *= 0.96
            else:
                self.velocity *= 0.96

        self.position += self.velocity * dt

    def _apply_sanctuary_forces(self, dt):
        """Apply repulsion forces from sanctuary zones."""
        if not self.sanctuary:
            return

        fx, fy = self.sanctuary.compute_repulsion(self.position[0], self.position[1])
        if abs(fx) > 0.1 or abs(fy) > 0.1:
            self.velocity[0] += fx * dt
            self.velocity[1] += fy * dt
            # Cap velocity to prevent overshooting
            speed = np.linalg.norm(self.velocity)
            if speed > 300:
                self.velocity = self.velocity / speed * 300

    def _check_boundaries(self):
        x_min, y_min, w, h = self.bounds
        margin = 20

        if self.position[0] < x_min + margin:
            self.position[0] = x_min + margin
            self.velocity[0] = abs(self.velocity[0]) * 0.5
        elif self.position[0] > x_min + w - margin:
            self.position[0] = x_min + w - margin
            self.velocity[0] = -abs(self.velocity[0]) * 0.5

        if self.position[1] < y_min + margin:
            self.position[1] = y_min + margin
            self.velocity[1] = abs(self.velocity[1]) * 0.5
        elif self.position[1] > y_min + h - margin:
            self.position[1] = y_min + h - margin
            self.velocity[1] = -abs(self.velocity[1]) * 0.5

    def _check_modules(self):
        """Poll communication modules for new messages."""
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
            "state": self.state
        }
