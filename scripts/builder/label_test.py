import unittest

from scripts.builder.build import _label_arguments


class LabelTest(unittest.TestCase):
    def test_overrides_source_defaults_with_release_identity(self) -> None:
        self.assertEqual(
            _label_arguments("a" * 40, "2026.09.15.1"),
            [
                "--label",
                f"org.opencontainers.image.revision={'a' * 40}",
                "--label",
                "org.opencontainers.image.version=2026.09.15.1",
            ],
        )


if __name__ == "__main__":
    unittest.main()
