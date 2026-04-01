"""
NetShare Notification Card — glowing post-it style overlay widget.

Design: engineering professional dark theme with animated cyan glow border.
Behaviour:
  - Slides in from the bottom-right corner
  - Glows with a pulsing cyan border animation
  - Mouse hover → pauses the auto-dismiss timer + slightly expands
  - "Open Folder" button → opens the sender's shared folder in Explorer
  - "Dismiss" button → immediately hides the card
  - Auto-dismisses after DISPLAY_SECONDS seconds (paused while hovered)

Each incoming notification spawns one card.
Cards stack upward if multiple notifications arrive quickly.
"""

import math
import os
import subprocess
from datetime import datetime

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QFont, QFontMetrics, QCursor
)

# ------------------------------------------------------------------
# Theme constants — engineering professional dark
# ------------------------------------------------------------------
CLR_BG_TOP       = QColor(10,  24,  40)   # deep navy
CLR_BG_BOT       = QColor(6,   16,  28)   # almost-black navy
CLR_GLOW         = QColor(0,   210, 255)  # electric cyan
CLR_GLOW_DIM     = QColor(0,   140, 200, 80)
CLR_BORDER       = QColor(0,   180, 220)
CLR_TEXT_HEAD    = QColor(224, 244, 255)  # near-white cool
CLR_TEXT_LABEL   = QColor(100, 170, 210)  # muted steel blue
CLR_TEXT_VALUE   = QColor(190, 230, 255)  # bright ice blue
CLR_ACCENT       = QColor(0,   210, 255)  # cyan accent
CLR_BTN_PRIMARY  = QColor(0,   160, 200)
CLR_BTN_HOVER    = QColor(0,   210, 255)
CLR_BTN_DISMISS  = QColor(40,  60,  80)
CLR_DIVIDER      = QColor(30,  60,  90)

CARD_WIDTH       = 340
CARD_HEIGHT_COMPACT  = 120   # no message
CARD_HEIGHT_FULL     = 148   # with message
CORNER_RADIUS    = 10
GLOW_RADIUS      = 14        # outer glow spread
DISPLAY_SECONDS  = 10
SLIDE_DURATION   = 320       # ms for slide-in animation

FONT_TITLE  = QFont("Segoe UI", 9,  QFont.Bold)
FONT_LABEL  = QFont("Segoe UI", 8)
FONT_VALUE  = QFont("Segoe UI", 8,  QFont.Bold)
FONT_BTN    = QFont("Segoe UI", 8,  QFont.Bold)
FONT_BRAND  = QFont("Consolas", 7)


