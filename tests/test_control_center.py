import os
import json
import tempfile
import unittest
from PySide6.QtWidgets import QApplication
from config.settings import Settings
from ui.control_center import ControlCenter
from ui.welcome import WelcomeGuide

app = QApplication.instance() or QApplication([])


class TestControlCenterAndOnboarding(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "config.json")
        self.settings = Settings(config_path=self.config_path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_settings_count_validation(self):
        # Write corrupted config with out-of-bound counts
        corrupted_data = {
            "overlays": {
                "fireflies_count": 99,
                "dragonflies_count": -5,
                "dandelions_count": "invalid"
            }
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(corrupted_data, f)

        # Reload settings
        s = Settings(config_path=self.config_path)
        self.assertEqual(s.get("overlays", "fireflies_count"), 6)
        self.assertEqual(s.get("overlays", "dragonflies_count"), 2)
        self.assertEqual(s.get("overlays", "dandelions_count"), 3)

    def test_control_center_pin_persistence(self):
        cc = ControlCenter(config=self.settings)
        self.assertFalse(cc.is_pinned())

        cc.pin_btn.setChecked(True)
        self.assertTrue(self.settings.get("control_center", "pinned"))

    def test_welcome_guide_got_it(self):
        self.assertFalse(self.settings.get("onboarding", "welcome_completed"))
        guide = WelcomeGuide(config=self.settings)
        guide._on_got_it()
        self.assertTrue(self.settings.get("onboarding", "welcome_completed"))

    def test_individual_size_toggles(self):
        cc = ControlCenter(config=self.settings)
        # Select "Small" for dragonflies
        for btn in cc._species_widgets["dragonflies"]["size_group"].buttons():
            if btn.property("scaleValue") == 0.5:
                btn.setChecked(True)
                break
        self.assertEqual(self.settings.get("overlays", "dragonflies_scale"), 0.5)
        # Check that fireflies remain 1.0
        self.assertEqual(self.settings.get("overlays", "fireflies_scale"), 1.0)


if __name__ == '__main__':
    unittest.main()
