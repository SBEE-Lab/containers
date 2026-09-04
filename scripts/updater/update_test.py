import unittest

from scripts._git_tags import parse


class RemoteTagsTest(unittest.TestCase):
    def test_prefers_peeled_commit_for_annotated_tag(self) -> None:
        tag_object = "a" * 40
        commit = "b" * 40
        self.assertEqual(
            parse(
                [
                    f"{tag_object}\trefs/tags/v1.2.3",
                    f"{commit}\trefs/tags/v1.2.3^{{}}",
                ]
            ),
            {"v1.2.3": commit},
        )


if __name__ == "__main__":
    unittest.main()
