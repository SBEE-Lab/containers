import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.builder.build import _version_for_revision


def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


class BuildVersionTest(unittest.TestCase):
    def test_reads_calver_from_real_remote_tag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote = root / "remote.git"
            source = root / "source"
            git(root, "init", "--bare", str(remote))
            git(root, "clone", str(remote), str(source))
            git(source, "config", "user.name", "Test")
            git(source, "config", "user.email", "test@example.invalid")
            (source / "content").write_text("release")
            git(source, "add", "content")
            git(source, "commit", "-m", "release")
            revision = git(source, "rev-parse", "HEAD")
            git(
                source,
                "-c",
                "tag.gpgSign=false",
                "tag",
                "-a",
                "sbee-2026.09.15.1",
                "-m",
                "release",
            )
            git(source, "push", "origin", "HEAD", "refs/tags/sbee-2026.09.15.1")

            self.assertEqual(
                _version_for_revision(
                    source,
                    revision,
                    r"^sbee-[0-9]{4}\.[0-9]{2}\.[0-9]{2}\.[1-9][0-9]*$",
                    "sbee-calver",
                ),
                "2026.09.15.1",
            )


if __name__ == "__main__":
    unittest.main()
