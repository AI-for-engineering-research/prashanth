#!/usr/bin/env python3
"""slop_lint.py — deterministic scan for AI-slop vocabulary and stale relative references.

This is the cheap first stage of the `cold-read` skill. It does NOT rewrite anything;
it finds the offenses a cold reader would trip over so a rewrite pass (or a human) can fix them.

Three classes of finding:
  HARD  — slop vocabulary that is almost never right in a published technical artifact
          ("honest comparison", "clearly", "delve", "seamless"). Treat as must-fix.
  SOFT  — jargon / hedges with legitimate technical uses ("gate", "robust", "just").
          Review each; keep the real ones, cut the filler.
  STALE — relative / temporal references that only make sense to someone who watched the
          artifact being edited ("the 4% I claimed earlier", "is now fixed", "as requested").
          These are the references that read as nonsense to a cold reader days later.

Code is never linted: <pre>/<code>/<script>/<style> in HTML and fenced/inline code in Markdown
are blanked out first (offsets preserved), because verbatim source excerpts are untouchable.

Usage:
  slop_lint.py FILE [FILE ...]          scan one or more files
  slop_lint.py --list                   print the lexicon and exit
  slop_lint.py --json FILE [...]        machine-readable output (for the rewrite agent)
  slop_lint.py --extra WORDS.txt FILE   add project/personal banned regexes (one per line,
                                        '#' comments allowed). A file named personal-bans.txt
                                        next to this script is loaded automatically if present.

Exit code: 0 if no HARD findings, 1 if any HARD finding (so it can gate a pipeline).
"""

import argparse
import json
import os
import re
import sys

# --- Lexicon -----------------------------------------------------------------------------
# Each entry is (label, pattern). Patterns are matched case-insensitively with \b word
# boundaries already baked in below; use \s+ between words so line breaks don't hide a phrase.
# This script is the source of truth for the lexicon — `--list` dumps it, and the human-facing
# references/slop-lexicon.md explains the rationale.

HARD = [
    # "honest" in all its forms — honesty is assumed in technical work; asserting it signals the opposite
    ("honest/honestly", r"honest(ly|y)?"),
    ("dishonest", r"dishonest(ly|y)?"),
    ("to be honest", r"to be honest|in all honesty|honest truth"),
    # rhetorical certainty — replace with the evidence, not the adverb
    ("clearly/obviously", r"clearly|obviously|evidently|undeniably|undoubtedly|unequivocally|plainly"),
    ("definitive/decisive", r"definitive(ly)?|decisive(ly)?|conclusive(ly)?"),
    ("emphasis filler", r"basically|truly|genuinely|fundamentally|essentially|literally|absolutely|certainly|surely"),
    # meta-narration about the text itself
    ("worth-noting filler", r"it'?s worth (noting|mentioning)|it should be (noted|mentioned)|"
                            r"it is (important|worth) (to note|noting|mentioning)|"
                            r"needless to say|it goes without saying|notably|of note"),
    # marketing / LLM-house-style
    ("hype adjective", r"seamless(ly)?|effortless(ly)?|cutting-edge|state-of-the-art|"
                       r"best-in-class|world-class|first-class|game-?changer|"
                       r"powerful|revolutionary|groundbreaking|unparalleled|next-level"),
    ("hype verb", r"delv(e|ing|es)|unlock(s|ing)?|supercharg(e|es|ing)|elevat(e|es|ing)|"
                  r"harness(es|ing)?|empower(s|ing|ed)?|unleash(es|ing)?"),
    ("essay cliche", r"tapestry|testament to|in today'?s (world|landscape|fast-paced)|"
                     r"ever-(evolving|changing)|fast-paced|navigat(e|ing) the (complex|landscape)|"
                     r"the realm of|when it comes to|at the end of the day"),
]

