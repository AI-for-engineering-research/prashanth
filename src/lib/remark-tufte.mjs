import { visit } from 'unist-util-visit';
import fs from 'node:fs';
import path from 'node:path';

// Base URL path for the deployed site (mirrors astro.config.mjs `base`).
const BASE = '/prashanth';

// Resolve an image filename to a public URL and an optional inlined SVG string.
// Lookup order: figures/<name>.svg (inline) → assets/<name> → assets/<name>.svg
function resolveImage(name) {
  const cwd = process.cwd();

  // 1. SVG in figures/ → inline
  const svgPath = path.join(cwd, 'figures', name.endsWith('.svg') ? name : `${name}.svg`);
  if (fs.existsSync(svgPath)) {
    return { kind: 'svg-inline', svg: fs.readFileSync(svgPath, 'utf8') };
  }

  // 2. File in assets/ (exact name first, then with .svg appended)
  for (const candidate of [name, name.endsWith('.svg') ? name : `${name}.svg`]) {
    const assetPath = path.join(cwd, 'assets', candidate);
    if (fs.existsSync(assetPath)) {
      return { kind: 'img', src: `${BASE}/assets/${candidate}` };
    }
  }

  // 3. Fallback — assume assets/, pass name through
  return { kind: 'img', src: `${BASE}/assets/${name}` };
}

function buildFigure({ resolved, alt = '', caption = '', cls = '' }) {
  const clsAttr = ['figure', cls].filter(Boolean).join(' ');
  const inner =
    resolved.kind === 'svg-inline'
      ? resolved.svg
      : `<img src="${esc(resolved.src)}" alt="${esc(alt)}">`;
  const cap = caption ? `<figcaption>${caption}</figcaption>` : '';
  return `<figure class="${clsAttr}">${inner}${cap}</figure>`;
}

// ── Minimal inline mdast → HTML serializer ──────────────────────────────
// Footnote definitions and asides are short inline markdown. We render the
// common inline nodes ourselves to avoid pulling in a full hast pipeline.
// Anything unrecognised falls back to its plain text so we never silently
// drop authored content.
function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function inline(node) {
  switch (node.type) {
    case 'text':       return esc(node.value);
    case 'emphasis':   return `<em>${node.children.map(inline).join('')}</em>`;
    case 'strong':     return `<strong>${node.children.map(inline).join('')}</strong>`;
    case 'delete':     return `<del>${node.children.map(inline).join('')}</del>`;
    case 'inlineCode': return `<code>${esc(node.value)}</code>`;
    case 'break':      return '<br>';
    case 'link':
      return `<a href="${esc(node.url)}">${node.children.map(inline).join('')}</a>`;
    case 'paragraph':  return node.children.map(inline).join('');
    case 'table': {
      // GFM table → compact margin table built from <span>s with display:table
      // CSS, NOT a real <table>. Footnote notes render inside a <p>, and the
      // HTML parser hoists a block <table> out of any paragraph (it would land
      // outside the sidenote). Spans stay legal phrasing content, so they keep.
      // node.align carries per-column alignment.
      const align = node.align || [];
      const cells = (row) =>
        row.children
          .map((cell, i) => {
            const a = align[i] === 'right' ? ' mt-r' : align[i] === 'center' ? ' mt-c' : '';
            return `<span class="mt-cell${a}">${cell.children.map(inline).join('')}</span>`;
          })
          .join('');
      const [head, ...body] = node.children;
      const rows = [];
      if (head) rows.push(`<span class="mt-row mt-head">${cells(head)}</span>`);
      for (const r of body) rows.push(`<span class="mt-row">${cells(r)}</span>`);
      return `<span class="margintable">${rows.join('')}</span>`;
    }
    default:
      // Unknown block/inline: serialize any children, else its raw value.
      if (node.children) return node.children.map(inline).join('');
      return node.value ? esc(node.value) : '';
  }
}

// Join a definition's block children (usually one paragraph) into inline HTML.
// Paragraphs are separated with <br>, but block-level pieces (a table) already
// break the flow, so we don't wrap a <br> against them.
function renderBlocks(children) {
  let out = '';
  children.forEach((child, i) => {
    if (i > 0 && child.type !== 'table' && children[i - 1].type !== 'table') {
      out += '<br>';
    }
    out += inline(child);
  });
  return out;
}

