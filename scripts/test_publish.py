"""Tests for scripts/publish.py against the fixture vault.

Run with either of:
    python scripts/test_publish.py
    python -m unittest discover scripts
"""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
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
        self.assertIn("source: vault", fm)            # script-managed marker
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

    STALE = ('---\ntitle: "Old"\ndate: 2026-01-01\ntype: paper\n'
             'summary: "Stale"\nsource: vault\n---\n\nOld body.\n')
    HANDWRITTEN = ('---\ntitle: "Mine"\ndate: 2026-01-01\ntype: paper\n'
                   'summary: "Hand-written"\n---\n\nMy body.\n')

    def test_prune_removes_stale_generated_posts(self):
        run(self.out)
        stale = self.out / "old-note.md"
        stale.write_text(self.STALE)
        handwritten = self.out / "handwritten.md"
        handwritten.write_text(self.HANDWRITTEN)
        output = run(self.out, "--prune")
        self.assertFalse(stale.exists())            # marker + gone from vault
        self.assertTrue(handwritten.exists())       # no marker - never touched
        self.assertTrue((self.out / "gears-notes.md").exists())  # still public
        self.assertTrue((self.out / "deep-dive.md").exists())
        self.assertIn("removed    old-note.md", output)
        self.assertIn("1 removed", output)

    def test_prune_dry_run_deletes_nothing(self):
        run(self.out)
        stale = self.out / "old-note.md"
        stale.write_text(self.STALE)
        output = run(self.out, "--prune", "--dry-run")
        self.assertTrue(stale.exists())
        self.assertIn("would remove  old-note.md", output)

    def test_refuses_directory_without_obsidian_folder(self):
        with tempfile.TemporaryDirectory() as not_a_vault:
            (Path(not_a_vault) / "note.md").write_text("---\npublic: true\n---\nhi\n")
            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                code = publish.main([not_a_vault, "--out", str(self.out)])
            self.assertEqual(code, 2)
            self.assertIn(".obsidian", stderr.getvalue())
            self.assertEqual(list(self.out.glob("*.md")), [])


if __name__ == "__main__":
    unittest.main()