SOFT = [
    # legitimate in the right place; flag so a human keeps only the load-bearing ones
    ("minimizer", r"just|simply|merely|only just|quite|very|really|fairly|somewhat|rather"),
    ("vague-positive", r"robust(ly|ness)?|powerful|elegant|clean|nice|neat|smart|intuitive|"
                       r"straightforward|trivial(ly)?|easy|simple"),
    ("vague-leverage", r"leverag(e|es|ing|ed)|utiliz(e|es|ing|ed)|facilitat(e|es|ing|ed)"),
    ("pm-jargon", r"\bgate\b|\btier\b|long pole|north star|smoking gun|fan[- ]?out|"
                  r"low-hanging fruit|move the needle|circle back|double-click|boil the ocean|"
                  r"deep dive|drill down|table stakes|wheelhouse"),
    ("hedge", r"of course|arguably|presumably|in some sense|to some extent|more or less|"
              r"sort of|kind of|i think|i believe|perhaps|maybe|possibly"),
]

# STALE — the relative/temporal references that break for a cold reader. These are the
# Problem-2 detector. Almost all are worth flagging even though a few have innocent uses.
STALE = [
    ("temporal-backref", r"earlier|previously|formerly|above|below|"
                         r"as (mentioned|noted|discussed|stated|said|described|shown|explained)|"
                         r"as (i|we) (mentioned|noted|said|stated|claimed|discussed)|"
                         r"(mentioned|noted|stated|discussed) (above|earlier|previously|before)"),
    ("authored-claim", r"\b(i|we) (claim(ed)?|said|stated|mentioned|reported|wrote|noted|"
                       r"argued|assumed|estimated|guessed|thought|"
                       r"updated|changed|revised|fixed|corrected|added|removed|renamed)\b|"
                       r"my (earlier|previous|original|initial) (claim|estimate|number|figure|statement)"),
    ("correction", r"(is|was|were|are|been|being|now)\s+(in)?correct|"
                   r"(is|was|were|has been|have been|been|now)\s+(fixed|corrected|resolved|patched)|"
                   r"the\s+fix\b|(was|were|is|are)\s+wrong|"
                   r"(my|the)\s+(mistake|error|oversight)|to correct|correction"),
    ("now-contrast", r"\bnow\s+(shows?|correctly|properly|fixed|displays?|includes?|hidden|"
                     r"visible|shown|reflects?|matches?)|"
                     r"no longer|used to|previously (was|did|had)|"
                     r"instead of (the|what)|rather than (the|what|before)|"
                     r"changed (from|to)|updated (to|from)|revised (to|from)|"
                     r"this (version|time|iteration)|the (previous|last|prior) (version|run|pass|time)"),
    ("conversation-leak", r"as (requested|asked|you wanted|you asked|per your)|"
                          r"per your (request|ask|comment|feedback)|you (asked|wanted|requested|mentioned)|"
                          r"hope (this|that) helps|let me know|feel free|"
                          r"here'?s the (updated|revised|fixed|new)|let me\b|i'?ll (now|go ahead)|"
                          r"as (per )?(our|the) (chat|conversation|discussion)"),
]

CLASSES = [("HARD", HARD), ("SOFT", SOFT), ("STALE", STALE)]


def _compile(entries):
    out = []
    for label, pat in entries:
        # only auto-wrap with \b when the pattern doesn't already manage its own boundaries
        wrapped = pat if (r"\b" in pat) else r"\b(?:%s)\b" % pat
        out.append((label, re.compile(wrapped, re.IGNORECASE)))
    return out


def _blank_regions(text, regexes):
    """Replace matched regions with spaces (newlines preserved) so offsets stay correct."""
    spans = []
    for rx in regexes:
        for m in rx.finditer(text):
            spans.append((m.start(), m.end()))
    if not spans:
        return text
    chars = list(text)
    for s, e in spans:
        for i in range(s, e):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


HTML_CODE = [
    re.compile(r"<pre\b.*?</pre>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<code\b.*?</code>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<script\b.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<style\b.*?</style>", re.IGNORECASE | re.DOTALL),
]
HTML_TAG = [re.compile(r"<[^>]+>")]
MD_CODE = [
    re.compile(r"```.*?```", re.DOTALL),
    re.compile(r"~~~.*?~~~", re.DOTALL),
    re.compile(r"`[^`\n]+`"),
]


