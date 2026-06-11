---
name: visual-walkthrough
description: Generate a hand-crafted, self-contained HTML process flowchart that walks a reader through a code module — color-themed nodes connected by SVG arrows, with iteration shown as dashed loop wrappers (with explicit termination conditions and back-edge cues), nested sub-flows, KaTeX equations paired with verbatim source lines, and pinned-SHA permalinks. Trigger when the user asks for a "walkthrough", "flowchart", "explain how X works as HTML", "document how this module flows", "show me what the algorithm looks like", or wants a single-file HTML doc that traces information flow including loops, branches, and convergence checks. Works on any language; tuned for scientific code in Julia / Python / Fortran. Output is one or more HTML files the reader opens in a browser. Do NOT use for code review, refactoring suggestions, or interactive tutorials — this is a read-only explanatory artifact built from real code, not invented.
---

# Code Walkthrough HTML — process flowchart style

Generate a self-contained HTML process flowchart that traces information flow through a code module. The reader sees a vertical column of color-themed nodes connected by SVG arrows. Iteration is wrapped in dashed boxes with explicit termination conditions and back-edge cues. Each node is click-to-expand and reveals: the docstring summary, KaTeX equations rendered next to the verbatim source lines they came from, a reads/writes table, and a pinned-SHA GitHub permalink.

**Style reference:** `/Users/prashanth/codes/pyEPM/docs/epm_flowchart.html` (operator-split Lagrangian model with time-step loop and nested microphysics wrapper). A second worked example for a different domain lives at `/Users/prashanth/codes/ralph/projects/claudes_TASOPT.jl/TASOPT.jl/engine_sizing_flowchart.html`.

## Inputs to gather (ask once, up front, only what's missing)

1. **Entry point** — function name + file path where the walkthrough starts.
2. **Scope** — which module(s) to descend into. Default: same Julia module / Python package as the entry point. Anything outside scope becomes a leaf node or a callout.
3. **Repo URL + commit SHA** — for permalinks. Try in order: `git remote get-url origin`, then `git rev-parse HEAD`. If not in a git repo, ask.
4. **Output path** — where to write the HTML. Default: `<entry_function>_flowchart.html` in CWD.

If the call structure has two non-trivial branches (e.g. sizing vs. off-design, design vs. inference), confirm which branch is the **main path** before generating; the alt branch goes in a sidebar callout or its own sibling file.

Confirm these in one line before generating.

## Files in this skill

- `SKILL.md` — this file (the protocol)
- `template.html` — HTML skeleton: header gradient, KaTeX wired up, full CSS for nodes / arrows / loop-wrappers / sidebar-callouts / schematic SVGs, click-to-expand and print-expand-all JS. Slots: `{{TITLE}}`, `{{SUBTITLE}}`, `{{HEADER_META}}`, and HTML-comment markers (`<!-- LEGEND_OPTIONAL -->`, `<!-- SCHEMATIC_OPTIONAL -->`, `<!-- FLOW_NODES -->`, `<!-- SIDEBAR_CALLOUTS -->`, `<!-- FOOTER_BLOCK -->`).
- `extraction_protocol.md` — read this before generating. The full HTML pattern catalog: node themes, arrow flavors, loop-wrapper shape with convergence-check decision node, micro-wrapper for nested sub-flows, equation-block + source-block pairing rules, schematic-SVG guidance, sidebar-callout pattern, and the anti-fabrication checklist.

## Protocol

1. Read `extraction_protocol.md` and `template.html` in this directory.
2. Open the worked references — `pyEPM` for node + loop-wrapper styling, `engine_sizing_flowchart.html` for the type-modularity additions. They are the visual contract.
3. Resolve inputs above. If two branches exist, confirm the main path.
4. Walk the entry function. For each step in the algorithm's execution:
   - Decide the node theme by **what kind of work the step does**, not by source-file location (see `extraction_protocol.md` §3a).
   - Wrap any `for`/`while` loop with a real iteration semantics in a `.loop-wrapper`. Quote the literal loop header in the `.cond` chip; add a convergence-check decision node at the end of the loop body quoting the literal termination test.
   - Group conceptually-related sub-flows (operator splits, "combustor + cooling") in a `.micro-wrapper`.
   - For each node body: paraphrase the docstring (1–3 sentences, no marketing), pair every equation with the verbatim source line(s) it came from, list reads/writes when the node mutates shared state, and link a pinned-SHA permalink at the bottom.
   - For non-trivial alt branches: write a `.sidebar-callout` after the main flow, OR generate a sibling file and link to it from the callout.
