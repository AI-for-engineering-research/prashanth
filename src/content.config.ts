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

export const collections = { log };
