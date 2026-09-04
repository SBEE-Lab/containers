import unittest

from scripts.builder.build import _registry_cache_arguments


class RegistryCacheTest(unittest.TestCase):
    def test_uses_separate_max_mode_cache_image(self) -> None:
        self.assertEqual(
            _registry_cache_arguments("registry.example/team/image"),
            [
                "--cache-from",
                "type=registry,ref=registry.example/team/image-cache:buildkit",
                "--cache-to",
                "type=registry,ref=registry.example/team/image-cache:buildkit,mode=max,image-manifest=true,oci-mediatypes=true",
            ],
        )


if __name__ == "__main__":
    unittest.main()
