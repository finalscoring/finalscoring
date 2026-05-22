# AGENTS.md

Operating rules for any agent working in this repo. Read `docs/PROJECT.md`
(what's decided), `docs/DECISIONS_OPEN.md` (what's not — never decide these
yourself), and `docs/BUILD_NOTES.md` (suggested commit sequence) before
starting.

## Mantras

- **Be concise. Nobody reads walls of text.**
- **Small, reviewable change sets.** One concern per commit — what an
  experienced dev who wants their code reviewed would submit. Stop after
  each chunk for review.
- **Ask, don't assume.** If a decision isn't made, ask. Never assume
  tooling, platforms, services, or design choices. Do the literal scope
  of the request and nothing more.
- **The maintainer owns design.** Propose options; let them choose.
  Architecture and design decisions are theirs.
- **Git history is sacrosanct.** Never rewrite history (rebase, amend,
  force-push, reset, history-altering tags) unless very explicitly
  approved.
- **Never publish without instruction.** No commit, push, merge, tag,
  release, post, or deploy unless explicitly told to.
- **Approval doesn't carry over.** Any approval covers only the concrete
  task at hand. It never implicitly extends to future commands.

## Project facts that constrain your work

- **Python 3.14.** This is a project, not a library — favour reliability
  and concreteness over generalisation.
- **GitLab, not GitHub.** Never introduce GitHub, GitHub Actions, or
  GitHub-specific tooling/URLs. Don't assume any CI provider, registry,
  or host that hasn't been chosen.
- **Tooling:** ruff (lint + format), ty (type check), pytest. Package is
  typed. Keep the repo installable and green after every chunk.
- **License:** AGPLv3, whole repo.
- **Don't fabricate exact content** (license text, etc.). If it can't be
  obtained correctly, leave it out and flag it.

## Existing assets — reference, don't copy

- The Spiel des Jahres spider + LLM pipeline are proof-of-concept to
  learn from, not components to port wholesale. See `docs/SDJ_PIPELINE_NOTES.md`.
- Game data and BGG matching come from the maintainer's Recommend.Games
  project, not rebuilt. Integration mechanism is undecided.
- Scoring logic is sketched in `docs/SCORING_SKETCH.md`; the algorithm shape
  is agreed but all parameters are open.
