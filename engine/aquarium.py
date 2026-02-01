from PySide6.QtWidgets import QMainWindow, QWidget
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QGuiApplication, QPainter
from utils.logger import logger
from ui.skin import FishSkin

class MonitorManager:
    def __init__(self):
        self.screens = QGuiApplication.screens()
        self.geometries = [screen.geometry() for screen in self.screens]
        self.total_bounds = self._calculate_total_bounds()
        logger.info(f"Detected {len(self.screens)} screens.")
        for i, rect in enumerate(self.geometries):
            logger.info(f"Screen {i}: {rect.x()}, {rect.y()}, {rect.width()}x{rect.height()}")

    def _calculate_total_bounds(self):
        if not self.geometries:
            return QRect(0, 0, 1920, 1080)

        min_x = min(r.x() for r in self.geometries)
        min_y = min(r.y() for r in self.geometries)
        max_x = max(r.x() + r.width() for r in self.geometries)
        max_y = max(r.y() + r.height() for r in self.geometries)

        return QRect(min_x, min_y, max_x - min_x, max_y - min_y)

    def get_total_bounds_tuple(self):
        return (self.total_bounds.x(), self.total_bounds.y(),
                self.total_bounds.width(), self.total_bounds.height())

class AquariumSector(QMainWindow):
    def __init__(self, screen_geometry, sector_id):
        super().__init__()
        self.sector_id = sector_id
        self.screen_geometry = screen_geometry
        self.fish_state = None
        self.fish_local_pos = (0, 0)
        self.should_render = False
        self.skin = FishSkin()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.WindowTransparentForInput |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        self.setGeometry(screen_geometry)

        logger.info(f"Aquarium Sector {sector_id} initialized at {screen_geometry}")

    def update_fish_state(self, fish_state):
        self.fish_state = fish_state
        # Global to local coordinates
        global_pos = fish_state["position"]
        local_x = global_pos[0] - self.screen_geometry.x()
        local_y = global_pos[1] - self.screen_geometry.y()

        # Check if fish is in this sector (with padding)
        padding = 200
        if (-padding <= local_x <= self.screen_geometry.width() + padding and
            -padding <= local_y <= self.screen_geometry.height() + padding):
            self.fish_local_pos = (local_x, local_y)
            self.should_render = True
        else:
            self.should_render = False

        if self.should_render:
            self.update() # Trigger repaint

    def paintEvent(self, event):
        if not self.should_render or not self.fish_state:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self.skin.render(painter, self.fish_local_pos, self.fish_state)
        painter.end()
