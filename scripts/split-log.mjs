// Split the single authored WeeklyLog.md into one markdown file per week for
// the Astro `log` content collection. Run via `npm run content` (called before
// dev/build). You keep writing in WeeklyLog.md; this regenerates the per-week
// files — they're gitignored, not hand-edited.
//
// Convention: `## <title>` starts a new week; `###` and below are its body.
// Anything before the first `##` (the H1, intro) is ignored.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(import.meta.dirname, '..');
export const SOURCE = path.join(ROOT, 'WeeklyLog.md');
const OUT = path.join(ROOT, 'src', 'content', 'log');

const slugify = (s) =>
  s.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

const yamlStr = (s) => JSON.stringify(s);             // safe-quote for YAML scalars

export function splitLog({ quiet = false } = {}) {
  const lines = fs.readFileSync(SOURCE, 'utf8').split('\n');

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
    if (!cur) continue;                                // skip H1/intro before first week
    const sub = /^###\s+(.+?)\s*$/.exec(line);
    if (sub) cur.topics.push(sub[1]);
    cur.body.push(line);
  }

  // Rewrite the output dir from scratch so renamed/removed weeks don't linger.
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });

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
    if (!quiet) console.log(`wrote src/content/log/${slug}.md`);
  });

  if (!quiet) console.log(`split ${weeks.length} week(s)`);
  return weeks.length;
}

// Run directly (npm run content); the dev-server integration imports splitLog.
if (process.argv[1] === fileURLToPath(import.meta.url)) splitLog();
