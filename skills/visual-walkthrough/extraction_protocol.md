# Extraction Protocol

Read this when generating a walkthrough. The output is a vertical, hand-crafted process flowchart: a column of color-themed nodes connected by SVG arrows, with iteration wrapped in dashed loop boxes. Click-to-expand bodies hold the docstring summary, paraphrased equations rendered with KaTeX, the verbatim source lines they came from, and a permalink. The visual reference is the hand-built `pyEPM` flowchart at `/Users/prashanth/codes/pyEPM/docs/epm_flowchart.html`.

This is **not** a Mermaid diagram. Mermaid produced something generic; readers wanted a real algorithmic walkthrough that shows iteration and convergence. The cost is ~30–50 lines of HTML per node. Pay it.

---

## 1. When to use which output

| Situation | Output |
|---|---|
| One linear pipeline (parser, formatter, simple call chain) | One flowchart file |
| Two branches that share a pipeline (sizing vs. off-design, request vs. retry) | One flowchart file with the main path inline + the alt path in a `sidebar-callout` |
| One branch has its own non-trivial iteration (Newton solver, multi-stage retry, mission loop) | One flowchart file per branch, cross-linked |
| Mostly-static type hierarchy (struct composition, schema) | A short cards file is fine; flowcharts overkill |

When in doubt, ship one flowchart focused on the most pedagogical path; offer to produce siblings for the other branches.

---

## 2. Structure of one flowchart file

The file is a vertical column inside `.flow`, alternating **nodes** and **arrows**. Iteration is wrapped in a `.loop-wrapper`. Sub-flows that aren't loops but are conceptually grouped (e.g. "combustor + cooling", "operator-split microphysics") use a `.micro-wrapper`. Optional alt branches live in a `.sidebar-callout` outside the main flow.

```
header (gradient + title + meta)
container
├── legend (optional)
├── station-schematic (optional inline SVG)
├── flow
│   ├── node 1
│   ├── arrow
│   ├── node 2
│   ├── arrow
│   ├── loop-wrapper                  ← iteration
│   │   ├── loop-label
│   │   └── loop-inner
│   │       ├── node A
│   │       ├── arrow
│   │       ├── micro-wrapper          ← grouped sub-flow (optional)
│   │       │   ├── micro-label
│   │       │   └── micro-inner
│   │       │       ├── node B1
│   │       │       └── node B2
│   │       ├── arrow
│   │       ├── node C
│   │       └── decision (convergence check)
│   └── node N (e.g. EXIT block)
├── sidebar-callout (alt branch, optional)
└── footer (references / conventions)
```

---

## 3. Node patterns

### 3a. Color themes — pick by domain meaning, not by step number

Colors are **semantic**. They tell the reader the kind of work the node does. Apply them consistently across the file.

| Theme class | When to use |
|---|---|
| `node-config` (gray) | Entry points, setup, parameter unpacking, area/sizing computations, output write-back wiring |
| `node-blue` | Primary computation step, ODE/solver call, compressor stage, anything CPU-heavy |
| `node-green` | Adiabatic / lossless transformation, inlet, nozzle, init, geometric setup |
| `node-orange` | **Optional** step that may be a no-op (heat exchanger with zero deltas, opt-in feature) |
| `node-red` | Combustor, chemistry, stiff coupling, irreversible mixing |
| `node-teal` | Turbine, recovery, energy-balance closure |
| `node-purple` | Output / write-back / serialization |
| `node-output` | Final write-back to the canonical state object (white background, purple border, heavier weight) |
| `node-decision` | A non-clickable note describing a branch decision (dashed gray border) |

If your domain doesn't map to engines, don't force the colors. The rule is: pick 4–6 themes for the file, give each a clear meaning, document them in the legend, and stick with it.

### 3b. Standard node HTML

