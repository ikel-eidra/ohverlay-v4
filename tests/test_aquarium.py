import sys
from PySide6.QtWidgets import QApplication
from engine.aquarium import MonitorManager

def test_monitor_manager():
    # We need a QApplication to access screens
    app = QApplication.instance() or QApplication(sys.argv)
    mm = MonitorManager()
    bounds = mm.get_total_bounds_tuple()
    assert len(bounds) == 4
    assert bounds[2] > 0
    assert bounds[3] > 0
