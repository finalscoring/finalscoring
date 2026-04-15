# Frontend principles

Defines frontend direction for Final Scoring.

Goal: keep frontend aligned with product — browseable, content-heavy, critic aggregation site for board games.

## Product posture

Should feel like public information product. Not SaaS dashboard. Not highly dynamic app shell.

Priority:

- clarity
- legibility
- information structure
- browseability
- indexability

## Core frontend goals

Help users:

- discover games
- understand critical reception
- inspect contributing reviews
- compare games at a glance

## Page-first, content-first approach

Prioritise strong page-level experiences over complex client-side behaviour.

Key early pages:

- homepage or browse page
- rankings or listing page
- game detail page
- publication pages if useful

## Prefer server-friendly rendering

Server-oriented rendering is good default given product shape.

Benefits:

- crawlable public pages
- stable content URLs
- content-heavy layouts
- low reliance on client-only state

No large client-state architectures without clear need.

## Game pages matter most

Game detail page = core product surface.

Should make easy to understand:

- game identity
- aggregate critic score
- review count
- which publications reviewed it
- original source links
- whether reviews scored or unscored

Treat as primary design and implementation anchor.

## Rankings and browse pages

Help users answer:

- which games most highly regarded?
- which games have most critical coverage?
- what to look at next?

Emphasise clarity and comparability over decorative interaction.

## Avoid dashboard thinking

Don't default to:

- cards everywhere with low information density
- SaaS admin aesthetics
- excessive filtering panels before data justifies them
- flashy animated UI that doesn't help reading

Content product, not internal analytics software.

## Component philosophy

Components should be:

- small
- understandable
- easy to compose
- driven by product needs

No large design system or component abstraction hierarchy too early.

## State management

Keep simple.

Prefer:

- route-based state
- straightforward component state where needed
- explicit data fetching
- server-friendly patterns

No global client-side state frameworks early unless clearly needed.

## API integration

Data access should be easy to trace.

Contributors should know:

- where data comes from
- which route powers which page
- how page data maps to UI output

No opaque data layers or indirection-heavy abstractions early.

## Accessibility and readability

Prioritise:

- readable typography
- sensible information hierarchy
- obvious links and actions
- accessible structure
- clear distinction between summary data and source details

## Visual polish

Matters, but MVP shouldn't chase perfection before content model works.

Simple, clean, credible > flashy but underpowered.

## Rule of thumb

Frontend idea makes site feel less like board game critic publication surface and more like generic app template → off-track for MVP.