```html
<div class="node node-{theme}" id="node-{slug}">
  <div class="node-header" onclick="toggle('{slug}')">
    <span class="badge">{Short label, ≤12 chars}</span>
    {One-line headline of what this node does}
    <span class="stations">{optional: input → output identifiers}</span>
    <span class="toggle" id="toggle-{slug}">&#9654;</span>
  </div>
  <div class="node-body" id="body-{slug}">
    <p>{Paraphrased docstring, 1–3 sentences, NO marketing}</p>

    <div class="eq-block {theme-class}-eq">
      $$ {KaTeX equation, paraphrased from the source line below} $$
    </div>

<pre class="source-block"><span class="ln">L{n}</span>{verbatim source line}</pre>

    <div class="reads-writes">
      <span class="rw-label">Reads</span>  <span><code>x.field</code> <code>y</code></span>
      <span class="rw-label">Writes</span> <span><code>z.field</code></span>
    </div>

    <p class="ref"><strong>Source:</strong> <a href="{permalink}">{path}:L{a}-L{b}</a></p>
  </div>
</div>
```

The headline and the badge should let a reader who only scans the closed flowchart understand the algorithm's shape in 30 seconds. The body is where they go to audit detail.

### 3c. Decision node (non-clickable)

For branch-decision text like "if X then call Y else Z" or "convergence check":

```html
<div class="node node-decision">
  <div class="node-header"><span class="badge">Branch</span>&nbsp;<code>{verbatim condition}</code></div>
  <div class="node-body">
    {Plain text explaining what each side of the branch does and which side this flowchart follows.}
  </div>
</div>
```

Decision-node bodies are always visible (no click-to-expand). Use them sparingly — most branches are clearer as labeled arrows.

---

## 4. Arrows — explicit SVG, never CSS-only

Two arrow flavors:

**Plain arrow** (between sequential nodes):
```html
<div class="arrow">
  <svg width="2" height="28"><line x1="1" y1="0" x2="1" y2="28" stroke="var(--arrow)" stroke-width="2"/></svg>
  <svg width="12" height="10"><polygon points="0,0 12,0 6,10" fill="var(--arrow)"/></svg>
</div>
```

**Labeled arrow** (when the data passing between two nodes deserves a name — e.g., `y(t_{i+1})`, branch condition, "design fan-out"):
```html
<div class="arrow">
  <svg width="2" height="28"><line x1="1" y1="0" x2="1" y2="28" stroke="var(--arrow)" stroke-width="2"/></svg>
  <span class="arrow-label">{terse label, ideally a code expression}</span>
  <svg width="12" height="10"><polygon points="0,0 12,0 6,10" fill="var(--arrow)"/></svg>
</div>
```

Use labels every 3–4 arrows at most. If every arrow has a label the page becomes noisy; readers tune them out.

Inside a `loop-wrapper`, use shorter arrows (`height="20"` instead of `28`) so the inner column doesn't feel sparse.

---

## 5. Loop wrappers — first-class, with explicit termination

Every meaningful iteration in the source code becomes a `.loop-wrapper`. The label states **what is iterating** in plain language; the `.cond` chip states **the literal source-code condition** verbatim.

```html
<div class="loop-wrapper">
  <div class="loop-label">{What iterates} &nbsp; <span class="cond">{verbatim for/while header}</span></div>

  <div style="font-size:.78rem;color:var(--blue);text-align:center;padding:.2rem 0 .8rem;font-family:var(--font-mono)">
    {iteration bounds + tolerance, e.g. "itmax = 50, toler = 1.0e-9"}
  </div>

  <div class="loop-inner">
    {nested nodes + arrows}

    <div class="node node-decision">
      <div class="node-header"><span class="badge">Convergence</span>&nbsp;<code>{verbatim convergence test}</code> ?</div>
      <div class="node-body">
        <strong>Yes</strong> → break out, fall through to next node.
        <strong>No</strong> → {what mutates between iterations}, restart from {first node in loop}.
      </div>
    </div>

    <div class="loop-feedback">↑ If not converged, restart from the {name} node above.</div>
  </div>
</div>
```

