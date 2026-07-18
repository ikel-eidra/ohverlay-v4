import os
import tempfile
import unittest
from config.settings import Settings

class TestSettings(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_no_shared_mutable_state(self):
        # Create two separate Settings instances using a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.json")
            
            s1 = Settings(config_path=config_path)
            s1.set("overlays", "fireflies", False)
            
            # Since s1 saved it, s2 will load it, so we need to test instance default isolation directly
            s2 = Settings(config_path=os.path.join(temp_dir, "config2.json"))
            
            s1.data["hotkeys"]["toggle_visibility"] = "ctrl+alt+z"
            
            self.assertNotEqual(
                s1.data["hotkeys"]["toggle_visibility"],
                s2.data["hotkeys"]["toggle_visibility"],
                "Settings instances share nested mutable state!"
            )
            
            self.assertEqual(
                s2.data["hotkeys"]["toggle_visibility"],
                "ctrl+alt+h",
                "Second instance default state was corrupted by first instance modification!"
            )

if __name__ == '__main__':
    unittest.main()
