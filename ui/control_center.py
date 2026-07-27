"""
Persistent Ohverlay Control Center.
A compact, floating panel anchored near the taskbar for controlling nature overlays.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QFrame, QRadioButton, QButtonGroup, QSlider, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QColor, QFont, QGuiApplication
from utils.logger import logger


class ControlCenterSignals(QWidget):
    pass


class ControlCenter(QWidget):
    """Persistent control panel for Ohverlay settings and species management."""

    show_welcome_requested = Signal()
    toggle_all_requested = Signal()
    quit_requested = Signal()
    overlay_toggled = Signal(str, bool)     # (species_id, enabled)
    count_changed = Signal(str, int)        # (species_id, count)
    scale_changed = Signal(str, float)      # (species_id, scale)
    physics_preset_changed = Signal(str)    # ("calm" | "lively" | "dramatic")
    interaction_strength_changed = Signal(float)  # (0.25 to 2.0)

    def __init__(self, config=None, overlay_manager=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.overlay_manager = overlay_manager

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)

        self._species_widgets = {}

        self._build_ui()
        self._update_from_config()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        card = QFrame(self)
        card.setObjectName("controlCard")
        card.setStyleSheet("""
            #controlCard {
                background-color: rgba(17, 19, 24, 0.96);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
            QLabel {
                color: #f0f2f5;
                font-family: 'Arial', sans-serif;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 0.08);
                color: #f0f2f5;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                font-family: 'Arial', sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.16);
                border-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:checked {
                background-color: #2563eb;
                border-color: #3b82f6;
                color: #ffffff;
            }
            QPushButton.stepBtn {
                min-width: 22px;
                max-width: 22px;
                min-height: 22px;
                max-height: 22px;
                padding: 0;
                font-size: 13px;
                font-weight: bold;
            }
            QRadioButton {
                color: #9ea4b0;
                font-size: 11px;
                font-family: 'Arial', sans-serif;
            }
            QRadioButton::indicator:checked {
                background-color: #3b82f6;
                border: 2px solid #ffffff;
                border-radius: 5px;
                width: 10px;
                height: 10px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255, 255, 255, 0.12);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #3b82f6;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 1px solid #3b82f6;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QCheckBox {
                color: #9ea4b0;
                font-size: 11px;
                font-family: 'Arial', sans-serif;
            }
        """)

        # Shadow
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 140))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        # ── Header ──
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(1)

        title_label = QLabel("Ohverlay", card)
        title_label.setFont(QFont("Arial", 12, QFont.Bold))

        subtitle_label = QLabel("Nature is alive", card)
        subtitle_label.setFont(QFont("Arial", 8))
        subtitle_label.setStyleSheet("color: #9ea4b0;")

        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Pin checkbox
        self.pin_btn = QCheckBox("📌 Pin", card)
        self.pin_btn.setToolTip("Keep controls open when clicking elsewhere")
        self.pin_btn.toggled.connect(self._on_pin_toggled)
        header_layout.addWidget(self.pin_btn)

        close_btn = QPushButton("×", card)
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #9ea4b0;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ffffff;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 11px;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)

        card_layout.addLayout(header_layout)

        # Separator line
        card_layout.addWidget(self._make_h_line())

        # ── Species Rows ──
        species_list = [
            ("✨ Fireflies", "fireflies", 6),
            ("🪶 Dragonflies", "dragonflies", 2),
            ("🌱 Dandelions", "dandelions", 3),
            ("🌸 Sakura Petals", "sakura_petals", 18),
        ]

        for label_text, oid, default_count in species_list:
            row_layout = QHBoxLayout()

            sp_label = QLabel(label_text, card)
            sp_label.setFont(QFont("Arial", 10, QFont.DemiBold))

            toggle_btn = QPushButton("OFF", card)
            toggle_btn.setCheckable(True)
            toggle_btn.setFixedWidth(46)
            toggle_btn.toggled.connect(lambda checked, s_id=oid: self._on_species_toggled(s_id, checked))

            minus_btn = QPushButton("−", card)
            minus_btn.setProperty("class", "stepBtn")
            minus_btn.setFixedWidth(22)

            count_label = QLabel(str(default_count), card)
            count_label.setFixedWidth(20)
            count_label.setAlignment(Qt.AlignCenter)
            count_label.setFont(QFont("Arial", 10, QFont.Bold))

            plus_btn = QPushButton("+", card)
            plus_btn.setProperty("class", "stepBtn")
            plus_btn.setFixedWidth(22)

            minus_btn.clicked.connect(lambda _, s_id=oid: self._adjust_count(s_id, -1))
            plus_btn.clicked.connect(lambda _, s_id=oid: self._adjust_count(s_id, +1))

            row_layout.addWidget(sp_label)
            row_layout.addStretch()
            row_layout.addWidget(toggle_btn)
            row_layout.addSpacing(6)
            row_layout.addWidget(minus_btn)
            row_layout.addWidget(count_label)
            row_layout.addWidget(plus_btn)

            card_layout.addLayout(row_layout)

            # Sub-row for individual size
            size_subrow = QHBoxLayout()
            size_subrow.setContentsMargins(18, 0, 0, 0)
            
            size_lbl = QLabel("Size:", card)
            size_lbl.setFont(QFont("Arial", 8))
            size_lbl.setStyleSheet("color: #9ea4b0;")
            size_subrow.addWidget(size_lbl)
            
            bg = QButtonGroup(self)
            for sz_label, sz_val in [("Small", 0.5), ("Normal", 1.0), ("Large", 1.5)]:
                rb = QRadioButton(sz_label, card)
                rb.setStyleSheet("QRadioButton { font-size: 10px; color: #9ea4b0; font-family: 'Arial', sans-serif; }")
                rb.setProperty("scaleValue", sz_val)
                rb.setProperty("speciesId", oid)
                if sz_val == 1.0:
                    rb.setChecked(True)
                bg.addButton(rb)
                size_subrow.addWidget(rb)
                
            size_subrow.addStretch()
            card_layout.addLayout(size_subrow)
            bg.buttonToggled.connect(self._on_species_size_toggled)

            self._species_widgets[oid] = {
                "toggle": toggle_btn,
                "count_label": count_label,
                "minus": minus_btn,
                "plus": plus_btn,
                "size_group": bg,
            }

        # Separator line
        card_layout.addWidget(self._make_h_line())

        # ── Action Buttons Footer ──
        act_layout = QHBoxLayout()

        self.hide_all_btn = QPushButton("Hide All", card)
        self.hide_all_btn.clicked.connect(self._on_hide_all_clicked)

        welcome_btn = QPushButton("Welcome Guide", card)
        welcome_btn.clicked.connect(self.show_welcome_requested.emit)

        quit_btn = QPushButton("Quit", card)
        quit_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                border: 1px solid rgba(239, 68, 68, 0.4);
                color: #fca5a5;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.3);
                border-color: rgba(239, 68, 68, 0.6);
            }
        """)
        quit_btn.clicked.connect(self.quit_requested.emit)

        act_layout.addWidget(self.hide_all_btn)
        act_layout.addWidget(welcome_btn)
        act_layout.addWidget(quit_btn)

        card_layout.addLayout(act_layout)

        main_layout.addWidget(card)
        self.setFixedWidth(310)

    def _make_h_line(self):
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.08); border: none; min-height: 1px; max-height: 1px;")
        return line

    def _position_above_taskbar(self):
        """Calculate primary screen bounds and position Control Center near tray area."""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geo = screen.geometry()
        avail = screen.availableGeometry()

        # Default width/height
        panel_w = self.width()
        panel_h = self.sizeHint().height()

        # Inquire taskbar position by comparing total vs available geometry
        x = avail.right() - panel_w - 12
        y = avail.bottom() - panel_h - 12

        # Clamp safely within available display coordinates
        x = max(avail.left() + 10, min(x, avail.right() - panel_w - 10))
        y = max(avail.top() + 10, min(y, avail.bottom() - panel_h - 10))

        self.move(x, y)

    def show_panel(self):
        """Show and position the Control Center."""
        self._update_from_config()
        self._position_above_taskbar()
        self.show()
        self.raise_()
        self.activateWindow()

    def is_pinned(self):
        return self.pin_btn.isChecked()

    def _on_pin_toggled(self, checked):
        if self.config:
            self.config.set("control_center", "pinned", checked)
            self.config.save()

    def changeEvent(self, event):
        """Close on focus loss if not pinned."""
        if event.type() == QEvent.ActivationChange:
            if not self.isActiveWindow() and not self.is_pinned():
                self.hide()
        super().changeEvent(event)

    def _update_from_config(self):
        if not self.config:
            return

        # Pin state
        pinned = self.config.get("control_center", "pinned") or False
        self.pin_btn.setChecked(bool(pinned))

        # Species state
        for oid, widgets in self._species_widgets.items():
            active = self.config.get("overlays", oid) or False
            count = self.config.get("overlays", f"{oid}_count")
            if count is None:
                count = 6 if oid == "fireflies" else (2 if oid == "dragonflies" else 3)

            widgets["toggle"].blockSignals(True)
            widgets["toggle"].setChecked(bool(active))
            widgets["toggle"].setText("ON" if active else "OFF")
            widgets["toggle"].blockSignals(False)

            widgets["count_label"].setText(str(count))
            widgets["count_label"].setToolTip(f"{oid.capitalize()}: {count} of 12")

        # Species scale/size
        for oid, widgets in self._species_widgets.items():
            scale_val = float(self.config.get("overlays", f"{oid}_scale") or 1.0)
            for btn in widgets["size_group"].buttons():
                val = float(btn.property("scaleValue"))
                if abs(val - scale_val) < 0.05:
                    btn.blockSignals(True)
                    btn.setChecked(True)
                    btn.blockSignals(False)

    def _on_species_toggled(self, species_id, checked):
        widgets = self._species_widgets.get(species_id)
        if widgets:
            widgets["toggle"].setText("ON" if checked else "OFF")

        if self.config:
            self.config.set("overlays", species_id, checked)
            self.config.save()

        if self.overlay_manager:
            if checked:
                self.overlay_manager.open_overlay(species_id)
            else:
                self.overlay_manager.close_overlay(species_id)

        self.overlay_toggled.emit(species_id, checked)

    def _adjust_count(self, species_id, delta):
        widgets = self._species_widgets.get(species_id)
        if not widgets:
            return

        current = int(widgets["count_label"].text())
        new_count = max(1, min(12, current + delta))
        if new_count == current:
            return

        widgets["count_label"].setText(str(new_count))
        widgets["count_label"].setToolTip(f"{species_id.capitalize()}: {new_count} of 12")

        if self.config:
            self.config.set("overlays", f"{species_id}_count", new_count)
            self.config.save()

        # Reload active overlay to apply count
        if self.overlay_manager and self.overlay_manager.is_active(species_id):
            self.overlay_manager.close_overlay(species_id)
            self.overlay_manager.open_overlay(species_id)

        self.count_changed.emit(species_id, new_count)

    def _on_species_size_toggled(self, button, checked):
        if not checked:
            return
        species_id = button.property("speciesId")
        val = float(button.property("scaleValue"))
        if self.config:
            self.config.set("overlays", f"{species_id}_scale", val)
            self.config.save()

        # Reload the overlay if active to apply new scale/size
        if self.overlay_manager and self.overlay_manager.is_active(species_id):
            self.overlay_manager.close_overlay(species_id)
            self.overlay_manager.open_overlay(species_id)

        self.scale_changed.emit(species_id, val)

    def _on_physics_preset_toggled(self, button, checked):
        if not checked:
            return
        mode = str(button.property("physicsMode")).lower()
        if self.config:
            self.config.set("nature", "physics_preset", mode)
            self.config.save()
        self.physics_preset_changed.emit(mode)

    def _on_slider_changed(self, value):
        self.strength_val_lbl.setText(f"{value}%")
        multiplier = value / 100.0
        if self.config:
            self.config.set("nature", "interaction_strength", multiplier)
            self.config.save()
        self.interaction_strength_changed.emit(multiplier)

    def _on_hide_all_clicked(self):
        self.toggle_all_requested.emit()
        is_visible = getattr(self.overlay_manager, "_global_visible", True)
        self.hide_all_btn.setText("Show All" if not is_visible else "Hide All")