The convergence-check decision node is mandatory — without it, readers don't know how the loop terminates.

The `loop-feedback` line is a back-edge cue. It substitutes for an actual back-arrow because back-arrows in pure HTML/CSS are awkward; a textual cue plus the dashed-border wrapper is enough.

### Nested loops / grouped sub-flows

`.micro-wrapper` is the same shape as `.loop-wrapper` but with green dashed borders and a `.micro-label`. Use it for:

- Sub-flows that are conceptually grouped but not a loop (e.g. "combustor + cooling" within a larger pipeline)
- Inner loops nested inside an outer loop (Newton inside time-step)
- Operator splits that always run together

If the inner thing is a loop, override `.micro-label` styling to match `.loop-label` (dashed blue border) — or just use a nested `.loop-wrapper` directly. Both work.

---

## 6. Equation blocks and source blocks

### 6a. Equation block

Always paired with the verbatim source line(s) it represents. The left border color matches the surrounding node's theme:

```html
<div class="eq-block green-eq">
  $$ p_{t12} = p_{t0}\,\pi_\mathrm{id} $$
</div>
<pre class="source-block"><span class="ln">L118</span>st12.pt = st0.pt * inlet.pid</pre>
```

KaTeX delimiters: `$$ ... $$` for display, `$ ... $` for inline. **Inside `\begin{aligned}` blocks, write `&` as `&amp;` in HTML source** — the browser otherwise eats it. Same for `<`, write `&lt;`.

### 6b. Source block (verbatim, with line numbers)

```html
<pre class="source-block"><span class="ln">L398</span>for iter = 1:itmax
<span class="ln">L399</span>      {body}
<span class="ln">L2645</span>      if (dmax &lt; toler) | (iter == itmax)</pre>
```

Always show **line numbers**, always paired with a permalink in the same node body. Don't wrap or reformat — copy the source verbatim, including indentation. If lines are too wide, the `overflow-x: auto` on `.source-block` lets the user scroll.

When you want to highlight a non-contiguous excerpt (lines 35, 57, 88), use a single `<pre>` with the relevant lines and let the line-number gaps tell the reader they skipped material. Don't fake a contiguous range.

### 6c. Reads / writes table

Optional but recommended for nodes that mutate shared state. Keeps the data-flow auditable:

```html
<div class="reads-writes">
  <span class="rw-label">Reads</span>  <span><code>eng.Tt4</code> <code>eng.design.pid</code></span>
  <span class="rw-label">Writes</span> <span><code>eng.st4.ht</code></span>
</div>
```

---

## 7. Permalinks — one per node body

Format strictly as:

```
https://github.com/{owner}/{repo}/blob/{commit_sha_full}/{path_from_repo_root}#L{start}-L{end}
```

- 40-char SHA, never `main` / `HEAD` / a branch name.
- Visible link text: `{path}:L{start}-L{end}` (path relative to repo root).
- One per node body, in a `<p class="ref">` at the bottom.
- Multiple permalinks separated by `&nbsp;|&nbsp;` if the node spans non-contiguous source.

If the git remote is SSH (`git@github.com:owner/repo.git`), translate to HTTPS form.

---

## 8. Inline schematic SVGs (optional)

When a hand-drawn diagram (engine cross-section, Köhler curve, time-T plot, plume geometry) would help the reader picture the physics that the equations describe, embed an SVG directly. Keep them under ~400×220 px. Fill from the same color palette as the node themes so the diagram visually agrees with the surrounding nodes.

Two placement options:

- **Top of the file** as a `.station-schematic` block (overview / domain map).
- **Inside a node body** as a `.svg-container` block (illustrating the equation in that node).

Don't fabricate data — only draw schematics that represent something the source code or a docstring describes. If you don't have a source for the geometry, leave it out.

---

## 9. Types & modularity panel (when the codebase has a typed component layer)