5. **If the codebase has a typed component layer** (struct hierarchy, component types, composed sub-types): `grep -n '^struct \|^mutable struct ' <relevant_files>` to enumerate types. Build a side-by-side **types panel** + **expandable type cards** at `<!-- TYPES_PANEL_OPTIONAL -->` per `extraction_protocol.md` §9. Add `.typesig` chips to component-action flow nodes per §11.
6. **If you see a typed-vs-inline split** (typed wrapper exists in one file, inline implementation runs in the path you're walking): grep call sites to confirm. Add a **Migration-status block** (✓/✗/→) to the relevant type card per §10. Add a **migration-callout** to the affected flow-node body, splitting source excerpts into "inline form (executed)" vs "typed wrapper (not invoked from this path)". **Then ask the user whether to file a tracker issue** for the gap — sketch what it would contain (title, evidence, draft acceptance criteria) but do not run `bd create` or equivalent without explicit approval.
7. Optional: add an inline `.station-schematic` SVG at `<!-- SCHEMATIC_OPTIONAL -->` only if a hand-drawn domain diagram genuinely helps. The bar is high — cute-but-unhelpful diagrams get cut.
8. **For long flowcharts** (>6 flow nodes, has a loop wrapper, or has a populated types panel): build a `<nav class="toc-rail">` and inject at `<!-- TOC_RAIL_OPTIONAL -->` per `extraction_protocol.md` §12. Each link uses `data-toggle="{slug}"` so click-to-jump auto-expands the target. Add wrapper IDs (`type-{slug}`, `loop-{name}`, `micro-{name}`, `sidebar-{name}`) for the link targets. The rail auto-hides below 1500 px viewport — short flowcharts that the rail wouldn't help skip this step entirely.
9. Optional: split equation+source pairs into the side-by-side `.pair` / `.pair-source` layout (CSS already in template) for nodes where the math and code are conceptually paired one-to-one. Useful on wide screens; falls back to stacked below 920 px.
10. Inject the HTML into the template at the comment markers, fill the placeholders, write the file, tell the user the path. Do not echo the HTML in chat.

## Hard rules (anti-fabrication — non-negotiable)

These are the rules that make this artifact trustworthy enough to publish.

- **Every node body has a permalink** with a pinned 40-char SHA, and visible `path:Lstart-Lend` link text.
- **Every equation is paired with the verbatim source line(s) it came from** in the same node body. If you cannot honestly LaTeXify a line (opaque function call, table lookup, branching logic), show only the source — do not invent math the code doesn't express.
- **Every loop's `.cond` chip is a literal substring of the source.** If multi-line, use the first line and add `(see L{n})`.
- **Every loop has a convergence-check decision node** quoting the literal termination test (`if dmax < toler`, etc.). A loop without an explicit exit cue is a stub, not a walkthrough.
- **Node summaries paraphrase the docstring or describe purely structural facts** (signature, what's mutated). Do not infer physical meaning from variable names alone.
- **Schematic SVGs represent something documented in the source or a cited reference.** Geometry you can't trace is fabrication — leave it out.
- **Branch labels on arrows are verbatim** from the source (`case == 'design'`, `opt_calc_call == CalcMode.Sizing`).
- **Type chips and migration-status markers cite real call sites.** A chip naming a type that doesn't exist, or a `✓` claiming a typed wrapper is invoked when grep shows otherwise, is fabrication. Verify with `grep -n '^struct \|^mutable struct ' <file>` and `grep -rn 'function_name\!' src/` before writing the markers.
- **Surfacing a migration gap means asking, not filing.** Sketch a tracker issue (title, evidence, draft acceptance criteria) and ask the user whether to create it. Do not run `bd create` or equivalent without explicit approval — the user owns the tracker and decides which findings become action items.

## What "good" looks like

- A reader who has never seen the code can scan the closed flowchart and learn the algorithm's shape (entry, branches, loops, exit) in 30 seconds.
- The visible loop labels and convergence chips tell them where iteration lives and how it terminates without expanding any node.
- Every claim in any expanded node body is auditable in one click via the permalink.
- The HTML opens in any browser, no build step, no internet required *except* the KaTeX CDN.
- The file feels hand-crafted, not generated. Color choices have meaning. Arrow labels appear only where they earn their place. Equation-block colors agree with the surrounding node theme.

## When NOT to use this skill

- **Code review** → use a code-review agent.
- **Refactoring proposals** → use the simplify or improve-codebase-arch skill.
- **Interactive tutorials** → this is read-only explanatory.
- **Cards-style stack of function summaries** with no real iteration or branching — that's a different artifact, this skill no longer produces it. Either accept the flowchart format (which works fine for linear pipelines too) or use a different tool.
