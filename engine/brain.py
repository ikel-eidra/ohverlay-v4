import numpy as np
import time
from utils.logger import logger

class BehavioralReactor:
    def __init__(self):
        self.hunger = 0.0  # 0 to 100
        self.mood = 100.0   # 0 to 100
        self.position = np.array([100.0, 100.0])  # Global coordinates
        self.velocity = np.array([0.0, 0.0])
        self.target = np.array([100.0, 100.0])
        self.last_update = time.time()

        self.state = "IDLE" # IDLE, SEARCHING, FEEDING, RESTING
        self.bounds = [0, 0, 1920, 1080] # Default, will be updated by MonitorManager

        logger.info("Neural Brain (Behavioral Reactor) initialized.")

    def set_bounds(self, x, y, w, h):
        self.bounds = [x, y, w, h]
        logger.info(f"Aquarium bounds set to: {self.bounds}")

    def update(self):
        now = time.time()
        dt = now - self.last_update
        self.last_update = now

        # Clamp dt to avoid huge jumps if the app lags
        dt = min(dt, 0.1)

        # Increase hunger
        self.hunger = min(100.0, self.hunger + 0.5 * dt)

        # Update mood based on hunger
        if self.hunger > 70:
            self.mood = max(0.0, self.mood - 1.0 * dt)
        else:
            self.mood = min(100.0, self.mood + 0.1 * dt)

        self._think(dt)
        self._move(dt)
        self._check_boundaries()

    def _think(self, dt):
        if self.state == "IDLE":
            if self.hunger > 30:
                self.state = "SEARCHING"
                self._find_new_target()
                logger.debug(f"State changed to SEARCHING. Hunger: {self.hunger:.2f}")
            elif np.random.random() < 0.01: # Randomly move even if not hungry
                self._find_new_target()

        elif self.state == "SEARCHING":
            dist = np.linalg.norm(self.target - self.position)
            if dist < 15:
                if self.hunger > 20:
                    self.state = "FEEDING"
                    logger.debug("State changed to FEEDING.")
                else:
                    self.state = "IDLE"
                    logger.debug("State changed to IDLE.")

        elif self.state == "FEEDING":
            self.hunger = max(0.0, self.hunger - 10.0 * dt)
            if self.hunger <= 0:
                self.state = "IDLE"
                logger.debug("Satiated. State changed to IDLE.")
            elif np.random.random() < 0.05: # Chance to finish early or move to next algae
                 self._find_new_target()
                 self.state = "SEARCHING"

    def _find_new_target(self):
        x_min, y_min, w, h = self.bounds
        self.target = np.array([
            np.random.uniform(x_min, x_min + w),
            np.random.uniform(y_min, y_min + h)
        ])
        logger.debug(f"New target acquired: {self.target}")

    def _move(self, dt):
        if self.state == "SEARCHING":
            direction = self.target - self.position
            norm = np.linalg.norm(direction)
            if norm > 0:
                direction /= norm
                # Speed depends on mood
                speed = 50.0 + (self.mood / 100.0) * 150.0
                target_velocity = direction * speed
                # Smooth velocity transition
                self.velocity = self.velocity * 0.9 + target_velocity * 0.1
            else:
                self.velocity *= 0.9
        elif self.state == "FEEDING":
            # Small jitter while feeding
            self.velocity = np.random.uniform(-10, 10, size=2)
        else:
            # Idle drift
            self.velocity *= 0.95

        self.position += self.velocity * dt

    def _check_boundaries(self):
        x_min, y_min, w, h = self.bounds
        if self.position[0] < x_min:
            self.position[0] = x_min
            self.velocity[0] *= -1
        elif self.position[0] > x_min + w:
            self.position[0] = x_min + w
            self.velocity[0] *= -1

        if self.position[1] < y_min:
            self.position[1] = y_min
            self.velocity[1] *= -1
        elif self.position[1] > y_min + h:
            self.position[1] = y_min + h
            self.velocity[1] *= -1

    def get_state(self):
        return {
            "position": self.position.tolist(),
            "velocity": self.velocity.tolist(),
            "hunger": self.hunger,
            "mood": self.mood,
            "state": self.state
        }