When the module under walkthrough has a non-trivial type system — state containers (struct hierarchy), component types (one struct per algorithmic piece), composed sub-types (maps, fuels, etc.) — the closed flowchart alone hides the modularity. A reader sees "fan, LPC, HPC" as three nodes but doesn't see they're three instances of the same `Compressor{T}` type. Surface that with a **types panel**.

Trigger: codebase has any of (a) a typed state container with composed sub-states (e.g. `EngineState ⊃ DesignState + FlowStation × N`), (b) a small zoo of component types instantiated in known multiplicities (e.g. `Compressor × 3`), (c) a refactor mid-flight where typed wrappers exist alongside inline implementations. Skip for plain library code with no domain type model.

Inject at `<!-- TYPES_PANEL_OPTIONAL -->`. Two paired pieces:

### 9a. Side-by-side overview SVG

A single hand-drawn SVG, ~960 wide × 420–480 tall, split by a dashed vertical line into two columns:

- **Left ("WHAT FLOWS")** — state containers as nested boxes. The outer container is the top-level state; inside it, three or four labeled regions for the major field groups (composed sub-states, repeated stations, ambient + perf scalars). Below the outer box, "composes" arrows lead down to each composed sub-type (FlowStation, GasState, etc.) drawn as separate, smaller boxes that show their fields at one zoom level deeper. Use the `--purple` family for the top-level container so the colour means "single source of truth".
- **Right ("WHAT ACTS")** — component types as a stack of small color-coded boxes. Each box: type name + multiplicity badge (`×3 — fan/LPC/HPC`) + verbatim field listing. Colors agree with the flow-node colors of the steps they implement (`Compressor` blue, `Combustor` red, `Turbine` teal, etc.).
- A small **"How to read"** caption at the bottom of the right column linking the panel to the type chips on flow nodes ("a node tagged `::Compressor (FanMap)` is one of the three Compressor instances above — fan / LPC / HPC share their signature, only the embedded map differs").

Field listings inside SVG `<text>` elements must be **verbatim from the struct definition** in the source. Don't invent fields.

### 9b. Expandable type-detail cards (one per type)

Below the SVG, render a 2-column grid of `.type-card` elements — one card per struct shown in the panel. Each card is **click-to-expand** using the same `toggle()` function the flow nodes use; the open body shows the structured detail readers need to audit a type:

```html
<div class="type-card tc-{theme}">
  <div class="type-header" onclick="toggle('type-{slug}')">
    <span class="type-badge {theme}-b">{State|Component|Quasi-component}</span>
    <span class="type-name">TypeName{T}</span>
    <span class="type-meta">{count fields, mutability, instances}</span>
    <span class="type-toggle" id="toggle-type-{slug}">&#9654;</span>
  </div>
  <div class="type-body" id="body-type-{slug}">
    <p>{One-paragraph paraphrase of the docstring purpose.}</p>

    <div class="type-section">Fields</div>
    <pre class="field-list">{verbatim field listing from the struct}</pre>

    <div class="type-section">Constructor</div>
    <pre class="field-list">{verbatim signature(s) of public constructors}</pre>

    <div class="type-section">Methods</div>
    <pre class="field-list">{functions that take this type as primary argument, signature only}</pre>

    <div class="migration">
      {Migration-status block — see §10. OPTIONAL but strongly recommended
       when the codebase has any typed-vs-inline split.}
    </div>

    <p class="ref"><strong>Source:</strong> <a href="{permalink}">{path}</a></p>
  </div>
</div>
```

Available CSS theme classes (border + badge color), pick by what the type *is*, not by file location:

