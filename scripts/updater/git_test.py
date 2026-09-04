import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.builder.build import _snapshot_revision
from scripts.builder.changed import changed_images
from scripts.updater import _git


def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


class SubmoduleRevisionTest(unittest.TestCase):
    def test_reads_checked_out_revision_before_gitlink_is_staged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            upstream = root / "upstream"
            superproject = root / "superproject"
            upstream.mkdir()
            superproject.mkdir()

            git(upstream, "init")
            git(upstream, "config", "user.name", "Test")
            git(upstream, "config", "user.email", "test@example.invalid")
            (upstream / "source").write_text("first")
            git(upstream, "add", "source")
            git(upstream, "commit", "-m", "first")
            first = git(upstream, "rev-parse", "HEAD")
            (upstream / "source").write_text("second")
            git(upstream, "commit", "-am", "second")
            second = git(upstream, "rev-parse", "HEAD")

            git(superproject, "init")
            git(superproject, "config", "user.name", "Test")
            git(superproject, "config", "user.email", "test@example.invalid")
            source = superproject / "images" / "example" / "src"
            git(
                superproject,
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                str(upstream),
                str(source.relative_to(superproject)),
            )
            git(source, "checkout", "--detach", first)
            git(superproject, "add", ".")
            git(superproject, "commit", "-m", "pin first")
            first_superproject = git(superproject, "rev-parse", "HEAD")

            git(source, "checkout", "--detach", second)

            self.assertEqual(_git.gitlink_revision(superproject, source), first)
            self.assertEqual(_git.revision(source), second)
            _root, _source, build_revision = _snapshot_revision(
                superproject / "images" / "example"
            )
            self.assertEqual(build_revision, first)

            git(superproject, "add", str(source.relative_to(superproject)))
            git(superproject, "commit", "-m", "pin second")
            second_superproject = git(superproject, "rev-parse", "HEAD")
            self.assertEqual(
                changed_images(superproject, first_superproject, second_superproject),
                ["example"],
            )


if __name__ == "__main__":
    unittest.main()
