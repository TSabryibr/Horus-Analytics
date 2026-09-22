import unittest
import os
import json
import tempfile
import shutil

# We anticipate the module creation
# from managers.ExclusionManager import ExclusionManager

class TestExclusionManager(unittest.TestCase):
    def setUp(self):
        # Create a temp directory
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_exclusions.json")
        
        # Hardcoded exclusions for testing
        self.hardcoded = {"HARD_1", "HARD_2"}
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
        
    def test_initialization(self):
        """Test that manager initializes with hardcoded and file path."""
        # We will import inside test to allow running this before module exists (Red phase)
        try:
            from managers.ExclusionManager import ExclusionManager
        except ImportError:
            self.fail("ExclusionManager module not implemented yet (RED PHASE SUCCESS)")

        manager = ExclusionManager(self.hardcoded, self.test_file)
        self.assertEqual(manager.get_all(), self.hardcoded)
        
    def test_add_persistence(self):
        """Test adding exclusion updates memory and file."""
        from managers.ExclusionManager import ExclusionManager
        manager = ExclusionManager(self.hardcoded, self.test_file)
        
        manager.add("NEW_1")
        
        # Check memory
        expected = self.hardcoded.union({"NEW_1"})
        self.assertEqual(manager.get_all(), expected)
        
        # Check file
        with open(self.test_file, 'r') as f:
            data = json.load(f)
            self.assertIn("NEW_1", data)
            
    def test_remove_dynamic(self):
        """Test removing dynamic exclusion."""
        from managers.ExclusionManager import ExclusionManager
        manager = ExclusionManager(self.hardcoded, self.test_file)
        
        manager.add("TEMP_1")
        self.assertIn("TEMP_1", manager.get_all())
        
        manager.remove("TEMP_1")
        self.assertNotIn("TEMP_1", manager.get_all())
        
    def test_remove_hardcoded_fail(self):
        """Test removing hardcoded exclusion returns False/fails."""
        from managers.ExclusionManager import ExclusionManager
        manager = ExclusionManager(self.hardcoded, self.test_file)
        
        result = manager.remove("HARD_1")
        self.assertFalse(result)
        self.assertIn("HARD_1", manager.get_all())

if __name__ == "__main__":
    unittest.main()
