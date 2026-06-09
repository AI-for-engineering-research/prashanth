import { defineConfig } from 'astro/config';
import remarkDirective from 'remark-directive';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { remarkTufte } from './src/lib/remark-tufte.mjs';

// Static site deployed to GitHub Pages as a project site, hence the base
// subpath. Internal links read import.meta.env.BASE_URL so they stay correct.
export default defineConfig({
  site: 'https://ai-for-engineering-research.github.io',
  base: '/prashanth',
  markdown: {
    // gfm (footnotes, tables) is on by default. remarkDirective parses
    // `:::aside` / `:::figure{...}`; remarkTufte rewrites footnotes into
    // Tufte sidenotes and expands the directives. Order matters:
    // directive parser first, then our transform.
    // remarkMath parses $…$/$$…$$ into math nodes; rehypeKatex renders them to
    // static HTML at build time (zero runtime JS). KaTeX CSS is imported in
    // Base.astro so the glyphs lay out correctly.
    remarkPlugins: [remarkMath, remarkDirective, remarkTufte],
    rehypePlugins: [rehypeKatex],
    // We emit raw HTML (the sidenote checkbox markup), so don't sanitize it away.
    gfm: true,
    smartypants: true,
  },
});
