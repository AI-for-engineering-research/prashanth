// Split the single authored WeeklyLog.md into one markdown file per week for
// the Astro `log` content collection. Run via `npm run content` (called before
// dev/build). You keep writing in WeeklyLog.md; this regenerates the per-week
// files — they're gitignored, not hand-edited.
//
// Convention: `## <title>` starts a new week; `###` and below are its body.
// Anything before the first `##` (the H1, intro) is ignored.
import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(import.meta.dirname, '..');
const SRC = path.join(ROOT, 'WeeklyLog.md');
const OUT = path.join(ROOT, 'src', 'content', 'log');

const slugify = (s) =>
  s.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

const md = fs.readFileSync(SRC, 'utf8');
const lines = md.split('\n');

// Carve into weeks at each level-2 heading.
const weeks = [];
let cur = null;
for (const line of lines) {
  const m = /^##\s+(.+?)\s*$/.exec(line);
  if (m && !line.startsWith('###')) {
    cur = { title: m[1], body: [], topics: [] };
    weeks.push(cur);
    continue;
  }
  if (!cur) continue;                                  // skip H1/intro before first week
  const sub = /^###\s+(.+?)\s*$/.exec(line);
  if (sub) cur.topics.push(sub[1]);
  cur.body.push(line);
}

// Rewrite the output dir from scratch so renamed/removed weeks don't linger.
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT, { recursive: true });

const yamlStr = (s) => JSON.stringify(s);             // safe-quote for YAML scalars
weeks.forEach((w, i) => {
  const slug = slugify(w.title);
  const fm = [
    '---',
    `title: ${yamlStr(w.title)}`,
    `order: ${i + 1}`,
    w.topics.length === 0 ? 'topics: []' : 'topics:',
    ...w.topics.map((t) => `  - ${yamlStr(t)}`),
    '---',
    '',
  ].join('\n');
  const body = w.body.join('\n').replace(/^\n+/, '').replace(/\n+$/, '') + '\n';
  fs.writeFileSync(path.join(OUT, `${slug}.md`), fm + body);
  console.log(`wrote src/content/log/${slug}.md`);
});

console.log(`split ${weeks.length} week(s)`);