class NetShareCard(QWidget):
    """
    A single glowing post-it notification card.
    Positioned by the card manager (NetShareCardManager).
    """

    def __init__(self, notification: dict, on_open, on_dismiss, parent=None):
        super().__init__(parent)
        self._notification = notification
        self._on_open_cb = on_open
        self._on_dismiss_cb = on_dismiss

        self._hovered     = False
        self._glow_phase  = 0.0          # 0..2π, drives pulsing glow brightness
        self._opacity     = 0.0
        self._elapsed     = 0.0
        self._dismissed   = False

        # Determine card height
        has_msg = bool(notification.get("message", "").strip())
        self._card_h = CARD_HEIGHT_FULL if has_msg else CARD_HEIGHT_COMPACT
        total_h = self._card_h + GLOW_RADIUS * 2

        self.setFixedSize(CARD_WIDTH + GLOW_RADIUS * 2, total_h)

        # Frameless, always-on-top, no taskbar entry
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)

        # Animation timer (drives glow pulse + opacity + auto-dismiss)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(33)  # ~30 fps

        # Slide-in animation
        self._slide_anim = None

    # ------------------------------------------------------------------
    # Positioning
    # ------------------------------------------------------------------

    def slide_in_to(self, target_x: int, target_y: int):
        """Animate card sliding in from below to target position."""
        start_y = target_y + 50
        self.move(target_x, start_y)
        self.show()

        self._slide_anim = QPropertyAnimation(self, b"pos", self)
        self._slide_anim.setDuration(SLIDE_DURATION)
        self._slide_anim.setStartValue(QPoint(target_x, start_y))
        self._slide_anim.setEndValue(QPoint(target_x, target_y))
        self._slide_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._slide_anim.start()

    # ------------------------------------------------------------------
    # Animation tick
    # ------------------------------------------------------------------

    def _tick(self):
        dt = 0.033

        # Glow pulse: full cycle every ~2.5 s
        self._glow_phase = (self._glow_phase + dt * 2.5) % (2 * math.pi)

        # Fade in
        if self._opacity < 1.0:
            self._opacity = min(1.0, self._opacity + dt * 3.0)

        # Auto-dismiss countdown (paused while hovered)
        if not self._hovered and not self._dismissed:
            self._elapsed += dt
            if self._elapsed >= DISPLAY_SECONDS:
                self._start_dismiss()

        self.update()

    def _start_dismiss(self):
        if self._dismissed:
            return
        self._dismissed = True
        # Fade out
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._fade_out_tick)
        self._fade_timer.start(33)

    def _fade_out_tick(self):
        self._opacity = max(0.0, self._opacity - 0.05)
        self.update()
        if self._opacity <= 0.0:
            self._fade_timer.stop()
            self._anim_timer.stop()
            self._on_dismiss_cb(self)
            self.hide()
            self.deleteLater()

    # ------------------------------------------------------------------
    # Mouse events
    # ------------------------------------------------------------------

    def enterEvent(self, event):
        self._hovered = True
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self._opacity)

        ox = GLOW_RADIUS
        oy = GLOW_RADIUS
        cw = CARD_WIDTH
        ch = self._card_h

        # ---- Outer glow ----
        glow_alpha = int(80 + 60 * math.sin(self._glow_phase))
        if self._hovered:
            glow_alpha = min(200, glow_alpha + 80)
        for i in range(GLOW_RADIUS, 0, -2):
            a = int(glow_alpha * (i / GLOW_RADIUS) ** 2)
            glow_col = QColor(CLR_GLOW.red(), CLR_GLOW.green(), CLR_GLOW.blue(), a)
            painter.setPen(QPen(glow_col, 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(ox - i, oy - i, cw + i * 2, ch + i * 2,
                                    CORNER_RADIUS + i, CORNER_RADIUS + i)

        # ---- Card background gradient ----
        bg_grad = QLinearGradient(ox, oy, ox, oy + ch)
        bg_grad.setColorAt(0.0, CLR_BG_TOP)
        bg_grad.setColorAt(1.0, CLR_BG_BOT)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_grad))
        painter.drawRoundedRect(ox, oy, cw, ch, CORNER_RADIUS, CORNER_RADIUS)

        # ---- Top accent bar ----
        accent_h = 3
        accent_col = QColor(CLR_GLOW)
        accent_col.setAlpha(200)
        painter.setBrush(QBrush(accent_col))
        # Clip to card's top-left and top-right rounded corners
        painter.drawRect(ox + CORNER_RADIUS, oy, cw - CORNER_RADIUS * 2, accent_h)

        # ---- Border ----
        border_col = QColor(CLR_BORDER)
        border_col.setAlpha(160 + int(60 * math.sin(self._glow_phase)))
        painter.setPen(QPen(border_col, 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(ox, oy, cw, ch, CORNER_RADIUS, CORNER_RADIUS)

        # ---- Header row ----
        # Icon area
        icon_x = ox + 14
        icon_y = oy + 14
        painter.setBrush(QBrush(CLR_ACCENT))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(icon_x, icon_y, 8, 8)

        # Title
        painter.setFont(FONT_TITLE)
        painter.setPen(CLR_TEXT_HEAD)
        painter.drawText(icon_x + 14, oy + 25, "FILE NOTIFICATION")

        # Timestamp
        ts_raw = self._notification.get("timestamp", "")
        if ts_raw:
            try:
                dt_obj = datetime.fromisoformat(ts_raw)
                ts_str = dt_obj.strftime("%I:%M %p")
            except ValueError:
                ts_str = ts_raw[:5]
        else:
            ts_str = datetime.now().strftime("%I:%M %p")
        painter.setFont(FONT_LABEL)
        painter.setPen(CLR_TEXT_LABEL)
        ts_x = ox + cw - 60
        painter.drawText(ts_x, oy + 25, ts_str)

        # ---- Divider ----
        div_y = oy + 32
        painter.setPen(QPen(CLR_DIVIDER, 1))
        painter.drawLine(ox + 10, div_y, ox + cw - 10, div_y)

        # ---- Fields ----
        sender   = self._notification.get("sender", "Unknown").upper()
        filename = self._notification.get("filename", "").strip()
        message  = self._notification.get("message", "").strip()

        row_y = div_y + 16
        row_gap = 16

        def draw_row(label, value, y):
            painter.setFont(FONT_LABEL)
            painter.setPen(CLR_TEXT_LABEL)
            painter.drawText(ox + 14, y, label)
            painter.setFont(FONT_VALUE)
            painter.setPen(CLR_TEXT_VALUE)
            # Truncate value to fit
            fm = QFontMetrics(FONT_VALUE)
            max_w = cw - 80
            elided = fm.elidedText(value, Qt.ElideRight, max_w)
            painter.drawText(ox + 70, y, elided)

        draw_row("FROM:", sender, row_y)
        if filename:
            draw_row("FILE:", filename, row_y + row_gap)
            if message:
                draw_row("MSG:", message, row_y + row_gap * 2)
        elif message:
            draw_row("MSG:", message, row_y + row_gap)

        # ---- Bottom divider ----
        btn_area_top = oy + ch - 36
        painter.setPen(QPen(CLR_DIVIDER, 1))
        painter.drawLine(ox + 10, btn_area_top, ox + cw - 10, btn_area_top)

        # ---- Brand watermark ----
        painter.setFont(FONT_BRAND)
        painter.setPen(QColor(50, 90, 120, 150))
        painter.drawText(ox + 14, btn_area_top - 4, "Futol Ethical Technology Ecosystems")

        # ---- Hover hint ----
        if self._hovered:
            painter.setFont(FONT_LABEL)
            painter.setPen(QColor(CLR_GLOW.red(), CLR_GLOW.green(), CLR_GLOW.blue(), 160))
            painter.drawText(ox + cw - 130, btn_area_top - 4, "● hover pauses dismiss")

        painter.end()

    # ------------------------------------------------------------------
    # Button geometry helpers (for mousePressEvent)
    # ------------------------------------------------------------------

    def _btn_open_rect(self):
        ox = GLOW_RADIUS
        ch = self._card_h
        btn_y = GLOW_RADIUS + ch - 28
        return QRect(ox + 12, btn_y, 140, 20)

    def _btn_dismiss_rect(self):
        ox = GLOW_RADIUS
        cw = CARD_WIDTH
        ch = self._card_h
        btn_y = GLOW_RADIUS + ch - 28
        return QRect(ox + cw - 100, btn_y, 88, 20)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            if self._btn_open_rect().contains(pos):
                self._do_open()
            elif self._btn_dismiss_rect().contains(pos):
                self._start_dismiss()

    def _do_open(self):
        folder = (
            self._notification.get("_peer_folder")
            or self._notification.get("sender_folder", "")
        )
        if folder and os.path.isdir(folder):
            try:
                subprocess.Popen(["explorer", os.path.normpath(folder)])
            except Exception:
                pass
        if self._on_open_cb:
            self._on_open_cb(self._notification)
        self._start_dismiss()

    # ------------------------------------------------------------------
    # Custom button painting (overlaid on top of paintEvent result)
    # ------------------------------------------------------------------

    def paintEvent(self, event):  # noqa: F811  (redefines above — unified version below)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self._opacity)

        ox = GLOW_RADIUS
        oy = GLOW_RADIUS
        cw = CARD_WIDTH
        ch = self._card_h

        # ---- Outer glow rings ----
        glow_alpha = int(80 + 60 * math.sin(self._glow_phase))
        if self._hovered:
            glow_alpha = min(220, glow_alpha + 100)
        for i in range(GLOW_RADIUS, 0, -2):
            frac = (i / GLOW_RADIUS) ** 1.5
            a = int(glow_alpha * frac)
            c = QColor(CLR_GLOW.red(), CLR_GLOW.green(), CLR_GLOW.blue(), a)
            painter.setPen(QPen(c, 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(ox - i, oy - i, cw + i * 2, ch + i * 2,
                                    CORNER_RADIUS + i, CORNER_RADIUS + i)

        # ---- Card background ----
        bg = QLinearGradient(ox, oy, ox, oy + ch)
        bg.setColorAt(0.0, CLR_BG_TOP)
        bg.setColorAt(1.0, CLR_BG_BOT)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(ox, oy, cw, ch, CORNER_RADIUS, CORNER_RADIUS)

        # ---- Top accent stripe ----
        stripe_alpha = 180 + int(50 * math.sin(self._glow_phase))
        stripe_col = QColor(CLR_GLOW.red(), CLR_GLOW.green(), CLR_GLOW.blue(), stripe_alpha)
        painter.setBrush(QBrush(stripe_col))
        painter.drawRect(ox + CORNER_RADIUS, oy, cw - CORNER_RADIUS * 2, 3)

        # ---- Card border ----
        b_alpha = 140 + int(80 * math.sin(self._glow_phase))
        painter.setPen(QPen(QColor(CLR_BORDER.red(), CLR_BORDER.green(), CLR_BORDER.blue(), b_alpha), 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(ox, oy, cw, ch, CORNER_RADIUS, CORNER_RADIUS)

        # ---- Header ----
        # Notification dot
        dot_alpha = 200 + int(55 * math.sin(self._glow_phase * 2))
        painter.setBrush(QBrush(QColor(CLR_GLOW.red(), CLR_GLOW.green(), CLR_GLOW.blue(), dot_alpha)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(ox + 14, oy + 14, 8, 8)

        painter.setFont(FONT_TITLE)
        painter.setPen(CLR_TEXT_HEAD)
        painter.drawText(ox + 28, oy + 24, "FILE NOTIFICATION")

        # Timestamp
        ts_raw = self._notification.get("timestamp", "")
        try:
            ts_str = datetime.fromisoformat(ts_raw).strftime("%I:%M %p")
        except (ValueError, TypeError):
            ts_str = datetime.now().strftime("%I:%M %p")
        painter.setFont(FONT_LABEL)
        painter.setPen(CLR_TEXT_LABEL)
        painter.drawText(ox + cw - 58, oy + 24, ts_str)

        # Divider under header
        div1_y = oy + 32
        painter.setPen(QPen(CLR_DIVIDER, 1))
        painter.drawLine(ox + 10, div1_y, ox + cw - 10, div1_y)

        # ---- Data fields ----
        sender   = self._notification.get("sender", "Unknown").upper()
        filename = self._notification.get("filename", "").strip()
        message  = self._notification.get("message", "").strip()

        row_y   = div1_y + 15
        row_gap = 15

        def draw_field(label, value, y):
            painter.setFont(FONT_LABEL)
            painter.setPen(CLR_TEXT_LABEL)
            painter.drawText(ox + 12, y, label)
            painter.setFont(FONT_VALUE)
            painter.setPen(CLR_TEXT_VALUE)
            fm = QFontMetrics(FONT_VALUE)
            elided = fm.elidedText(value, Qt.ElideRight, cw - 82)
            painter.drawText(ox + 68, y, elided)

        draw_field("FROM:", sender, row_y)
        next_y = row_y + row_gap
        if filename:
            draw_field("FILE:", filename, next_y)
            next_y += row_gap
        if message:
            draw_field("MSG:", message, next_y)

        # Divider above buttons
        btn_top = oy + ch - 34
        painter.setPen(QPen(CLR_DIVIDER, 1))
        painter.drawLine(ox + 10, btn_top, ox + cw - 10, btn_top)

        # Brand watermark
        painter.setFont(FONT_BRAND)
        painter.setPen(QColor(45, 85, 115, 140))
        painter.drawText(ox + 12, btn_top - 5, "Futol Ethical Technology Ecosystems")

        # Hover info
        if self._hovered:
            painter.setFont(FONT_BRAND)
            painter.setPen(QColor(CLR_GLOW.red(), CLR_GLOW.green(), CLR_GLOW.blue(), 140))
            painter.drawText(ox + cw - 125, btn_top - 5, "\u23f8 hover pauses dismiss")

        # ---- Buttons ----
        open_rect    = self._btn_open_rect()
        dismiss_rect = self._btn_dismiss_rect()

        # Open button
        open_col = CLR_BTN_HOVER if self._hovered else CLR_BTN_PRIMARY
        painter.setBrush(QBrush(open_col))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(open_rect, 4, 4)
        painter.setFont(FONT_BTN)
        painter.setPen(QColor(5, 15, 25))
        painter.drawText(open_rect, Qt.AlignCenter, "\U0001f4c2  Open Folder")

        # Dismiss button
        painter.setBrush(QBrush(CLR_BTN_DISMISS))
        painter.setPen(QPen(CLR_DIVIDER, 1))
        painter.drawRoundedRect(dismiss_rect, 4, 4)
        painter.setFont(FONT_BTN)
        painter.setPen(CLR_TEXT_LABEL)
        painter.drawText(dismiss_rect, Qt.AlignCenter, "\u2715  Dismiss")

        painter.end()


# ------------------------------------------------------------------
# Card Manager — stacks cards upward from the bottom-right corner
# ------------------------------------------------------------------

class NetShareCardManager:
    """
    Manages active notification cards.
    Positions them stacked upward from the bottom-right of the primary screen.
    """

    MARGIN_RIGHT  = 20
    MARGIN_BOTTOM = 60   # above taskbar
    STACK_GAP     = 10

    def __init__(self, on_open_folder_cb):
        self._cards = []
        self._on_open_folder_cb = on_open_folder_cb

    def show_notification(self, notification: dict):
        """Spawn a new notification card for the given notification dict."""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()  # respects taskbar

        card = NetShareCard(
            notification,
            on_open=self._on_open_folder_cb,
            on_dismiss=self._on_card_dismissed,
        )
        self._cards.append(card)
        self._reposition_all(geo)

    def _on_card_dismissed(self, card):
        if card in self._cards:
            self._cards.remove(card)
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        self._reposition_all(screen.availableGeometry())

    def _reposition_all(self, geo):
        """Stack active cards upward from the bottom-right corner."""
        right  = geo.right()
        bottom = geo.bottom()

        cumulative_y = bottom - self.MARGIN_BOTTOM
        for card in reversed(self._cards):
            card_total_h = card.height()
            card_x = right - card.width() - self.MARGIN_RIGHT
            card_y = cumulative_y - card_total_h

            if not card.isVisible():
                card.slide_in_to(card_x, card_y)
            else:
                card.move(card_x, card_y)

            cumulative_y = card_y - self.STACK_GAP
