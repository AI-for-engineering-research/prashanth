# Build

## Update + preview (every time)
1. edit `WeeklyLog.md` (log) or `PowerCycles_Overview.md` (project page). plain markdown.
2. `npm run dev`
3. open http://localhost:4321 — auto-reloads on save.
4. ctrl-C to stop.

## Publish
`npm run build` -> output in `dist/`. upload `dist/` to host. done.
(build + dev auto-run figures first.)

## first time / new machine
`npm install` once. need installed: node, uv (figures use uv).

## margin + special syntax (inside the markdown)
- numbered sidenote: `word[^x]` ... then on its own line: `[^x]: note text`
- margin note (no number): line `:::aside`, text, line `:::`
- figure: `::figure{id="timing" caption="..."}`  (id = svg file in figures/)
- math: `$x^2$` inline, `$$x^2$$` display
- new week: `## Week N`

## figures (only when changing a chart)
1. numbers -> `data/benchmark.json`
2. plot code -> `scripts/figures.py` (matplotlib, saves `figures/<id>.svg`)
3. rebuild. reference with `::figure{id="<id>"}`

## footer date = build date, auto. don't touch.
