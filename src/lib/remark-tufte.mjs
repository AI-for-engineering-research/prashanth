import { visit } from 'unist-util-visit';
import fs from 'node:fs';
import path from 'node:path';

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
    default:
      // Unknown block/inline: serialize any children, else its raw value.
      if (node.children) return node.children.map(inline).join('');
      return node.value ? esc(node.value) : '';
  }
}

// Join a definition's block children (usually one paragraph) into inline HTML.
function renderBlocks(children) {
  return children.map(inline).join('<br>');
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

    // 3. Directives: :::aside (unnumbered margin note) and ::figure{id,caption}.
    visit(tree, (node) => {
      if (node.type !== 'containerDirective' && node.type !== 'leafDirective') return;

      if (node.name === 'aside') {
        const body = renderBlocks(node.children || []);
        node.type = 'html';
        node.value = `<span class="sidenote marginnote">${body}</span>`;
        node.children = [];
        return;
      }

      if (node.name === 'figure') {
        const attrs = node.attributes || {};
        const id = attrs.id;
        let svg = '';
        if (id) {
          const file = path.join(process.cwd(), 'figures', `${id}.svg`);
          try {
            svg = fs.readFileSync(file, 'utf8');
          } catch {
            svg = `<!-- figure '${id}' not found: run \`npm run figures\` -->`;
          }
        }
        // Caption can come from an attribute or the directive body.
        const caption = attrs.caption || (node.children ? renderBlocks(node.children) : '');
        const cls = attrs.class ? ` ${attrs.class}` : '';
        node.type = 'html';
        node.children = [];
        node.value =
          `<figure class="figure${cls}">${svg}` +
          (caption ? `<figcaption>${caption}</figcaption>` : '') +
          `</figure>`;
      }
    });
  };
}