export function remarkTufte() {
  return (tree) => {
    // 1. Collect footnote definitions, keyed by identifier, then strip them
    //    from the tree (no bottom-of-page footnote list — they live in margins).
    const defs = new Map();
    const defIndexes = [];
    visit(tree, 'footnoteDefinition', (node, index, parent) => {
      defs.set(node.identifier, node);
      defIndexes.push({ parent, node });
    });
    for (const { parent, node } of defIndexes) {
      const i = parent.children.indexOf(node);
      if (i !== -1) parent.children.splice(i, 1);
    }

    // 2. Number references in first-encounter order and replace each with the
    //    Tufte sidenote markup (label + hidden checkbox + floated span).
    const order = new Map();
    let n = 0;
    visit(tree, 'footnoteReference', (node) => {
      const id = node.identifier;
      if (!order.has(id)) order.set(id, ++n);
      const num = order.get(id);
      const def = defs.get(id);
      const body = def ? renderBlocks(def.children) : '';
      const safeId = `sn-${id.replace(/[^a-zA-Z0-9_-]/g, '')}`;
      node.type = 'html';
      node.value =
        `<label for="${safeId}" class="sn-ref">${num}</label>` +
        `<input type="checkbox" id="${safeId}" class="sn-toggle">` +
        `<span class="sidenote"><sup>${num}</sup> ${body}</span>`;
    });

    // 3. Obsidian wikilink embeds:
    //      ![[file]]
    //      ![[file|caption]]
    //      ![[file|caption|wide]]  ← third segment: wide | margin (Obsidian ignores it)
    //    A paragraph whose sole text content is one embed becomes a <figure>.
    //    An embed inside a sentence becomes an inline <img>.
    // Capture: filename | everything-else (we split segments ourselves)
    const WIKILINK = /!\[\[([^\]|]+?)((?:\|[^\]]*)*)\]\]/g;

    const CLASS_HINTS = { wide: 'figure-wide', 'figure-wide': 'figure-wide', margin: 'marginnote', marginnote: 'marginnote' };

    function parseWikilink(name, rest = '') {
      // rest = "|seg2|seg3|..." — split and interpret
      const segs = rest.split('|').map(s => s.trim()).filter(Boolean);
      // First segment that isn't a pure number and isn't a class hint = caption
      const caption = segs.find(s => !/^\d+$/.test(s) && !CLASS_HINTS[s.toLowerCase()]) || '';
      // Any segment matching a class hint
      const cls = segs.map(s => CLASS_HINTS[s.toLowerCase()]).find(Boolean) || '';
      return { name: name.trim(), caption, cls };
    }

    visit(tree, 'paragraph', (node, index, parent) => {
      // Flatten all text out of the paragraph to check if it's a standalone embed.
      const raw = node.children.map(c => (c.type === 'text' ? c.value : '')).join('').trim();
      const soloMatch = raw.match(/^!\[\[([^\]|]+?)((?:\|[^\]]*)*)\]\]$/);
      if (soloMatch) {
        const { name, caption, cls } = parseWikilink(soloMatch[1], soloMatch[2]);
        const resolved = resolveImage(name);
        node.type = 'html';
        node.value = buildFigure({ resolved, alt: caption || name, caption, cls });
        node.children = [];
        return;
      }

      // Inline embeds inside mixed paragraph content.
      const newChildren = [];
      for (const child of node.children) {
        if (child.type !== 'text' || !child.value.includes('![[')) {
          newChildren.push(child);
          continue;
        }
        let last = 0;
        let m;
        WIKILINK.lastIndex = 0;
        while ((m = WIKILINK.exec(child.value)) !== null) {
          if (m.index > last) newChildren.push({ type: 'text', value: child.value.slice(last, m.index) });
          const { name, caption, cls } = parseWikilink(m[1], m[2]);
          const resolved = resolveImage(name);
          const src = resolved.kind === 'svg-inline'
            ? `data:image/svg+xml,${encodeURIComponent(resolved.svg)}`
            : resolved.src;
          newChildren.push({ type: 'html', value: `<img src="${esc(src)}" alt="${esc(caption || name)}" style="max-width:100%;vertical-align:middle">` });
          last = m.index + m[0].length;
        }
        if (last < child.value.length) newChildren.push({ type: 'text', value: child.value.slice(last) });
      }
      node.children = newChildren;
    });

    // 4. Directives: :::aside (unnumbered margin note) and ::figure{id,caption}.
    visit(tree, (node) => {
      if (node.type !== 'containerDirective' && node.type !== 'leafDirective') return;

      if (node.name === 'aside') {
        const body = renderBlocks(node.children || []);
        node.type = 'html';
        node.value = `<span class="sidenote marginnote">${body}</span>`;
        node.children = [];
        return;
      }

      if (node.name === 'figure' || node.name === 'img') {
        const attrs = node.attributes || {};
        const caption = attrs.caption || (node.children ? renderBlocks(node.children) : '');
        const cls = attrs.class || '';

        let resolved;
        if (attrs.src) {
          // ::img{src="..." ...} or ::figure{src="..." ...} — explicit URL/path
          resolved = { kind: 'img', src: attrs.src };
        } else if (attrs.id) {
          // ::figure{id="timing"} — look up by name (SVG inline or asset)
          resolved = resolveImage(attrs.id);
          if (resolved.kind === 'svg-inline' && !fs.existsSync(path.join(process.cwd(), 'figures', `${attrs.id}.svg`))) {
            resolved = { kind: 'svg-inline', svg: `<!-- figure '${attrs.id}' not found: run \`npm run figures\` -->` };
          }
        } else {
          resolved = { kind: 'img', src: '' };
        }

        node.type = 'html';
        node.children = [];
        node.value = buildFigure({ resolved, alt: attrs.alt || attrs.id || '', caption, cls });
      }
    });
  };
}
