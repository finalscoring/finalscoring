# 003 — AGPLv3 license

**Status:** Accepted.
**Date:** 2026-05.

## Context

The "100% open source, full transparency" mantra commits Final Scoring
to publishing its code, prompts, methodology, and editorial state.
The license choice determines whether that openness propagates to
derivatives, and in particular to anyone running a modified version
as a network service.

Three options were on the table: permissive (MIT/BSD), strong
copyleft with SaaS provision (AGPLv3), and source-available with
commercial restrictions (BSL, Elastic, SSPL).

Source-available licenses are not OSI-recognised open source. Picking
one would directly contradict the "100% open source" mantra. They
were ruled out.

Between MIT and AGPL: MIT maximizes adoption, AGPL preserves the
openness commitment for derivatives. For a project whose brand is
credibility and whose mantra explicitly invokes transparency, the
case for AGPL is stronger — a closed-source fork running Final
Scoring's methodology with private modifications would directly
undermine the brand.

## Decision

All code, prompts, methodology documents, and editorial data in this
repository are licensed AGPLv3 (`SPDX-License-Identifier:
AGPL-3.0-or-later`). The full license text is in `LICENSE`.

## Consequences

**Committed to:**
- Anyone running a modified version as a network service must
  publish their modifications under the same terms.
- Some corporations will not touch this codebase. That cost is
  accepted — Final Scoring is not seeking corporate adoption.
- Contributions are licensed under the same terms.

**Precluded:**
- Embedding Final Scoring code in a closed-source product.
- Relicensing in the future without contributor consent.

## Reversibility

Low. Relicensing would require consent from all contributors and is
not anticipated. The license should be considered a permanent
commitment.
