import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.builder.build import _require_unpublished


class PublishPreflightTest(unittest.TestCase):
    def run_skopeo(self, exit_code: int, error: str) -> Exception | None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "skopeo"
            executable.write_text(
                f"#!/bin/sh\nprintf '%s' '{error}' >&2\nexit {exit_code}\n"
            )
            executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
            previous = os.environ["PATH"]
            os.environ["PATH"] = f"{directory}:{previous}"
            try:
                try:
                    _require_unpublished("registry.example/image:1.0.0")
                except (ValueError, subprocess.CalledProcessError) as error_result:
                    return error_result
                return None
            finally:
                os.environ["PATH"] = previous

    def test_rejects_existing_tag(self) -> None:
        self.assertIsInstance(self.run_skopeo(0, ""), ValueError)

    def test_allows_only_missing_manifest(self) -> None:
        self.assertIsNone(self.run_skopeo(1, "manifest unknown"))

    def test_propagates_registry_failure(self) -> None:
        error = self.run_skopeo(1, "unauthorized")
        self.assertIsNotNone(error)
        self.assertNotIsInstance(error, ValueError)


if __name__ == "__main__":
    unittest.main()
