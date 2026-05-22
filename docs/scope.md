# Scope

What Final Scoring does and doesn't do. This document exists to make
"no" answers fast and consistent.

## In scope

- Ingestion of critic and reviewer opinion on board games from text,
  video, and podcast sources.
- Structured extraction of per-(critic, game) reviews with attribution,
  short verbatim quotes, and AI-written summaries.
- Per-critic normalization and tier-weighted aggregation into a
  per-game score with confidence interval.
- Browse, search, and filter across games and critics.
- A public methodology page documenting how all the above works.
- Multilingual operation (English and German at launch; other
  languages as additional sources come online).

## Out of scope, permanently

These belong in other projects, not in Final Scoring.

- **User accounts.** No login, no profiles.
- **Community ratings.** That's BGG's role.
- **Comments or discussion.** That's BGG / Reddit / Discord.
- **Recommendations.** That's [Recommend.Games][rg].
- **Collection management** (owned games, wishlist, plays). That's BGG.
- **Marketplace integration** (buy links, price tracking).
- **A general-purpose board game database.** Game metadata is imported
  from Recommend.Games (which in turn sources from BGG).
- **Editorial publications written by us.** No "game of the week",
  no awards lists, no editorial picks. We aggregate critic opinion;
  we don't add our own.

## Deferred to later phases

These are not v1, but are not permanently excluded.

- **Video review ingestion.** Whisper transcription is solved
  technically but operationally heavy. v2 candidate.
- **Podcast ingestion.** Same shape as video; deferred to v2/v3.
- **Themed consensus summaries** (the "what stands out / main caution
  / score shape" feature). v2.
- **Critic-impact-derived weighting** (data-driven source tiers based
  on downstream impact). v3, requires longitudinal data.
- **Additional languages beyond English and German.** Driven by source
  availability.

## The test

When a feature idea arrives, ask: *does this make critical reception
more legible to a hobbyist looking at a game?*

- If yes, it's a candidate. Add to the roadmap.
- If it's social, generative, or competitive with BGG, it's a no.
- If it's an editorial publication of our own opinions, it's a no.
- If it requires writable state in production, it's almost certainly a no.

[rg]: https://recommend.games/
