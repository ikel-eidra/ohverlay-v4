"""
Bubble particle system for fish-to-user communication.
Bubbles float upward from the fish, morph into text messages, then fade away.
"""

import math
import time
import random
from PySide6.QtGui import QColor, QPainterPath, QFont, QFontMetrics, QRadialGradient, QBrush, QPen
from PySide6.QtCore import QPointF, Qt


class Bubble:
    """A single bubble that rises and optionally carries a text message."""

    def __init__(self, x, y, message=None, category="ambient"):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.message = message
        self.category = category  # "health", "love", "schedule", "news", "ambient"
        self.created_at = time.time()
        self.lifetime = 8.0 if message else 3.0
        self.radius = random.uniform(4, 8) if not message else random.uniform(10, 16)
        self.rise_speed = random.uniform(20, 45)
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.wobble_amp = random.uniform(8, 20)
        self.opacity = 0.0
        self.max_opacity = 1.0
        self.text_revealed = False
        self.pop_progress = 0.0  # 0 to 1, used for text morph

    @property
    def age(self):
        return time.time() - self.created_at

    @property
    def alive(self):
        return self.age < self.lifetime

    @property
    def progress(self):
        return min(1.0, self.age / self.lifetime)

    def update(self, dt):
        """Update bubble position and animation state."""
        # Rise upward with wobble
        self.y -= self.rise_speed * dt
        self.wobble_phase += 2.5 * dt
        self.x = self.start_x + math.sin(self.wobble_phase) * self.wobble_amp

        # Opacity envelope: fade in, hold, fade out
        if self.progress < 0.15:
            self.opacity = self.progress / 0.15
        elif self.progress > 0.75:
            self.opacity = (1.0 - self.progress) / 0.25
        else:
            self.opacity = 1.0

        self.opacity = max(0.0, min(1.0, self.opacity)) * self.max_opacity

        # Text reveal after bubble has risen a bit
        if self.message and self.progress > 0.2:
            self.text_revealed = True
            self.pop_progress = min(1.0, (self.progress - 0.2) / 0.3)

    def render(self, painter):
        """Render the bubble with optional text message."""
        if self.opacity <= 0.01:
            return

        alpha = int(self.opacity * 200)
        painter.save()

        # Category colors
        cat_colors = {
            "health": [100, 220, 140],
            "love": [255, 120, 160],
            "schedule": [120, 180, 255],
            "news": [255, 200, 80],
            "ambient": [180, 220, 255],
        }
        base_col = cat_colors.get(self.category, [180, 220, 255])

        # Draw bubble sphere
        grad = QRadialGradient(
            self.x - self.radius * 0.3,
            self.y - self.radius * 0.3,
            self.radius * 1.5
        )
        grad.setColorAt(0.0, QColor(255, 255, 255, int(alpha * 0.6)))
        grad.setColorAt(0.4, QColor(base_col[0], base_col[1], base_col[2], int(alpha * 0.4)))
        grad.setColorAt(1.0, QColor(base_col[0], base_col[1], base_col[2], 0))

        painter.setPen(QPen(QColor(255, 255, 255, int(alpha * 0.5)), 0.8))
        painter.setBrush(QBrush(grad))

        # Grow/shrink animation
        display_radius = self.radius
        if self.message and self.text_revealed:
            display_radius = self.radius * (1.0 + self.pop_progress * 1.5)

        painter.drawEllipse(QPointF(self.x, self.y), display_radius, display_radius)

        # Highlight spec
        highlight_alpha = int(alpha * 0.7)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, highlight_alpha))
        painter.drawEllipse(
            QPointF(self.x - display_radius * 0.25, self.y - display_radius * 0.35),
            display_radius * 0.3, display_radius * 0.2
        )

        # Draw text message if revealed
        if self.message and self.text_revealed and self.pop_progress > 0.3:
            text_alpha = int(min(1.0, (self.pop_progress - 0.3) / 0.4) * self.opacity * 255)
            self._draw_message(painter, text_alpha, base_col)

        painter.restore()

    def _draw_message(self, painter, text_alpha, base_col):
        """Render the text message above the bubble."""
        font = QFont("Segoe UI", 11)
        font.setWeight(QFont.Medium)
        painter.setFont(font)

        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self.message)
        text_height = fm.height()

        # Background pill
        pill_x = self.x - text_width / 2 - 12
        pill_y = self.y - self.radius * 2 - text_height - 8
        pill_w = text_width + 24
        pill_h = text_height + 12

        bg_path = QPainterPath()
        bg_path.addRoundedRect(pill_x, pill_y, pill_w, pill_h, 10, 10)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(20, 20, 30, int(text_alpha * 0.7)))
        painter.drawPath(bg_path)

        # Border
        painter.setPen(QPen(QColor(base_col[0], base_col[1], base_col[2], int(text_alpha * 0.5)), 1.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(bg_path)

        # Text
        painter.setPen(QColor(255, 255, 255, text_alpha))
        painter.drawText(
            QPointF(self.x - text_width / 2, pill_y + text_height + 2),
            self.message
        )


class BubbleSystem:
    """Manages the lifecycle of all bubbles, spawning and cleanup."""

    def __init__(self, config=None):
        self.bubbles = []
        self.message_queue = []
        self.last_message_time = 0
        self.last_ambient_time = 0

        self.enabled = True
        self.max_visible = 5
        self.display_duration = 8.0
        self.min_interval = 60.0

        if config:
            self.apply_config(config)

    def apply_config(self, config):
        bcfg = config.get("bubbles") if hasattr(config, "get") and callable(config.get) else {}
        if isinstance(bcfg, dict):
            self.enabled = bcfg.get("enabled", self.enabled)
            self.max_visible = bcfg.get("max_visible", self.max_visible)
            self.display_duration = bcfg.get("display_duration_seconds", self.display_duration)
            self.min_interval = bcfg.get("min_interval_seconds", self.min_interval)

    def queue_message(self, message, category="ambient"):
        """Add a message to the queue for delivery by the fish."""
        self.message_queue.append({"message": message, "category": category})

    def update(self, dt, fish_x, fish_y):
        """Update all bubbles and spawn new ones if needed."""
        if not self.enabled:
            return

        # Update existing bubbles
        self.bubbles = [b for b in self.bubbles if b.alive]
        for bubble in self.bubbles:
            bubble.update(dt)

        now = time.time()

        # Spawn ambient bubbles occasionally
        if now - self.last_ambient_time > 4.0 and len(self.bubbles) < 3:
            self.last_ambient_time = now
            if random.random() < 0.3:
                self._spawn_ambient(fish_x, fish_y)

        # Deliver queued messages
        message_bubbles = [b for b in self.bubbles if b.message]
        if (self.message_queue and
                len(message_bubbles) < self.max_visible and
                now - self.last_message_time > self.min_interval):
            msg_data = self.message_queue.pop(0)
            self._spawn_message(fish_x, fish_y, msg_data["message"], msg_data["category"])
            self.last_message_time = now

    def force_deliver(self, fish_x, fish_y):
        """Force-deliver the next queued message immediately."""
        if self.message_queue:
            msg_data = self.message_queue.pop(0)
            self._spawn_message(fish_x, fish_y, msg_data["message"], msg_data["category"])
            self.last_message_time = time.time()

    def _spawn_ambient(self, fish_x, fish_y):
        """Spawn a small decorative bubble near the fish."""
        bx = fish_x + random.uniform(-15, 15)
        by = fish_y + random.uniform(-10, 5)
        self.bubbles.append(Bubble(bx, by))

    def _spawn_message(self, fish_x, fish_y, message, category):
        """Spawn a message-carrying bubble near the fish."""
        bx = fish_x + random.uniform(-20, 20)
        by = fish_y - 10
        bubble = Bubble(bx, by, message=message, category=category)
        bubble.lifetime = self.display_duration
        self.bubbles.append(bubble)

        # Also spawn a few ambient bubbles for effect
        for _ in range(random.randint(2, 4)):
            ax = fish_x + random.uniform(-25, 25)
            ay = fish_y + random.uniform(-5, 10)
            self.bubbles.append(Bubble(ax, ay))

    def render(self, painter):
        """Render all active bubbles."""
        for bubble in self.bubbles:
            bubble.render(painter)
