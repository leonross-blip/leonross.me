"""Tests for scripts/publish.py against the fixture vault.

Run with either of:
    python scripts/test_publish.py
    python -m unittest discover scripts
"""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import publish

FIXTURE_VAULT = Path(__file__).resolve().parent / "tests" / "fixtures" / "vault"


def run(out_dir: Path, *extra: str) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = publish.main([str(FIXTURE_VAULT), "--out", str(out_dir), *extra])
    assert code == 0, buf.getvalue()
    return buf.getvalue()


class PublishTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_publishes_only_public_notes(self):
        run(self.out)
        names = sorted(p.name for p in self.out.glob("*.md"))
        self.assertEqual(names, ["deep-dive.md", "gears-notes.md"])

    def test_frontmatter_mapping(self):
        run(self.out)
        text = (self.out / "gears-notes.md").read_text()
        fm = text.split("---")[1]
        self.assertIn('title: "GEARS and what it actually shows"', fm)
        self.assertIn("date: 2026-05-14", fm)          # created -> date
        self.assertIn("type: paper", fm)               # domain -> type
        self.assertIn("tags: [perturbation, single-cell]", fm)
        self.assertIn("link: https://doi.org/10.1038/s41587-023-01905-6", fm)
        for dropped in ("status", "up", "obsidian_vault", "public", "created", "domain"):
            self.assertNotRegex(fm, rf"(?m)^{dropped}:")
        # type -> type mapping via TYPE_MAP (startup -> company)
        self.assertIn("type: company", (self.out / "deep-dive.md").read_text())

    def test_wikilinks(self):
        run(self.out)
        body = (self.out / "gears-notes.md").read_text()
        # public target -> site URL, alias kept
        self.assertIn("[the Recursion deep dive](/writing/deep-dive/)", body)
        # non-public target -> plain text
        self.assertIn("and Private Note for raw thoughts", body)
        self.assertNotIn("[[", body)
        # embeds dropped
        self.assertNotIn("gears-fig2.png", body)

    def test_callout_stripped(self):
        run(self.out)
        body = (self.out / "gears-notes.md").read_text()
        self.assertNotIn("[!note]", body)
        self.assertNotIn("vault-only scaffolding", body)
        self.assertIn("## Method in plain words", body)  # content after survives

    def test_idempotent(self):
        run(self.out)
        first = {p.name: p.read_text() for p in self.out.glob("*.md")}
        output = run(self.out)
        second = {p.name: p.read_text() for p in self.out.glob("*.md")}
        self.assertEqual(first, second)
        self.assertIn("0 written, 2 unchanged", output)

    def test_dry_run_writes_nothing(self):
        output = run(self.out, "--dry-run")
        self.assertEqual(list(self.out.glob("*.md")), [])
        self.assertIn("would write", output)


if __name__ == "__main__":
    unittest.main()
