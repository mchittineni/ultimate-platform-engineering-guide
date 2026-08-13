#!/usr/bin/env python3
"""Write each question's strongest graph edges into its `## Related Questions` block.

The edges come from ``build_knowledge_graph.py`` - the same graph the HTML page is
rendered from - so the vault and the site never disagree about what is related to
what. Nothing here is hand-maintained: add a question, re-run, and its neighbours
appear on both sides.

The block is delimited by ``<!-- RELATED:START -->`` / ``<!-- RELATED:END -->`` and
regenerated in place, which makes the script idempotent and keeps hand-written prose
around it untouched. Links are relative paths so they resolve on GitHub, in an
editor, and in ``validate_content.py``; the ``[[wikilink]]`` form is kept alongside
for Obsidian-style vaults.

Usage:
    python3 scripts/inject_wikilinks.py           # write the blocks
    python3 scripts/inject_wikilinks.py --check   # report drift, write nothing (CI)
    python3 scripts/inject_wikilinks.py --strip   # remove every block

Exit codes: 0 = clean, 1 = drift found (--check only).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from build_knowledge_graph import MAX_EDGES_PER_NODE, build_graph, related_ids
from lib_content import REPO_ROOT, all_questions, load_topics, parse_frontmatter

MARKER = "RELATED"
START, END = f"<!-- {MARKER}:START -->", f"<!-- {MARKER}:END -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.DOTALL)

HEADING = "## Related Questions"

# The footer rule of a question file: a `---` alone on its line, inside the body.
# Matching the body rather than the whole file matters - a bare search would hit
# the frontmatter's closing delimiter and inject the block into the header.
FOOTER_RULE_RE = re.compile(r"^---[ \t]*$", re.M)


def render_block(question, neighbours) -> str:
    """The managed block for one question: heading, wikilinks, and relative links."""
    lines = [START, "", HEADING, ""]
    for target, shared in neighbours:
        rel = f"../{target['topic']}/{Path(target['path']).name}"
        why = f" - shares {', '.join(shared)}" if shared else ""
        lines.append(f"- [[{target['title']}]] · [{target['title']}]({rel}){why}")
    lines += ["", END, ""]
    return "\n".join(lines)


def neighbours_for(graph: dict, node_id: int, limit: int) -> list[tuple[dict, list[str]]]:
    """Neighbour nodes plus the concepts that earned each link, in wikilink order."""
    by_id = {n["id"]: n for n in graph["nodes"]}
    shared_by_pair = {
        (min(e["s"], e["t"]), max(e["s"], e["t"])): e["c"] for e in graph["edges"]
    }
    out = []
    for other in related_ids(graph, node_id, limit):
        key = (min(node_id, other), max(node_id, other))
        out.append((by_id[other], shared_by_pair.get(key, [])))
    return out


def apply_block(content: str, block: str) -> str:
    """Insert or replace the managed block, always above the file's footer rule."""
    if BLOCK_RE.search(content):
        return BLOCK_RE.sub(lambda _: block, content, count=1)

    _, body = parse_frontmatter(content)
    offset = len(content) - len(body)
    footer = FOOTER_RULE_RE.search(body)
    if footer:
        cut = offset + footer.start()
        return content[:cut] + block + "\n" + content[cut:]
    return content.rstrip() + "\n\n" + block


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    parser.add_argument("--strip", action="store_true", help="remove every managed block")
    parser.add_argument(
        "--limit", type=int, default=MAX_EDGES_PER_NODE,
        help=f"links per question (default: {MAX_EDGES_PER_NODE})",
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="print the summary only")
    args = parser.parse_args()

    topics = load_topics()
    questions = [q for q in all_questions(topics) if q.id > 0]

    if args.strip:
        removed = 0
        for q in questions:
            content = q.path.read_text(encoding="utf-8")
            stripped = BLOCK_RE.sub("", content)
            if stripped != content:
                q.path.write_text(stripped, encoding="utf-8")
                removed += 1
        print(f"removed the related-questions block from {removed} file(s)")
        return 0

    graph = build_graph(topics)
    changed: list[Path] = []
    isolated: list[str] = []

    for q in questions:
        neighbours = neighbours_for(graph, q.id, args.limit)
        content = q.path.read_text(encoding="utf-8")
        if not neighbours:
            isolated.append(q.title)
            # An unlinked question should not keep a stale block from a previous run.
            updated = BLOCK_RE.sub("", content)
        else:
            updated = apply_block(content, render_block(q, neighbours))
        if updated == content:
            continue
        changed.append(q.path)
        if not args.check:
            q.path.write_text(updated, encoding="utf-8")

    if not args.quiet:
        for path in changed:
            print(f"  {'stale' if args.check else 'wrote'}: {path.relative_to(REPO_ROOT)}")
        if isolated:
            print(f"  {len(isolated)} question(s) have no strong link yet:")
            for title in isolated:
                print(f"    - {title}")

    if args.check:
        if changed:
            print(
                f"\n{len(changed)} file(s) have a stale related-questions block - "
                "run `python3 scripts/inject_wikilinks.py`",
                file=sys.stderr,
            )
            return 1
        print(f"Related-questions blocks are current across {len(questions)} question files.")
        return 0

    print(f"Updated {len(changed)} of {len(questions)} question files ({graph['meta']['edges']} graph edges).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
