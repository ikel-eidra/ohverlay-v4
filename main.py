import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from engine.brain import BehavioralReactor
from engine.aquarium import MonitorManager, AquariumSector
from utils.logger import logger

def main():
    logger.info("Initializing Project Aether-Fin...")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Keep running even if sectors are closed (though they shouldn't be)

    # 1. Initialize Monitor Manager
    monitor_manager = MonitorManager()
    total_bounds = monitor_manager.get_total_bounds_tuple()

    # 2. Initialize Neural Brain
    brain = BehavioralReactor()
    brain.set_bounds(*total_bounds)

    # 3. Initialize Aquarium Sectors (one per screen)
    sectors = []
    for i, screen in enumerate(monitor_manager.screens):
        sector = AquariumSector(screen.geometry(), i)
        sector.show()
        sectors.append(sector)

    # 4. Main Loop
    timer = QTimer()
    def tick():
        brain.update()
        fish_state = brain.get_state()

        for sector in sectors:
            sector.update_fish_state(fish_state)

    timer.timeout.connect(tick)
    timer.start(33) # ~30 FPS

    logger.info("Project Aether-Fin operational.")

    # Add a way to exit the app if needed (e.g., Ctrl+C in terminal)
    # In a real overlay, we'd have a system tray icon.

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
