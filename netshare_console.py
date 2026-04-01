"""
NetShare Activity Console — engineering professional dark-theme status window.

Displays a live activity log table, peer connection status, and system info.
Branding: Futol Ethical Technology Ecosystems / Sarah Attaqnia Contracting Company.

The console can be toggled from the tray icon. It is NOT always visible —
it's an on-demand audit/monitoring window.
"""

import json
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QSizePolicy, QPushButton, QScrollBar
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap,
    QPainter, QLinearGradient, QBrush, QPen, QFontMetrics
)

# ------------------------------------------------------------------
# Theme
# ------------------------------------------------------------------
BG_WINDOW      = "#080F18"
BG_HEADER      = "#0A1520"
BG_TABLE       = "#06101A"
BG_ROW_ALT    = "#0C1824"
BG_STATUS_BAR  = "#050D16"
CLR_CYAN       = "#00D4FF"
CLR_CYAN_DIM   = "#006880"
CLR_GREEN      = "#00FF88"
CLR_ORANGE     = "#FF6B35"
CLR_RED        = "#FF4444"
CLR_TEXT       = "#C8E8FF"
CLR_MUTED      = "#4A7A9A"
CLR_HEADER_TXT = "#7FB8D8"
CLR_BORDER     = "#0D2840"
CLR_BRAND_1    = "#00D4FF"
CLR_BRAND_2    = "#7FB8D8"

FONT_MONO    = QFont("Consolas",    9)
FONT_MONO_SM = QFont("Consolas",    8)
FONT_LABEL   = QFont("Segoe UI",    9)
FONT_LABEL_B = QFont("Segoe UI",    9, QFont.Bold)
FONT_TITLE   = QFont("Segoe UI",   11, QFont.Bold)
FONT_BRAND   = QFont("Consolas",    8)
FONT_STATUS  = QFont("Consolas",    8)

EVENT_ICONS = {
    "sent":         ("▲", CLR_CYAN),
    "received":     ("●", CLR_GREEN),
    "opened":       ("✓", CLR_GREEN),
    "ack_received": ("✓", CLR_CYAN),
    "error":        ("✗", CLR_RED),
}

MAX_ROWS = 200  # keep at most 200 rows in memory


def _now_str():
    return datetime.now().strftime("%H:%M:%S")


def _clr(hex_str):
    return QColor(hex_str)


# ------------------------------------------------------------------
# Header banner widget
# ------------------------------------------------------------------

class ConsoleBanner(QWidget):
    """Top banner with company branding and live clock."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(68)
        self._tick = 0

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

        self._time_str = datetime.now().strftime("%H:%M:%S")
        self._date_str = datetime.now().strftime("%A, %d %B %Y")

    def _update_clock(self):
        self._time_str = datetime.now().strftime("%H:%M:%S")
        self._date_str = datetime.now().strftime("%A, %d %B %Y")
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background gradient
        grad = QLinearGradient(0, 0, w, 0)
        grad.setColorAt(0.0, _clr("#040C18"))
        grad.setColorAt(0.5, _clr("#081828"))
        grad.setColorAt(1.0, _clr("#040C18"))
        p.fillRect(0, 0, w, h, QBrush(grad))

        # Left: app name
        p.setFont(QFont("Consolas", 14, QFont.Bold))
        p.setPen(_clr(CLR_CYAN))
        p.drawText(16, 28, "NETSHARE")

        p.setFont(QFont("Consolas", 8))
        p.setPen(_clr(CLR_MUTED))
        p.drawText(16, 44, "NETWORK FILE NOTIFICATION SYSTEM  v1.0")

        # Centre: company name
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(_clr(CLR_TEXT))
        company = "Sarah Attaqnia Contracting Company"
        fm = QFontMetrics(p.font())
        cx = (w - fm.horizontalAdvance(company)) // 2
        p.drawText(cx, 26, company)

        p.setFont(QFont("Consolas", 7))
        p.setPen(_clr(CLR_MUTED))
        brand = "Developed by Futol Ethical Technology Ecosystems"
        fm2 = QFontMetrics(p.font())
        bx = (w - fm2.horizontalAdvance(brand)) // 2
        p.drawText(bx, 40, brand)

        # Right: live clock
        p.setFont(QFont("Consolas", 16, QFont.Bold))
        p.setPen(_clr(CLR_CYAN))
        time_w = QFontMetrics(p.font()).horizontalAdvance(self._time_str)
        p.drawText(w - time_w - 16, 30, self._time_str)

        p.setFont(QFont("Consolas", 7))
        p.setPen(_clr(CLR_MUTED))
        date_w = QFontMetrics(p.font()).horizontalAdvance(self._date_str)
        p.drawText(w - date_w - 16, 46, self._date_str)

        # Bottom border line (cyan)
        p.setPen(QPen(_clr(CLR_CYAN_DIM), 1))
        p.drawLine(0, h - 1, w, h - 1)
        p.end()


# ------------------------------------------------------------------
# Status bar
# ------------------------------------------------------------------

class ConsoleStatusBar(QWidget):
    """Bottom status bar showing peer status, log count, system status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(26)
        self._peers = []    # list of (name, reachable: bool)
        self._log_count = 0
        self._status_msg = "IDLE"

    def set_peers(self, peers):
        self._peers = peers
        self.update()

    def set_log_count(self, n):
        self._log_count = n
        self.update()

    def set_status(self, msg):
        self._status_msg = msg.upper()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()

        p.fillRect(0, 0, w, h, _clr(BG_STATUS_BAR))
        p.setPen(QPen(_clr(CLR_BORDER), 1))
        p.drawLine(0, 0, w, 0)

        x = 12
        p.setFont(FONT_STATUS)

        def segment(color, text):
            nonlocal x
            p.setPen(_clr(color))
            p.drawText(x, 17, text)
            x += QFontMetrics(FONT_STATUS).horizontalAdvance(text) + 14
            # separator
            p.setPen(_clr(CLR_BORDER))
            p.drawLine(x - 6, 5, x - 6, h - 5)

        segment(CLR_GREEN,   f"● ONLINE")
        segment(CLR_MUTED,   f"LOG: {self._log_count} events")

        for peer_name, reachable in self._peers:
            col = CLR_GREEN if reachable else CLR_MUTED
            icon = "◆" if reachable else "◇"
            segment(col, f"{icon} {peer_name}")

        # Right-aligned status msg
        p.setFont(FONT_STATUS)
        p.setPen(_clr(CLR_MUTED))
        msg_w = QFontMetrics(FONT_STATUS).horizontalAdvance(self._status_msg)
        p.drawText(w - msg_w - 12, 17, self._status_msg)

        p.end()


