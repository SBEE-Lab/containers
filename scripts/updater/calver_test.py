import unittest

from scripts.updater.calver import CalVer


class CalVerTest(unittest.TestCase):
    def test_normalizes_curated_source_tag(self) -> None:
        self.assertEqual(str(CalVer.parse("sbee-2026.09.15.1")), "2026.09.15.1")

    def test_orders_date_before_daily_sequence(self) -> None:
        self.assertGreater(
            CalVer.parse("sbee-2026.09.16.1"),
            CalVer.parse("sbee-2026.09.15.20"),
        )
        self.assertGreater(
            CalVer.parse("sbee-2026.09.15.2"),
            CalVer.parse("sbee-2026.09.15.1"),
        )

    def test_rejects_invalid_or_ambiguous_tags(self) -> None:
        for tag in (
            "2026.09.15.1",
            "sbee-2026.9.15.1",
            "sbee-2026.02.30.1",
            "sbee-2026.09.15.0",
            "sbee-2026.09.15.01",
        ):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                CalVer.parse(tag)


if __name__ == "__main__":
    unittest.main()