| Theme class | `type-badge` class | When to use |
|---|---|---|
| `tc-state-purple` | `state-b` | Top-level state container (the canonical source-of-truth object) |
| `tc-state-blue` | `cmp-b` | Composed sub-state with its own sub-fields |
| `tc-state-green` | `noz-b` | Leaf state struct (most-nested, scalar fields only) |
| `tc-cmp-blue` | `cmp-b` | Compressor / pump / pipeline-stage component |
| `tc-cmb-red` | `cmb-b` | Combustor / chemistry / irreversible-mixing component |
| `tc-trb-teal` | `trb-b` | Turbine / energy-recovery component |
| `tc-noz-green` | `noz-b` | Nozzle / outlet / boundary component |
| `tc-inl-green` | `inl-b` | Inlet / source / entry component |
| `tc-shf-gray` | `shf-b` | Connector struct (shaft, bus, channel) |
| `tc-hx-orange` | `hx-b` | Quasi-component without its own struct |

If your domain doesn't map to engines, repurpose by meaning — but stay consistent within one file.

---

## 10. Migration-status convention (typed-vs-inline split)

Some refactors leave both implementations in the codebase: a typed wrapper that's the target shape, and an inline scalar version that's still what runs in the legacy hot path. The walkthrough must surface this honestly — pretending the typed API is invoked when it isn't is fabrication, and silently citing two file ranges as if they're the same code is worse.

Use a **`.migration` block** inside any type-card body and (when relevant) a **`.migration-callout`** at the top of any flow-node body. Both render as a yellow left-border callout.

### Markers

Inside the migration block, three semantic spans:

- `<span class="check">✓</span>` — typed API IS invoked at this site, with a `path:Lstart-Lend` citation.
- `<span class="cross">✗</span>` — inline form still runs at this site, with a `path:Lstart-Lend` citation.
- `<span class="arrow">→</span>` — interpretation note (where the dual citation in the flow node comes from, what the chip names vs. what executes, etc.).

### Required content

For every `✓` or `✗` marker, cite **the actual call site** (file + line range). A migration claim without a verifiable citation is a fabrication. If you're unsure whether a typed function is called from a path, grep for it (`grep -rn "function_name\!" src/`) before writing the marker.

### When to use a flow-node migration callout

When the typed wrapper for a node's algorithm exists but the legacy path still uses inline code, the flow-node body should:

1. Open with a `<div class="migration-callout">` explaining the dual-citation reality in plain prose ("two implementations of the same physics live in this codebase — the path actually executes the inline form at X, the typed wrapper at Y is the refactor target shape and is currently called only from Z").
2. Show **both source excerpts** in `source-block`s — first the inline form actually executed (label it explicitly), then the typed wrapper (label that too).
3. Split the `<p class="ref">` into "**Inline form (executed):**" and "**Typed wrapper (not invoked from this path):**" with separate permalinks.

This converts the dual citation from a confusing artifact into a teaching point.

### Offer to file a tracker issue (don't file it unprompted)

When the walkthrough surfaces a migration gap that isn't already tracked, **ask the user whether they'd like a tracker issue filed for it**. Sketch what the issue would contain — title, the duplication evidence with line citations, the target state, draft acceptance criteria — but **do not run `bd create` (or the equivalent) until they say yes**. The user owns the tracker; the walkthrough surfaces findings, the user decides which become action items. Filing issues without permission clutters the backlog and pre-empts their judgement about scope.

---

## 11. Type chips on flow-node headers

When the types panel exists, mirror it on each flow-node header with a single `.typesig` chip naming the **dominant component type** the node implements. Readers scanning the closed flowchart immediately see "fan, LPC, HPC are three `::Compressor` chips" — modularity surfaced at a glance.

```html
<span class="typesig {theme}">::Compressor{T} (FanMap)</span>
```

