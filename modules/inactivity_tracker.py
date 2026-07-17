import ctypes
from PySide6.QtCore import QObject, QTimer, Signal

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("dwTime", ctypes.c_uint)]

class InactivityTracker(QObject):
    screensaver_triggered = Signal()
    screensaver_dismissed = Signal()
    
    def __init__(self, timeout_seconds=10, parent=None):
        super().__init__(parent)
        self.timeout_seconds = timeout_seconds
        self.is_active = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_idle)
        self.timer.start(1000) # Check every second
        
    def check_idle(self):
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo)):
            millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
            idle_seconds = millis / 1000.0
            
            if idle_seconds >= self.timeout_seconds and not self.is_active:
                self.is_active = True
                self.screensaver_triggered.emit()
            elif idle_seconds < self.timeout_seconds and self.is_active:
                self.is_active = False
                self.screensaver_dismissed.emit()
