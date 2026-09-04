import json
import tempfile
import unittest
from pathlib import Path

from scripts.builder._metadata import read_image_digest


class MetadataTest(unittest.TestCase):
    def test_reads_buildx_image_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.json"
            path.write_text(json.dumps({"containerimage.digest": "sha256:" + "a" * 64}))
            self.assertEqual(read_image_digest(path), "sha256:" + "a" * 64)

    def test_rejects_missing_or_invalid_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.json"
            for metadata in ({}, {"containerimage.digest": "latest"}):
                path.write_text(json.dumps(metadata))
                with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                    read_image_digest(path)


if __name__ == "__main__":
    unittest.main()
