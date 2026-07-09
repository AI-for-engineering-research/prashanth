# Slop lexicon — categories, rationale, how to extend

The runnable list lives in `../scripts/slop_lint.py`. Run `python3 ../scripts/slop_lint.py --list`
to dump exactly what the scanner matches. This file explains *why* each class exists, so future
edits stay principled instead of accumulating pet peeves at random.

## Why these words cost trust

In technical and scientific writing the reader assumes the author is honest, careful, and correct.
Those are the floor, not achievements. A word that *announces* the floor — "honest", "rigorous",
"to be clear" — tells the reader you felt the need to say it, which invites the doubt it was meant
to dispel. Hype words ("seamless", "powerful", "delve") and meta-narration ("it's worth noting")
add length without adding information. The reader's attention is the scarce resource; every such
word spends it for nothing.

## The classes

**HARD — almost never right in a published technical artifact. Must fix.**
- *honesty-signaling*: honest, honestly, dishonest, "to be honest", "in all honesty". Honesty is
  assumed; claiming it is a tell.
- *rhetorical certainty*: clearly, obviously, evidently, undeniably, definitive, decisive,
  conclusive. If it is clear, the evidence shows it; the adverb is a substitute for the evidence.
- *emphasis filler*: basically, truly, genuinely, fundamentally, essentially, literally, certainly.
  They modify nothing measurable.
- *meta-narration*: "it's worth noting", "it should be noted", "needless to say", "notably". If it
  is worth noting, note it; don't announce that you are about to.
- *hype*: seamless, effortless, cutting-edge, state-of-the-art, best-in-class, game-changer,
  powerful, revolutionary; verbs delve / unlock / supercharge / elevate / harness / empower; essay
  clichés "tapestry", "testament to", "in today's world", "ever-evolving", "the realm of".

**SOFT — legitimate in the right place. Review; keep only the really essential ones.**
- *minimizers*: just, simply, merely, quite, very, really. Usually deletable with no loss.
- *vague positives*: robust, powerful, elegant, clean, intuitive, trivial, easy. Often true but
  unmeasured — replace with the property that makes it so.
- *vague verbs*: leverage, utilize, facilitate (use "use" / the specific action).
- *PM jargon*: gate, tier, long pole, north star, smoking gun, fan-out, low-hanging fruit, deep
  dive. Some have real technical senses (a logic *gate*); that is why this class is review-only.
- *hedges*: of course, arguably, presumably, sort of, I think, perhaps.

**STALE — relative / temporal references that break for a cold reader. Review; almost all must go.**
This is the second, subtler problem: when an artifact is *edited* in response to feedback, the edit
itself leaks into the prose. The reader sees the diff narrated, not the fact.
- *temporal back-references*: earlier, previously, above, below, "as mentioned", "as noted".
- *authored claims*: "I claimed", "we estimated", "I updated", "my earlier figure". First-person
  edit narration almost always means session context bled into the artifact.
- *corrections*: "is incorrect", "now fixed", "the fix", "was wrong", "my mistake".
- *now-contrast*: "now shows", "no longer", "used to", "instead of the", "updated to", "changed
  from", "the previous version", "this iteration".
- *conversation leaks*: "as requested", "per your request", "you asked", "hope this helps", "let me
  know", "here's the updated".

The fix for a STALE hit is never to soften it — it is to state the **absolute** fact ("X is 4%")
or, if the artifact does not contain the fact, to remove the sentence and flag it for someone who
has the context.

## How to extend

- **Personal bans** (specific words a reader dislikes): add to `personal-bans.txt`, one regex per
  line. The linter loads that file automatically. This is the right place for ad-hoc additions.
- **A new shared class** (a pattern worth catching everywhere): add an entry to the relevant list
  in `slop_lint.py` and document the rationale here. Keep HARD tight — only words that are slop in
  ~all technical contexts. Anything context-dependent belongs in SOFT or STALE, which are
  review-only, so a false positive costs a glance, not a wrong edit.
- Patterns are case-insensitive and get `\b` word boundaries automatically. Use `\s+` between words
  so a line break inside a phrase still matches.
