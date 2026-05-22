# Frontend

Placeholder. The frontend stack decision is deliberately deferred
until the backend is producing real data — Phase 4 in the roadmap.

## Likely choice

Next.js with server-rendered or static-exported pages, reading from
the baked SQLite database at build time (or at request time via a
small read-only data layer). The current placeholder at
<https://finalscoring.games/> is not authoritative — none of its
choices are committed to.

## Constraints from the mantras

Whatever stack lands here must:

- Ship without third-party analytics, ad pixels, or telemetry.
- Self-host fonts (no Google Fonts).
- Use privacy-preserving embeds for any video (e.g. `youtube-nocookie.com`
  or thumbnail-link-out).
- Be open-source-compatible with the AGPLv3 license.

## Constraints from the architecture

- The runtime database is a read-only SQLite file baked into the image.
- No live writes, no user accounts, no sessions.
- Build cadence is weekly; the frontend can lean on this for caching
  and static generation.

## When to fill this in

After Phase 3 (aggregation + scoring) is producing meaningful data
against at least one real critic source. Designing a frontend against
imagined data leads to either too-generic surfaces or surfaces that
don't survive contact with real reviews.