def mask(text, path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".html", ".htm", ".xhtml", ".svg"):
        text = _blank_regions(text, HTML_CODE)   # drop verbatim code/scripts/styles
        text = _blank_regions(text, HTML_TAG)     # drop tags + attributes, keep visible text
    elif ext in (".md", ".markdown", ".mdx"):
        text = _blank_regions(text, MD_CODE)
    return text


def line_col(offsets, pos):
    # offsets is a sorted list of line-start indices
    lo, hi = 0, len(offsets) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if offsets[mid] <= pos:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1, pos - offsets[lo] + 1


def load_extra(paths):
    entries = []
    for p in paths:
        if not p or not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            for raw in f:
                line = raw.split("#", 1)[0].strip()
                if line:
                    entries.append(("personal", line))
    return entries


def scan(path, compiled):
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    masked = mask(raw, path)
    line_starts = [0]
    for i, ch in enumerate(raw):
        if ch == "\n":
            line_starts.append(i + 1)
    findings = []
    for cls, entries in compiled:
        for label, rx in entries:
            for m in rx.finditer(masked):
                ln, col = line_col(line_starts, m.start())
                findings.append({
                    "class": cls, "label": label, "line": ln, "col": col,
                    "text": raw[m.start():m.end()],
                    "start": m.start(), "end": m.end(),
                })
    # Dedupe nested/duplicate matches: a sub-match ("takeaway" inside "key takeaway") or a word
    # listed in two classes (a personal ban that is also SOFT) is reported once. Keep the longest,
    # highest-priority span; drop anything fully contained within an already-kept one.
    priority = {"PERSONAL": 0, "HARD": 1, "STALE": 2, "SOFT": 3}
    ordered = sorted(findings, key=lambda f: (-(f["end"] - f["start"]), priority[f["class"]]))
    kept = []
    for f in ordered:
        if any(k["start"] <= f["start"] and f["end"] <= k["end"] for k in kept):
            continue
        kept.append(f)
    return sorted(kept, key=lambda f: (f["line"], f["col"]))


def compile_all(extra_entries):
    compiled = [(cls, _compile(entries)) for cls, entries in CLASSES]
    if extra_entries:
        compiled.append(("PERSONAL", _compile(extra_entries)))
    return compiled


def print_list(extra_entries):
    for cls, entries in CLASSES:
        print(f"\n# {cls}")
        for label, pat in entries:
            print(f"  {label}: {pat}")
    if extra_entries:
        print("\n# PERSONAL")
        for _, pat in extra_entries:
            print(f"  {pat}")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--list", action="store_true", help="print the lexicon and exit")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--extra", action="append", default=[], help="extra banned-words file (repeatable)")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    default_personal = os.path.join(here, "..", "references", "personal-bans.txt")
    extra_paths = list(args.extra)
    if os.path.exists(default_personal):
        extra_paths.append(default_personal)
    extra_entries = load_extra(extra_paths)

    if args.list:
        print_list(extra_entries)
        return 0

    if not args.files:
        ap.error("no files given (use --list to dump the lexicon)")

    compiled = compile_all(extra_entries)
    all_findings = {}
    hard_total = 0
    for path in args.files:
        findings = scan(path, compiled)
        all_findings[path] = findings
        hard_total += sum(1 for f in findings if f["class"] in ("HARD", "PERSONAL"))

    if args.json:
        print(json.dumps(all_findings, indent=2))
        return 1 if hard_total else 0

    for path, findings in all_findings.items():
        counts = {}
        for f in findings:
            counts[f["class"]] = counts.get(f["class"], 0) + 1
        summary = ", ".join(f"{c}={counts[c]}" for c in ("HARD", "PERSONAL", "SOFT", "STALE") if c in counts) or "clean"
        print(f"\n=== {path}  [{summary}] ===")
        if not findings:
            print("  no findings")
            continue
        for f in findings:
            print(f"  {f['line']:>5}:{f['col']:<3} {f['class']:<8} {f['label']:<22} → {f['text']!r}")

    print(f"\n{hard_total} must-fix (HARD/PERSONAL) finding(s).")
    return 1 if hard_total else 0


if __name__ == "__main__":
    sys.exit(main())
