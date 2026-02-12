"""
Quick test script for jellyfish
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.jellyfish_iridescent_skin import IridescentJellyfish

app = QApplication(sys.argv)

# Create jellyfish
jelly = IridescentJellyfish(config=None)
jelly.x = 960  # Center of screen
jelly.y = 540
jelly.show()

# Animate
def animate():
    # Move in circle
    import math
    t = jelly.time
    target_x = 960 + math.sin(t) * 200
    target_y = 540 + math.cos(t * 0.7) * 150
    jelly.update_state(0.033, target_x, target_y)

timer = QTimer()
timer.timeout.connect(animate)
timer.start(33)

print("Jellyfish test running! Close window to exit.")
app.exec()
