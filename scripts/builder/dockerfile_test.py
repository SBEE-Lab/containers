import tempfile
import unittest
from pathlib import Path

from scripts.builder.build import _derive_dockerfile


class DerivedDockerfileTest(unittest.TestCase):
    def test_declares_build_arguments_without_changing_source(self) -> None:
        source_text = "# syntax=docker/dockerfile:1\nFROM example AS build\nRUN tool\n"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Dockerfile"
            destination = Path(directory) / "Derivedfile"
            source.write_text(source_text)

            _derive_dockerfile(source, destination, ["UV_HTTP_TIMEOUT"])

            self.assertEqual(source.read_text(), source_text)
            self.assertEqual(
                destination.read_text(),
                "# syntax=docker/dockerfile:1\n"
                "FROM example AS build\n"
                "ARG UV_HTTP_TIMEOUT\n"
                "RUN tool\n",
            )

    def test_declares_arguments_in_each_stage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Dockerfile"
            destination = Path(directory) / "Derivedfile"
            source.write_text("FROM one\nFROM two\n")

            _derive_dockerfile(source, destination, ["NETWORK_TIMEOUT"])

            self.assertEqual(
                destination.read_text(),
                "FROM one\nARG NETWORK_TIMEOUT\nFROM two\nARG NETWORK_TIMEOUT\n",
            )

    def test_rejects_invalid_argument_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Dockerfile"
            source.write_text("FROM example\n")
            with self.assertRaisesRegex(ValueError, "invalid build argument"):
                _derive_dockerfile(source, Path(directory) / "out", ["BAD-NAME"])


if __name__ == "__main__":
    unittest.main()