Chip classes (set the chip's color):

| Class | Use for |
|---|---|
| `typesig` (no modifier) | State container, sub-state slice (purple, default) |
| `typesig cmp` | Compressor / pump / pipeline component (blue) |
| `typesig cmb` | Combustor / chemistry / mixing component (red) |
| `typesig trb` | Turbine / recovery (teal) |
| `typesig hx` | Heat exchanger / quasi-component (orange) |
| `typesig noz` | Inlet / nozzle / boundary (green) |
| `typesig gry` | Connector / shaft / bus (gray) |

### Honesty rules for type chips

- A chip naming `::Compressor (FanMap)` on a node where the actual call site uses `gas_prat(...)` directly **is acceptable** — the chip names the type the math implements (the modularity story). But the node body must contain a migration callout (§10) explaining the typed wrapper is not invoked here.
- A chip naming a type that does not exist in the source code is fabrication. Always verify via `grep -n "^struct \|^mutable struct " <file>`.
- Skip type chips on:
  - Pure entry / exit nodes (`tfwrap!`, `tfcalc!` ENTRY) — show what they consume / produce in prose, not chips.
  - Decision nodes — they have no type.
  - Convergence-check nodes — they have no type.
- Use the chip space for a domain-relevant string, not a Julia/Python function signature. `::Compressor (FanMap)` is more useful than `(::FlowStation, π, η_pol) → FlowStation`.

---

## 12. Floating left-rail TOC (long flowcharts)

For flowcharts with more than ~6 flow nodes, a loop wrapper, or a populated types panel, add a fixed-position left-rail TOC paired with a toggle button. It pays for itself by letting the reader jump to any section without scroll-hunting and shows them which section is currently on screen. Skip for short flowcharts (≤5 nodes, no loops); the rail is overhead with nothing to navigate.

The rail **slides in and out** under user control via a small `☰` button at the top-left. It opens by default on viewports ≥1500 px (where the centered container leaves margin) and closes by default on narrower screens (where it would overlap content). Either way the toggle button is always visible — the user can pop the rail open whenever they need to navigate, then dismiss it (`✕` button or `Esc`) to read the main flow without obstruction. The rail is hidden on print regardless.

Inject **both** the toggle button and the rail at `<!-- TOC_RAIL_OPTIONAL -->`. The template's CSS also includes a **right-bias rule** that fires on any viewport ≥1200 px when a TOC toggle is present: the container shifts ~96 px (6 rem) right of its centered position via `margin-left: calc(50vw - 600px + 6rem); margin-right: auto`. The shift is uniform across viewport widths — laptops and 4K monitors both get the same 96 px offset — so the bias never goes extreme. Gated on `body:has(.toc-toggle)`, so files that don't include a TOC stay symmetrically centered.

### 12a. Structure

```html
<button class="toc-toggle" type="button"
        aria-label="Toggle walkthrough navigation"
        aria-controls="toc-rail"
        aria-expanded="false"></button>

<nav class="toc-rail" id="toc-rail" aria-label="Walkthrough navigation">
  <div class="toc-title">Walkthrough</div>

  <div class="toc-section">
    <div class="toc-section-label">Types &amp; containers <span class="toc-badge">{N}</span></div>
    <ul>
      <li><a href="#type-{slug}" data-toggle="type-{slug}">{TypeName}{T}</a></li>
      ...
    </ul>
  </div>

  <div class="toc-section">
    <div class="toc-section-label">{Main flow label, e.g. "On-design flow"}</div>
    <ul>
      <li><a href="#node-{slug}" data-toggle="{slug}"><span class="toc-marker">▸</span>{Node title}</a></li>
      ...
    </ul>

    <div class="toc-loop">↻ {loop name}</div>
    <div class="toc-nested">
      <ul>
        <li><a href="#node-{slug}" data-toggle="{slug}">{Node inside loop}</a></li>
        ...
      </ul>

      <div class="toc-micro">▸ {micro-wrapper name}</div>
      <div class="toc-nested-2">
        <ul>
          <li><a href="#node-{slug}" data-toggle="{slug}">{Node inside micro-wrapper}</a></li>
        </ul>
      </div>

      <ul>...{remaining loop-body nodes}...</ul>
    </div>

    <ul>...{post-loop nodes (EXIT, fan-out)}...</ul>
  </div>

  <div class="toc-section">
    <div class="toc-section-label">{Alt branch label, e.g. "Off-design"}</div>
    <ul>
      <li><a href="#sidebar-{slug}">{Sidebar title}</a></li>
    </ul>
  </div>
</nav>
```

### 12b. Required wrapper IDs

Every TOC link's `href` needs a matching `id` in the page. The flow-node pattern (`id="node-{slug}"`) is already in place; you'll need to add IDs to wrappers that didn't previously have them:

- **Type cards** — add `id="type-{slug}"` to each `.type-card` wrapper. (Body IDs `body-type-{slug}` already exist for the click-to-expand mechanism; the wrapper ID is for scroll targeting.)
- **Loop wrappers** — add `id="loop-{name}"` to each `.loop-wrapper`.
- **Micro wrappers** — add `id="micro-{name}"` to each `.micro-wrapper`.
- **Sidebar callouts** — add `id="sidebar-{name}"` to each `.sidebar-callout`.

### 12c. The `data-toggle` attribute and click-to-expand

Every link to a flow-node body or type-card body should carry a `data-toggle="{slug}"` attribute. The TOC JS reads this attribute on click and calls the existing `toggle({slug})` so the target's body is expanded by the time the browser finishes scrolling — the reader doesn't land on a closed accordion.

Links to elements that don't have a body to open (decision nodes, loop wrappers, sidebar callouts) just use `href="#..."` without `data-toggle`.

### 12d. The `toc-loop` and `toc-micro` separators

These are styled labels (not links) that mark where a loop or micro-wrapper begins in the TOC. They mirror the dashed-border headers in the main flow visually — blue for loops, red for micro-wrappers. The nested items inside use `.toc-nested` (loop) or `.toc-nested-2` (micro).

### 12e. Anti-fabrication for the rail

1. **Every TOC link points at an ID that exists.** Open the file and verify each `href="#..."` resolves; broken jumps make the rail worse than no rail.
2. **TOC labels paraphrase node titles, they don't invent new ones.** A node titled "Inlet diffuser & BLI entropy mix" can be shortened to "Inlet diffuser + BLI" in the rail; it can't become "Inlet processing" — the reader needs to recognise the same step in both places.
3. **The rail's section grouping mirrors the page structure.** If the page has a types panel, a main flow, and a sidebar callout, the rail should have three sections in that order. Don't reorganise into a different hierarchy.

---

## 13. Sidebar callouts (alternative branches)

When the main flowchart follows one branch and a peer branch deserves a mention without doubling the file's length, drop a `.sidebar-callout` after the main flow:

```html
<div class="sidebar-callout">
  <h3><span class="badge">Off-design</span> Where this story branches</h3>
  <p>{2–4 sentences describing the alt branch}</p>
  <div class="eq-block">$$ {key equation} $$</div>
  <pre class="source-block">{key source excerpt}</pre>
  <p class="ref"><strong>Source:</strong> <a href="...">...</a></p>
</div>
```

If the alt branch is itself complex enough to deserve a flowchart, the callout should explicitly say "see `{filename}.html` for the full walkthrough" and link to the sibling file. Don't try to cram two complex iterations into one file.

---

## 14. Anti-fabrication checklist

Run this before writing the file. Every node must pass.

1. **Every node body has a permalink** with a pinned 40-char SHA.
2. **Every equation is paired with the verbatim source line(s) it came from**, in the same node body. No equation without a source line. If you cannot honestly LaTeXify a line (opaque function call, table lookup, branching logic), show only the source — do not invent math the code doesn't express.
3. **Every loop's `.cond` chip is a literal substring of the source**. If the loop header is multi-line or computed, use the first line and add `(see L{n})`.
4. **Every loop has a convergence-check decision node** quoting the literal termination test (`if dmax < toler`, `while !done`, etc.).
5. **Color themes are documented in the legend** when there are more than three.
6. **Node summaries are paraphrased from docstrings or describe purely structural facts** (signature, what's mutated). No physical interpretations invented from variable names alone.
7. **Branch labels on arrows are verbatim** from the source (`case == 'design'`, `opt_calc_call == CalcMode.Sizing`).
8. **Schematic SVGs represent something documented in the source or a cited reference.** Geometry you can't trace to a docstring or a comment is fabrication — leave it out.
9. **Type chips name types that exist** in the source (`grep -n '^struct \|^mutable struct ' <file>` to verify). A chip naming an aspirational/target type is acceptable only when the node body has a migration callout (§10) explaining the discrepancy.
10. **Migration markers (✓/✗) cite real call sites.** Every claim that a typed wrapper is or isn't invoked at a path must include a `path:Lstart-Lend` reference. If you haven't grepped for the call site, you can't make the claim.
11. **Type-card field listings are verbatim from the struct definition** in the source. Don't paraphrase fields; copy them.
12. **When a migration gap is surfaced, offer to file a tracker issue.** Sketch what it would contain (title, evidence, draft acceptance criteria) and ask. Do not run `bd create` or equivalent without explicit user approval — the user owns the tracker.

If a check fails for a node, fix that node before emitting the file.

---

## 15. Template placeholders

`template.html` exposes these slots:

| Placeholder | What goes there |
|---|---|
| `{{TITLE}}` | One-line title for `<title>` and the gradient header `<h1>`. |
| `{{SUBTITLE}}` | Two-sentence pitch under the title. Should name the entry function and the algorithm shape. |
| `{{HEADER_META}}` | `branch <a href="...">name</a> @ shortsha` — points at the commit so the reader can verify provenance. |
| `<!-- LEGEND_OPTIONAL -->` | Inject a `<div class="legend">` here when ≥4 color themes are in use. |
| `<!-- SCHEMATIC_OPTIONAL -->` | Inject a `<div class="station-schematic">` here for an overview SVG (only when a hand-drawn domain diagram genuinely helps; cute-but-unhelpful schematics earn the user's "delete it" — see the engine example, which does NOT ship one). |
| `<!-- TYPES_PANEL_OPTIONAL -->` | Inject a `<div class="station-schematic">` containing the side-by-side types panel SVG, immediately followed by a `<div class="types-detail">` of `.type-card` elements. See §9. |
| `<!-- TOC_RAIL_OPTIONAL -->` | Inject a `<nav class="toc-rail">` for long flowcharts (>6 nodes, has a loop, or has a populated types panel). See §12. The rail is auto-hidden below 1500 px viewport. |
| `<!-- FLOW_NODES -->` | The main column of nodes, arrows, loop-wrappers, micro-wrappers. |
| `<!-- SIDEBAR_CALLOUTS -->` | One or more `.sidebar-callout` blocks (alt branches). |
| `<!-- FOOTER_BLOCK -->` | A `<div>` with conventions, references, and the "generated from {repo}@{sha}" line. |

Drop the comment markers after substitution; leaving them in is harmless but ugly.

---

## 16. Worked reference

The skill ships with two worked examples that together exercise every pattern in this doc:

- **`pyEPM` flowchart** at `/Users/prashanth/codes/pyEPM/docs/epm_flowchart.html` — operator-split Lagrangian model with a time-step loop and a nested microphysics wrapper. This is the original visual contract for the node + loop-wrapper styling.

- **`engine_sizing_flowchart.html`** at `/Users/prashanth/codes/ralph/projects/claudes_TASOPT.jl/TASOPT.jl/engine_sizing_flowchart.html` adapts the pattern to a different domain (turbofan thermodynamic sizing) and is the contract for the type-modularity additions (§9–§11). It demonstrates: a multi-pass `ipass` convergence loop with labeled feedback, a nested combustor+cooling micro-wrapper, a sidebar-callout pointing at an off-design Newton-loop sibling, a side-by-side types panel SVG (state containers left, components right), eleven expandable type-detail cards with Migration-status blocks (✓/✗/→), type chips on flow-node headers, and a flow-node migration-callout for the inlet step where two implementations of the same physics live in the codebase.

When in doubt about a styling choice, look at how the worked examples solved the same problem.