# ------------------------------------------------------------------
# Main Console Window
# ------------------------------------------------------------------

class NetShareConsole(QWidget):
    """
    Engineering-professional activity console window.
    Shows a live log table of all send/receive/open events.
    """

    closed = Signal()

    COL_TIME  = 0
    COL_EVENT = 1
    COL_FROM  = 2
    COL_FILE  = 3
    COL_ID    = 4

    COLS = ["TIME", "EVENT", "FROM / TO", "FILE / MESSAGE", "ID"]

    def __init__(self, log_path: str, parent=None):
        super().__init__(parent)
        self.log_path = log_path
        self._last_log_size = 0
        self._row_data = []

        self.setWindowTitle("NetShare Console — Futol Ethical Technology Ecosystems")
        self.setMinimumSize(760, 480)
        self.resize(900, 540)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)

        self._apply_palette()
        self._build_ui()
        self._load_log()

        # Poll log file for new entries every 3 s
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_log)
        self._poll_timer.start(3000)

    # ------------------------------------------------------------------
    # Palette / theme
    # ------------------------------------------------------------------

    def _apply_palette(self):
        pal = QPalette()
        pal.setColor(QPalette.Window,          _clr(BG_WINDOW))
        pal.setColor(QPalette.WindowText,      _clr(CLR_TEXT))
        pal.setColor(QPalette.Base,            _clr(BG_TABLE))
        pal.setColor(QPalette.AlternateBase,   _clr(BG_ROW_ALT))
        pal.setColor(QPalette.Text,            _clr(CLR_TEXT))
        pal.setColor(QPalette.Button,          _clr(BG_HEADER))
        pal.setColor(QPalette.ButtonText,      _clr(CLR_TEXT))
        pal.setColor(QPalette.Highlight,       _clr(CLR_CYAN_DIM))
        pal.setColor(QPalette.HighlightedText, _clr(CLR_TEXT))
        self.setPalette(pal)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Banner
        self._banner = ConsoleBanner()
        root.addWidget(self._banner)

        # Toolbar
        toolbar = self._build_toolbar()
        root.addWidget(toolbar)

        # Table
        self._table = self._build_table()
        root.addWidget(self._table, 1)

        # Status bar
        self._status_bar = ConsoleStatusBar()
        root.addWidget(self._status_bar)

    def _build_toolbar(self):
        bar = QWidget()
        bar.setFixedHeight(34)
        bar.setStyleSheet(f"background: {BG_HEADER}; border-bottom: 1px solid {CLR_BORDER};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.setSpacing(8)

        title = QLabel("ACTIVITY LOG")
        title.setFont(QFont("Consolas", 9, QFont.Bold))
        title.setStyleSheet(f"color: {CLR_CYAN}; background: transparent;")
        lay.addWidget(title)

        lay.addStretch()

        for label, slot in [("REFRESH", self._load_log), ("CLEAR VIEW", self._clear_table)]:
            btn = QPushButton(label)
            btn.setFont(QFont("Consolas", 8))
            btn.setFixedHeight(22)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {BG_WINDOW};
                    color: {CLR_CYAN};
                    border: 1px solid {CLR_CYAN_DIM};
                    border-radius: 3px;
                    padding: 0 10px;
                }}
                QPushButton:hover {{
                    background: {CLR_CYAN_DIM};
                    color: #E8F8FF;
                }}
                QPushButton:pressed {{
                    background: {CLR_CYAN};
                    color: #000;
                }}
            """)
            btn.clicked.connect(slot)
            lay.addWidget(btn)

        return bar

    def _build_table(self):
        tbl = QTableWidget(0, len(self.COLS))
        tbl.setHorizontalHeaderLabels(self.COLS)
        tbl.setFont(FONT_MONO_SM)
        tbl.setAlternatingRowColors(True)
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setShowGrid(False)
        tbl.verticalHeader().setVisible(False)
        tbl.setFocusPolicy(Qt.NoFocus)

        tbl.setStyleSheet(f"""
            QTableWidget {{
                background: {BG_TABLE};
                alternate-background-color: {BG_ROW_ALT};
                color: {CLR_TEXT};
                border: none;
                gridline-color: {CLR_BORDER};
                font-family: Consolas;
                font-size: 8pt;
            }}
            QHeaderView::section {{
                background: {BG_HEADER};
                color: {CLR_HEADER_TXT};
                border: none;
                border-bottom: 1px solid {CLR_CYAN_DIM};
                padding: 4px 8px;
                font-family: Consolas;
                font-size: 8pt;
                font-weight: bold;
            }}
            QTableWidget::item:selected {{
                background: {CLR_CYAN_DIM};
                color: #E8F8FF;
            }}
            QScrollBar:vertical {{
                background: {BG_WINDOW};
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {CLR_CYAN_DIM};
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        hdr = tbl.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_TIME,  QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_EVENT, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_FROM,  QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_FILE,  QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.COL_ID,    QHeaderView.ResizeToContents)

        tbl.setRowHeight(0, 22)
        return tbl

    # ------------------------------------------------------------------
    # Log loading
    # ------------------------------------------------------------------

    def _load_log(self):
        if not os.path.exists(self.log_path):
            self._status_bar.set_status("No log yet")
            return

        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        entries = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        self._rebuild_table(entries)
        self._status_bar.set_log_count(len(entries))
        self._status_bar.set_status(f"Last refresh {_now_str()}")
        self._last_log_size = os.path.getsize(self.log_path)

    def _poll_log(self):
        if not os.path.exists(self.log_path):
            return
        size = os.path.getsize(self.log_path)
        if size != self._last_log_size:
            self._load_log()

    def _rebuild_table(self, entries):
        self._table.setRowCount(0)
        # Show newest first
        for entry in reversed(entries[-MAX_ROWS:]):
            self._append_row(entry)
        self._table.scrollToTop()

    def _append_row(self, entry: dict):
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setRowHeight(row, 22)

        event    = entry.get("event", "")
        ts_raw   = entry.get("timestamp", "")
        sender   = (entry.get("sender") or entry.get("to") or entry.get("from_user") or "—")
        filename = (entry.get("filename") or entry.get("message") or "—")
        notif_id = entry.get("notification_id", "—")

        try:
            ts_str = datetime.fromisoformat(ts_raw).strftime("%H:%M:%S")
        except (ValueError, TypeError):
            ts_str = ts_raw[:8] if ts_raw else "—"

        icon, color = EVENT_ICONS.get(event, ("·", CLR_MUTED))
        event_display = f"{icon}  {event.replace('_', ' ').upper()}"

        def cell(text, color_hex=CLR_TEXT, bold=False):
            item = QTableWidgetItem(str(text))
            item.setForeground(_clr(color_hex))
            if bold:
                f = QFont("Consolas", 8, QFont.Bold)
                item.setFont(f)
            return item

        self._table.setItem(row, self.COL_TIME,  cell(ts_str,        CLR_MUTED))
        self._table.setItem(row, self.COL_EVENT, cell(event_display,  color, bold=True))
        self._table.setItem(row, self.COL_FROM,  cell(sender,        CLR_TEXT))
        self._table.setItem(row, self.COL_FILE,  cell(filename,      CLR_TEXT))
        self._table.setItem(row, self.COL_ID,    cell(notif_id,      CLR_MUTED))

    def _clear_table(self):
        self._table.setRowCount(0)
        self._status_bar.set_status("View cleared (log file untouched)")

    # ------------------------------------------------------------------
    # Peer status update
    # ------------------------------------------------------------------

    def update_peers(self, peers: list):
        """peers: list of (name, reachable: bool)"""
        self._status_bar.set_peers(peers)

    # ------------------------------------------------------------------
    # Close event
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self._poll_timer.stop()
        self.closed.emit()
        event.accept()
