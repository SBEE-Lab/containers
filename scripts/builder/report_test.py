import os
import tempfile
import unittest
from pathlib import Path

from scripts.builder.build import BuildResult, _record_summary


class SummaryTest(unittest.TestCase):
    def test_records_immutable_release_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            summary = Path(directory) / "summary.md"
            previous = os.environ.get("GITHUB_STEP_SUMMARY")
            os.environ["GITHUB_STEP_SUMMARY"] = str(summary)
            try:
                _record_summary(
                    BuildResult("sha256:" + "a" * 64, "b" * 40, "3.0.4"),
                    "registry.example/team/alphafold3",
                )
            finally:
                if previous is None:
                    del os.environ["GITHUB_STEP_SUMMARY"]
                else:
                    os.environ["GITHUB_STEP_SUMMARY"] = previous
            content = summary.read_text()
            self.assertIn("alphafold3:3.0.4", content)
            self.assertIn("sha256:" + "a" * 64, content)
            self.assertIn("SBOM: verified", content)
            self.assertIn("Provenance: verified", content)


if __name__ == "__main__":
    unittest.main()
