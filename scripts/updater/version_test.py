import unittest

from scripts.updater.version import latest_matching_version


class VersionPolicyTest(unittest.TestCase):
    def test_selects_and_normalizes_calver(self) -> None:
        self.assertEqual(
            latest_matching_version(
                ["v3.0.4", "sbee-2026.09.15.1", "sbee-2026.09.15.2"],
                r"^sbee-[0-9]{4}\.[0-9]{2}\.[0-9]{2}\.[1-9][0-9]*$",
                "sbee-calver",
            ),
            ("sbee-2026.09.15.2", "2026.09.15.2"),
        )

    def test_preserves_stable_semver_behavior(self) -> None:
        self.assertEqual(
            latest_matching_version(
                ["nightly", "v1.9.0", "v2.0.0"],
                r"^v[0-9]+\.[0-9]+\.[0-9]+$",
                "semver",
            ),
            ("v2.0.0", "2.0.0"),
        )

    def test_rejects_unknown_scheme(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown version scheme"):
            latest_matching_version(["v1.0.0"], r".*", "unknown")


if __name__ == "__main__":
    unittest.main()
