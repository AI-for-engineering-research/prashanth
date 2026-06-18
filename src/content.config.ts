import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// The `log` collection is generated from WeeklyLog.md by scripts/split-log.mjs
// (npm run content). One markdown file per week, rendered through the same
// markdown pipeline (remarkTufte, KaTeX, directives) as the rest of the site.
const log = defineCollection({
  loader: glob({ pattern: '*.md', base: './src/content/log' }),
  schema: z.object({
    title: z.string(),
    order: z.number(),
    topics: z.array(z.string()).default([]),
  }),
});

// One markdown file per project, authored by hand in the root `projects/`
// folder (unlike `log`, there's no split step — each project is already its own
// file). Files whose name starts with `_` (e.g. _template.md) are ignored, so
// they can serve as scaffolds without ever publishing.
const projects = defineCollection({
  loader: glob({ pattern: '[!_]*.md', base: './projects' }),
  schema: z.object({
    title: z.string(),
    summary: z.string().default(''),
    status: z.string().optional(),
    order: z.number().default(99),
  }),
});

export const collections = { log, projects };
