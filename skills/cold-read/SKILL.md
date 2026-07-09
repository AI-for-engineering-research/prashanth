---
name: cold-read
description: Scrub AI-slop vocabulary and stale relative references out of any agent's output (Claude, GPT, or other) so it stands on its own for a reader with no session context. Two stages — a deterministic word/phrase lint, then a context-denied rewrite. Trigger on "clean up", "de-slop", "scrub", "remove the slop", "make this human-readable / human-friendly", "cold read", "humanize this"; on any artifact carrying trust-eroding words ("honest", "clearly", "obviously", "seamless", "delve") or dangling edit references ("the 4% I claimed earlier", "now fixed", "no longer hidden", "as requested", "updated to 2%"); and as the final step of any artifact-generating skill (walkthrough, visual-walkthrough, reports, PRDs). Operates on files and on the agent's own chat responses. Rewrites for clarity — not code review, not fact-checking.
argument-hint: "path to the artifact to clean (omit to apply to your own response)"
---

# Cold Read — make agent output stand on its own

Goal: a competent stranger with **zero session context**, reading days later, understands every
sentence and trusts every claim. That stranger is the spec.

## Two failure modes this kills

1. **Slop vocabulary** — honesty-signaling ("Honest Comparison", "to be honest"), rhetorical
   certainty ("clearly", "obviously", "definitive"), hype ("seamless", "delve", "cutting-edge"),
   and meta-narration ("it's worth noting"). Honesty and correctness are *assumed* in technical
   work; asserting them makes the reader suspect the opposite. The words add nothing and cost trust.
2. **Stale relative references** — the edit history leaking into the text: "the 4% I claimed
   earlier is incorrect", "now shown, not hidden", "no longer out of band", "as requested,
   updated to 2%". These reference the *conversation* or a *prior version* the reader never saw.
   To a cold reader they are noise.

## The principle — the cold reader is the auditor, and it must be context-denied

The best auditor for self-containedness is an agent **denied the conversation**. A reader who
remembers the session can rationalize "now fixed" from memory; a stranger cannot, so the stranger
flags exactly what is broken. We do not fight the subagent's lack of context — **we weaponize it.**
The agent that *generated* an artifact is the worst judge of whether it stands alone, because it
knows too much. Hand the file to a fresh reader instead.

## Two surfaces

- **A file** — an HTML walkthrough, a markdown report, a PRD, or raw text saved from any agent
  (Claude, GPT, whatever). The main use. (To clean a paste-in from another tool, save it to a file
  first, then run this.)
- **Your own chat response** — self-audit before sending. See the last section.

## Protocol — cleaning a file

**Stage 1 — Lint (deterministic, fast).** No model needed.

```
python3 scripts/slop_lint.py <FILE>
```

- `HARD` / `PERSONAL` → must fix, every one. (Exit code is 1 while any remain.)
- `STALE` → review each; these are the relative-reference tells. Most must go; a few are innocent.
- `SOFT` → jargon/hedges with real uses; keep only the load-bearing ones, cut the filler.
- The lint never touches code: verbatim `<pre>`/`<code>`/`<script>` (HTML) and fenced/inline code
  (Markdown) are masked out before scanning. Source excerpts are untouchable.

**Stage 2 — Cold-read rewrite (context-denied agent).** Dispatch a subagent (Agent tool) and give
it **only**: the file path, the lint output, and this skill. Tell it **nothing** about the
conversation, the previous version, what changed, or why — that denial is the entire mechanism.
Its instructions:

- Read the file as a stranger. Rewrite **in place** to:
  - remove every HARD/PERSONAL hit,
  - resolve or delete every STALE reference **using only what is already in the artifact**,
  - cut SOFT filler that carries no load,
  - apply the **register rules** below.
- **Never invent a fact.** If a sentence leans on something not present in the artifact, rewrite it
  to state only what the artifact supports, or cut it — and record it in a `NEEDS-CONTEXT` list.
- **Never change a claim's meaning.** Cleaning is not rewriting the result. Touch no code, quote,
  number, or data.
- Return: the changes made, plus the `NEEDS-CONTEXT` list.

**Stage 3 — Reconcile (you, with context).** You watched the session; the cold reader did not. For
each `NEEDS-CONTEXT` item, supply the **absolute** fact ("X is 4%") or confirm the deletion. This
is the division of labor: the context-denied agent finds the holes; you fill them. Never restore a
relative phrasing — convert it to a standalone statement.

**Stage 4 — Re-lint.** Re-run the linter. `HARD`/`PERSONAL` must be zero. Read it once more cold.

> For a short file you may run all four stages yourself — but you must deliberately read the file
> *alone*, judging only what is on the page and ignoring what you remember. The subagent is more
> reliable precisely because it **cannot** cheat.

## Register — hybrid

Match the form to the content:

| Use **prose** (full grammar, short declarative sentences) for | Use **telegraphic** (drop articles/copulas, fragments fine) for |
|---|---|
| explanations, the "why", reasoning | bullet lists |
| captions that must stand alone | table cells |
| any LaTeX math and its plain-language gloss | short labels, chips, status markers |

- Never telegraphic for an explanation paragraph — it reads as abrupt and hurts comprehension.
- Never padded prose inside a table cell — it bloats the grid.
- Examples:
  - Prose: "PyCycle uses linear interpolation; we use a cubic Hermite scheme — a smooth (C¹) curve."
  - Telegraphic bullet: "Cubic Hermite — C¹ continuous, no overshoot."
  - Telegraphic cell: "max err 1e-10".

## Rules the rewrite enforces

- **No HARD vocabulary.** Honesty/correctness are the floor, never a feature to announce.
- **No stale references.** Every claim is absolute and self-contained — a number, a name, a fact —
  never "the X from before", "now fixed", "as requested", "updated to". A comparison gives both
  values with units, the size and sign of the difference, and the cause.
- **Every number has units**, and in a sourced artifact, a source.
- **Define a technical term** in a few words on first use. Don't infantilize; don't inflate.
- **Don't touch verbatim code, quotes, or data**, and don't change any claim's meaning. If a clean
  would alter a claim, that's a `NEEDS-CONTEXT` item, not an edit.

## The lexicon

- **Source of truth:** `scripts/slop_lint.py` — run `python3 scripts/slop_lint.py --list` to dump it.
- **Rationale + how to extend:** `references/slop-lexicon.md`.
- **Your personal bans:** `references/personal-bans.txt` (one regex per line, `#` comments). Loaded
  automatically by the linter. Add words you dislike here; this is the canonical anti-slop list and
  other skills should defer to it rather than keeping their own.

## Applying to your own chat responses

Before sending a substantive response, self-audit against the same rules: no HARD words, no
references to the conversation that would be meaningless if the sentence were quoted alone, hybrid
register. To check mechanically, write the draft to the scratchpad and lint it:

```
python3 scripts/slop_lint.py /path/to/scratchpad/draft.md
```

## Calling cold-read from other skills

Any artifact-generating skill (walkthrough, visual-walkthrough, research reports, PRDs) should run
cold-read as its **final step**, dispatched **context-denied** — never as a self-check by the agent
that wrote the artifact, which knows too much to see the gaps.
