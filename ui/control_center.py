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
                background-color: rgba(18, 24, 38, 248);
                border: 1px solid rgba(80, 160, 255, 130);
                border-radius: 14px;
            }
            QLabel {
                color: #e0f0ff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: rgba(35, 75, 135, 180);
                color: #ffffff;
                border: 1px solid rgba(90, 170, 240, 140);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(55, 115, 195, 220);
                border-color: rgba(130, 200, 255, 220);
            }
            QPushButton:checked {
                background-color: rgba(46, 125, 50, 220);
                border-color: rgba(100, 220, 120, 220);
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
                color: #c0d8f0;
                font-size: 11px;
            }
            QRadioButton::indicator:checked {
                background-color: #50a0ff;
                border: 2px solid #ffffff;
                border-radius: 6px;
                width: 10px;
                height: 10px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(60, 100, 150, 150);
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #50a0ff;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                border: 1px solid #50a0ff;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QCheckBox {
                color: #a0c4e8;
                font-size: 11px;
            }
        """)

        # Shadow
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(20, 80, 180, 90))
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
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))

        subtitle_label = QLabel("Nature is alive", card)
        subtitle_label.setFont(QFont("Segoe UI", 8))
        subtitle_label.setStyleSheet("color: #70a0d0;")

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
                color: #88aacc;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ffffff;
                background: rgba(255, 255, 255, 30);
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
        ]

        for label_text, oid, default_count in species_list:
            row_layout = QHBoxLayout()

            sp_label = QLabel(label_text, card)
            sp_label.setFont(QFont("Segoe UI", 10, QFont.DemiBold))

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
            count_label.setFont(QFont("Segoe UI", 10, QFont.Bold))

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

            self._species_widgets[oid] = {
                "toggle": toggle_btn,
                "count_label": count_label,
                "minus": minus_btn,
                "plus": plus_btn,
            }

        # Separator line
        card_layout.addWidget(self._make_h_line())

        # ── Size Controls ──
        size_layout = QVBoxLayout()
        size_label = QLabel("Object Size", card)
        size_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        size_layout.addWidget(size_label)

        size_btn_layout = QHBoxLayout()
        self.size_group = QButtonGroup(self)

        for label_text, val in [("Small", 0.5), ("Normal", 1.0), ("Large", 1.5)]:
            rb = QRadioButton(label_text, card)
            rb.setProperty("scaleValue", val)
            if val == 1.0:
                rb.setChecked(True)
            self.size_group.addButton(rb)
            size_btn_layout.addWidget(rb)

        self.size_group.buttonToggled.connect(self._on_size_toggled)
        size_layout.addLayout(size_btn_layout)
        card_layout.addLayout(size_layout)

        # Separator line
        card_layout.addWidget(self._make_h_line())

        # ── Physics Preset Controls ──
        physics_layout = QVBoxLayout()
        phys_hdr_layout = QHBoxLayout()
        phys_label = QLabel("Nature Physics", card)
        phys_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        phys_hdr_layout.addWidget(phys_label)
        physics_layout.addLayout(phys_hdr_layout)

        phys_btn_layout = QHBoxLayout()
        self.physics_group = QButtonGroup(self)

        for mode in ["Calm", "Lively", "Dramatic"]:
            rb = QRadioButton(mode, card)
            rb.setProperty("physicsMode", mode.lower())
            if mode == "Lively":
                rb.setChecked(True)
            self.physics_group.addButton(rb)
            phys_btn_layout.addWidget(rb)

        self.physics_group.buttonToggled.connect(self._on_physics_preset_toggled)
        physics_layout.addLayout(phys_btn_layout)

        # Interaction Strength Slider (25% - 200%)
        slider_row = QHBoxLayout()
        slider_lbl = QLabel("Interaction:", card)
        slider_lbl.setFont(QFont("Segoe UI", 8))

        self.strength_slider = QSlider(Qt.Horizontal, card)
        self.strength_slider.setRange(25, 200)
        self.strength_slider.setValue(100)
        self.strength_slider.valueChanged.connect(self._on_slider_changed)

        self.strength_val_lbl = QLabel("100%", card)
        self.strength_val_lbl.setFixedWidth(36)
        self.strength_val_lbl.setFont(QFont("Segoe UI", 8, QFont.Bold))

        slider_row.addWidget(slider_lbl)
        slider_row.addWidget(self.strength_slider)
        slider_row.addWidget(self.strength_val_lbl)

        physics_layout.addLayout(slider_row)
        card_layout.addLayout(physics_layout)

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
                background-color: rgba(180, 40, 40, 180);
                border-color: rgba(220, 80, 80, 180);
            }
            QPushButton:hover {
                background-color: rgba(220, 50, 50, 220);
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
        line.setStyleSheet("background-color: rgba(60, 110, 180, 60); border: none; min-height: 1px; max-height: 1px;")
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

        # Global size/scale
        global_scale = float(self.config.get("overlays", "global_scale") or 1.0)
        for btn in self.size_group.buttons():
            val = float(btn.property("scaleValue"))
            if abs(val - global_scale) < 0.05:
                btn.blockSignals(True)
                btn.setChecked(True)
                btn.blockSignals(False)

        # Physics mode
        preset = str(self.config.get("nature", "physics_preset") or "lively").lower()
        for btn in self.physics_group.buttons():
            mode = str(btn.property("physicsMode")).lower()
            if mode == preset:
                btn.blockSignals(True)
                btn.setChecked(True)
                btn.blockSignals(False)

        # Interaction strength
        strength = float(self.config.get("nature", "interaction_strength") or 1.0)
        slider_val = int(strength * 100)
        self.strength_slider.blockSignals(True)
        self.strength_slider.setValue(slider_val)
        self.strength_val_lbl.setText(f"{slider_val}%")
        self.strength_slider.blockSignals(False)

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

    def _on_size_toggled(self, button, checked):
        if not checked:
            return
        val = float(button.property("scaleValue"))
        if self.config:
            self.config.set("overlays", "global_scale", val)
            for oid in ["fireflies", "dragonflies", "dandelions"]:
                self.config.set("overlays", f"{oid}_scale", val)
            self.config.save()

        # Reload all active overlays to apply size
        if self.overlay_manager:
            for oid in self.overlay_manager.get_active_ids():
                self.overlay_manager.close_overlay(oid)
                self.overlay_manager.open_overlay(oid)

        self.scale_changed.emit("global", val)

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
