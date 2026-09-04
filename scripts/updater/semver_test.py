import unittest

from scripts.updater.semver import SemVer, latest_matching_tag


class SemVerTest(unittest.TestCase):
    def test_orders_numeric_components(self) -> None:
        self.assertGreater(SemVer.parse("v1.10.0"), SemVer.parse("v1.9.9"))

    def test_rejects_non_stable_versions(self) -> None:
        for tag in ("latest", "v1.2", "v1.2.3-rc.1", "v01.2.3"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                SemVer.parse(tag)

    def test_selects_latest_tag_allowed_by_project_policy(self) -> None:
        self.assertEqual(
            latest_matching_tag(
                ["nightly", "v2.0.0-rc.1", "v1.9.0", "v2.0.0"],
                r"^v[0-9]+\.[0-9]+\.[0-9]+$",
            ),
            "v2.0.0",
        )

    def test_rejects_pattern_that_admits_no_stable_tag(self) -> None:
        with self.assertRaisesRegex(ValueError, "no stable SemVer tag"):
            latest_matching_tag(["nightly", "v1.0.0-rc.1"], r"^.*$")


if __name__ == "__main__":
    unittest.main()
