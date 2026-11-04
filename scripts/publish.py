#!/usr/bin/env python3
"""Publish posts from an Obsidian vault into src/content/posts/.

Usage:
    python scripts/publish.py /path/to/vault [--dry-run] [--prune] [--out DIR]

The vault path must contain a .obsidian folder (every Obsidian vault has
one) — the script refuses to run otherwise, so it can't be pointed at the
wrong directory.

Copies every Markdown file in the vault whose frontmatter has `public: true`
into src/content/posts/, converting it to the site's format:

  frontmatter   vault `created` -> `date`; vault `type` (or `domain`) -> post
                type via TYPE_MAP below; `title`, `summary`, `link`, `tags`
                kept; every other key dropped.
  [[wikilinks]] rewritten to a normal link (/writing/<slug>/) when the target
                note is also public, otherwise to plain text. Embeds
                (![[file]]) are removed.
  callouts      `> [!note]` / `> [!note]-` blockquote blocks are stripped.

Every generated post carries a `source: vault` frontmatter line (ignored by
the site build) marking it as script-managed. With --prune, any post in the
output directory that has that marker but whose vault note is no longer
`public: true` is deleted; hand-written posts (no marker) are never touched.

The script is idempotent: output filenames are slugified from the vault
filename, files are only rewritten when their content changed, and nothing
in the vault is modified.

Uses PyYAML for frontmatter when installed; otherwise falls back to a small
built-in parser that covers normal Obsidian frontmatter (strings, numbers,
booleans, dates, inline and block lists).
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = REPO_ROOT / "src" / "content" / "posts"

# Vault `type`/`domain` value (lowercased) -> site post type.
# Extend this table as the vault grows new domains.
TYPE_MAP = {
    "paper": "paper",
    "papers": "paper",
    "research": "paper",
    "literature": "paper",
    "company": "company",
    "companies": "company",
    "startup": "company",
    "startups": "company",
    "investing": "company",
}

SUMMARY_MAX = 200


# --- frontmatter parsing ----------------------------------------------------

def _mini_yaml(text: str) -> dict:
    """Tolerant parser for simple Obsidian frontmatter (no PyYAML needed)."""
    data: dict = {}
    key = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if re.match(r"^\s*-\s+", raw) and key is not None:
            data.setdefault(key, [])
            if isinstance(data[key], list):
                data[key].append(_scalar(re.sub(r"^\s*-\s+", "", raw).strip()))
            continue
        m = re.match(r"^([A-Za-z0-9_:\- ]+?):\s*(.*)$", raw)
        if not m:
            continue
        key, value = m.group(1).strip(), m.group(2).strip()
        if value == "":
            data[key] = None  # may be a block list; filled by "- item" lines
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [_scalar(v.strip()) for v in inner.split(",")] if inner else []
        else:
            data[key] = _scalar(value)
    return data


def _scalar(value: str):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    if value.lower() in ("true", "yes"):
        return True
    if value.lower() in ("false", "no"):
        return False
    return value


try:
    import yaml  # type: ignore

    def load_frontmatter(text: str) -> dict:
        return yaml.safe_load(text) or {}
except ImportError:

    def load_frontmatter(text: str) -> dict:
        return _mini_yaml(text)


def split_frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if not m:
        return {}, text
    return load_frontmatter(m.group(1)), text[m.end():]


# --- conversion helpers -------------------------------------------------------

def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "untitled"


def as_date(value) -> str | None:
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, str):
        m = re.match(r"(\d{4}-\d{2}-\d{2})", value.strip())
        if m:
            return m.group(1)
    return None


def as_tags(value) -> list[str]:
    if isinstance(value, list):
        return [str(t).lstrip("#") for t in value if str(t).strip()]
    if isinstance(value, str):
        return [t.strip().lstrip("#") for t in value.split(",") if t.strip()]
    return []


def strip_note_callouts(body: str) -> str:
    """Remove `> [!note]` / `> [!note]-` blockquote blocks."""
    out: list[str] = []
    skipping = False
    for line in body.splitlines():
        if re.match(r"^\s*>\s*\[!note\]-?", line, re.IGNORECASE):
            skipping = True
            continue
        if skipping:
            if line.lstrip().startswith(">"):
                continue
            skipping = False
        out.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out))


WIKILINK = re.compile(r"(!?)\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]")


def rewrite_wikilinks(body: str, public_slugs: dict[str, str]) -> str:
    def repl(m: re.Match) -> str:
        embed, target, alias = m.group(1), m.group(2).strip(), m.group(3)
        if embed:
            return ""  # drop embedded files/images
        stem = Path(target).stem
        display = (alias or stem).strip()
        slug = public_slugs.get(stem.lower())
        if slug:
            return f"[{display}](/writing/{slug}/)"
        return display

    return WIKILINK.sub(repl, body)


def first_paragraph(body: str) -> str:
    for block in re.split(r"\n\s*\n", body):
        text = block.strip()
        if not text or text.startswith(("#", ">", "-", "*", "|", "```", "![")):
            continue
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links -> text
        text = re.sub(r"[*_`]", "", text)
        text = " ".join(text.split())
        if len(text) > SUMMARY_MAX:
            text = text[: SUMMARY_MAX - 1].rstrip() + "…"
        return text
    return ""


def yaml_quote(value: str) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


# --- main ---------------------------------------------------------------------

def collect_public_notes(vault: Path) -> list[tuple[Path, dict, str]]:
    notes = []
    for path in sorted(vault.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(vault).parts):
            continue  # skip .obsidian, .trash, ...
        fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
        if isinstance(fm, dict) and fm.get("public") is True:
            notes.append((path, fm, body))
    return notes


def convert(path: Path, fm: dict, body: str, public_slugs: dict[str, str],
            warn) -> str | None:
    raw_type = str(fm.get("type") or fm.get("domain") or "").strip().lower()
    post_type = TYPE_MAP.get(raw_type)
    if not post_type:
        warn(f"{path.name}: type/domain {raw_type!r} not in TYPE_MAP - skipped")
        return None

    date = as_date(fm.get("created")) or as_date(fm.get("date"))
    if not date:
        date = dt.date.fromtimestamp(path.stat().st_mtime).isoformat()
        warn(f"{path.name}: no created/date in frontmatter - using file mtime {date}")

    title = str(fm.get("title") or path.stem)

    body = strip_note_callouts(body)
    body = rewrite_wikilinks(body, public_slugs)

    summary = str(fm.get("summary") or fm.get("description") or "").strip()
    if not summary:
        summary = first_paragraph(body)
        if summary:
            warn(f"{path.name}: no summary in frontmatter - using first paragraph")
        else:
            summary = title
            warn(f"{path.name}: no summary or body paragraph - using title")

    lines = [
        "---",
        f"title: {yaml_quote(title)}",
        f"date: {date}",
        f"type: {post_type}",
        f"summary: {yaml_quote(summary)}",
    ]
    link = fm.get("link") or fm.get("url")
    if link:
        lines.append(f"link: {link}")
    tags = as_tags(fm.get("tags"))
    if tags:
        lines.append("tags: [" + ", ".join(tags) + "]")
    lines.append("source: vault")  # marks the post as managed by this script
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body.strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("vault", type=Path, help="path to the Obsidian vault")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change without writing anything")
    ap.add_argument("--prune", action="store_true",
                    help="delete script-generated posts (source: vault) whose "
                         "vault note is no longer public: true")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT,
                    help="output directory (default: src/content/posts)")
    args = ap.parse_args(argv)

    if not args.vault.is_dir():
        print(f"error: {args.vault} is not a directory", file=sys.stderr)
        return 2
    if not (args.vault / ".obsidian").is_dir():
        print(f"error: {args.vault} contains no .obsidian folder - "
              "is this really an Obsidian vault?", file=sys.stderr)
        return 2

    def warn(msg: str) -> None:
        print(f"  warning: {msg}")

    notes = collect_public_notes(args.vault)
    public_slugs = {path.stem.lower(): slugify(path.stem) for path, _, _ in notes}

    written = unchanged = skipped = 0
    for path, fm, body in notes:
        output = convert(path, fm, body, public_slugs, warn)
        if output is None:
            skipped += 1
            continue
        dest = args.out / (slugify(path.stem) + ".md")
        if dest.exists() and dest.read_text(encoding="utf-8") == output:
            print(f"unchanged  {dest.name}")
            unchanged += 1
            continue
        if args.dry_run:
            print(f"would write  {dest.name}  (from {path.relative_to(args.vault)})")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(output, encoding="utf-8")
            print(f"wrote      {dest.name}  (from {path.relative_to(args.vault)})")
        written += 1

    removed = 0
    if args.prune:
        keep = set(public_slugs.values())
        for dest in sorted(args.out.glob("*.md")) if args.out.is_dir() else []:
            dest_fm, _ = split_frontmatter(dest.read_text(encoding="utf-8"))
            if not (isinstance(dest_fm, dict) and dest_fm.get("source") == "vault"):
                continue  # hand-written post - never touched
            if dest.stem in keep:
                continue  # vault note still public
            if args.dry_run:
                print(f"would remove  {dest.name}  (vault note no longer public)")
            else:
                dest.unlink()
                print(f"removed    {dest.name}  (vault note no longer public)")
            removed += 1

    print(f"{'(dry run) ' if args.dry_run else ''}"
          f"{written} written, {unchanged} unchanged, {skipped} skipped, "
          f"{f'{removed} removed, ' if args.prune else ''}"
          f"{len(notes)} public note(s) found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
