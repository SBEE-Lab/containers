import tempfile
import unittest
from pathlib import Path

from scripts.updater.run import discover


class DiscoverTest(unittest.TestCase):
    def test_discovers_only_complete_image_updaters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            complete = root / "images" / "complete"
            incomplete = root / "images" / "incomplete"
            complete.mkdir(parents=True)
            incomplete.mkdir(parents=True)
            (complete / "src").mkdir()
            (complete / "update.py").touch()
            (incomplete / "update.py").touch()
            self.assertEqual(discover(root), [complete])


if __name__ == "__main__":
    unittest.main()
