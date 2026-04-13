# Frontend principles

This document defines the intended frontend direction for Final Scoring.

The goal is to keep the frontend aligned with the product: a browseable, content-heavy, critic aggregation site for board games.

## Product posture

The frontend should feel like a public information product, not a SaaS dashboard and not a highly dynamic application shell.

Priority should go to:

- clarity
- legibility
- information structure
- browseability
- indexability

## Core frontend goals

The frontend should help users:

- discover games
- understand critical reception
- inspect contributing reviews
- compare games at a glance

## Page-first, content-first approach

The frontend should prioritise strong page-level experiences over complex client-side application behaviour.

Important early pages include:

- homepage or browse page
- rankings or listing page
- game detail page
- publication pages if and when they are useful

## Prefer server-friendly rendering

Given the product shape, server-oriented rendering is a good default.

The site is likely to benefit from:

- crawlable public pages
- stable content URLs
- content-heavy layouts
- low reliance on client-only state

Do not introduce large client-state architectures unless there is a clear need.

## Game pages matter most

The game detail page is one of the core product surfaces.

It should eventually make it easy to understand:

- the game identity
- the aggregate critic score
- review count
- which publications reviewed it
- the original source links
- whether reviews are scored or unscored

This page should be treated as a primary design and implementation anchor.

## Rankings and browse pages

Browse and ranking surfaces should help users answer questions like:

- which games are most highly regarded?
- which games have the most critical coverage?
- what should I look at next?

These pages should emphasise clarity and comparability over decorative interaction.

## Avoid dashboard thinking

Do not default to:

- cards everywhere with little information density
- SaaS admin aesthetics
- excessive filtering panels before the data justifies them
- flashy animated UI patterns that do not help reading

This is a content product, not internal analytics software.

## Component philosophy

Components should be:

- small
- understandable
- easy to compose
- driven by product needs

Do not create a large design system or component abstraction hierarchy too early.

## State management

Keep state management simple.

Prefer:

- route-based state
- straightforward component state where needed
- explicit data fetching
- server-friendly patterns

Avoid introducing global client-side state frameworks early unless the product clearly needs them.

## API integration

Frontend data access should be easy to trace.

Contributors should be able to tell:

- where data comes from
- which route powers which page
- how page data maps to UI output

Avoid opaque data layers or indirection-heavy abstractions too early.

## Accessibility and readability

The frontend should prioritise:

- readable typography
- sensible information hierarchy
- obvious links and actions
- accessible structure
- clear distinction between summary data and source details

## Visual polish

Visual polish matters, but MVP should not chase perfection before the content model is working.

A simple, clean, credible interface is better than a flashy but underpowered one.

## Rule of thumb

If a frontend idea makes the site feel less like a board game critic publication surface and more like a generic app template, it is probably off-track for MVP.
