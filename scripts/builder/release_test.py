import json
import tempfile
import unittest
from pathlib import Path

from scripts.builder.release import (
    ImageRelease,
    load_build_release,
    load_registry_release,
)


class ReleaseManifestTest(unittest.TestCase):
    def test_loads_build_result_as_immutable_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "multievolve.json"
            path.write_text(
                json.dumps(
                    {
                        "image": "registry.example/team/multievolve",
                        "digest": "sha256:" + "a" * 64,
                        "revision": "b" * 40,
                        "version": "2026.09.15.1",
                    }
                )
            )
            release = load_build_release(path)
            self.assertEqual(release.tag, "multievolve-2026.09.15.1")
            self.assertEqual(
                release.reference,
                "registry.example/team/multievolve@sha256:" + "a" * 64,
            )

    def test_loads_registry_inspection_for_backfill(self) -> None:
        release = load_registry_release(
            "registry.example/team/alphafold3",
            "3.0.4",
            {
                "Name": "registry.example/team/alphafold3",
                "Digest": "sha256:" + "c" * 64,
                "Labels": {
                    "org.opencontainers.image.revision": "d" * 40,
                    "org.opencontainers.image.version": "3.0.4",
                },
            },
        )
        self.assertEqual(
            release,
            ImageRelease(
                image="registry.example/team/alphafold3",
                version="3.0.4",
                digest="sha256:" + "c" * 64,
                revision="d" * 40,
            ),
        )

    def test_rejects_registry_version_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "version label"):
            load_registry_release(
                "registry.example/team/alphafold3",
                "3.0.4",
                {
                    "Name": "registry.example/team/alphafold3",
                    "Digest": "sha256:" + "c" * 64,
                    "Labels": {
                        "org.opencontainers.image.revision": "d" * 40,
                        "org.opencontainers.image.version": "3.0.3",
                    },
                },
            )


if __name__ == "__main__":
    unittest.main()
