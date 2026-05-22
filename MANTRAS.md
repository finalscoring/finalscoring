# Mantras

These three lines exist to make scope decisions easy. When a feature idea,
a tool, or a tempting integration arrives, it gets checked against these
first. Anything that violates one of them is out — not deferred, not
"maybe later", out.

## 1. No tracking, ever.

No analytics that phone home to third parties. No Google Fonts. No
default YouTube embeds (use `youtube-nocookie.com` or thumbnail-link-out).
No Sentry SaaS. No third-party A/B testing. No remarketing pixels.

Self-hosted analytics (Plausible, Umami) are acceptable if and only if
they store no identifying information. The default position is: no
analytics at all.

Concrete consequences:
- Frontend hosting must allow shipping without inserted scripts.
- Fonts are self-hosted or system stacks.
- Embedded media uses privacy-preserving variants.
- Error monitoring, if any, is self-hosted.

## 2. 100% open source, full transparency.

Everything in this repository is licensed AGPLv3. That includes code,
LLM prompts, scoring methodology, source tier assignments, and override
tables. There is no "secret sauce" — if it influences a score, it is
public, in git, and reviewable.

Concrete consequences:
- Prompts live in `prompts/` as versioned files, not as Python strings
  buried in code.
- Source tier weights live in a data file under version control, not in
  a private spreadsheet.
- The methodology page on the live site is generated from the same
  document committed to this repository.
- Anyone running a derived service must also be open about it (AGPLv3).

## 3. Single-minded focus on the mission: board game review aggregation.

Final Scoring is a critic index for board games. Not a community site.
Not a database. Not a recommender. Not a marketplace. Not a forum.

When tempted to add a feature, the test is: *does this make critical
reception more legible to a hobbyist looking at a game?* If not, it
doesn't belong here.

Concrete consequences:
- Permanently out of scope: user accounts, ratings, comments, lists,
  social features, recommendations, collection management, marketplaces,
  price tracking, BGG-style community ratings.
- Game metadata is *imported*, not curated here. Recommend.Games owns
  that domain.
- The homepage is deliberately quiet — it explains what Final Scoring
  is and lets people find games. It is not an editorial publication.

---

These mantras are deliberately short and absolute. The full plan for the
project, including roadmap and architecture, lives in `docs/`.
