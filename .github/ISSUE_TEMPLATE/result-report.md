---
name: Result report
about: Report a run of Examiner Kit v0.1 - a pass or a failure
title: "[Result] "
---

A reproduced failure is worth as much as a reproduced pass. Both are
submissions; both change what can honestly be claimed.

## Run outcome

<!-- One of: completed, all six tests ran / the runner refused to
run / the run stopped partway. Quote the runner's own summary line,
or its refusal message, verbatim. -->

## How your copy is identified

Either route stands on its own - give one:

- **Canonical archive:** the sha256 of the `examiner-kit-v0.1.tar.gz`
  you ran.
- **Repository clone:** the exact public git commit you cloned
  (the full hash) and the sha256 of
  `examiner-kit-v0.1/MANIFEST.json` in that clone.

## Results digest

<!-- The `results_digest` your run printed or wrote into
`results.json`. If the runner refused to run, say so here and quote
its integrity message verbatim under Failure detail. -->

## Environment

<!-- Operating system, Python version (`python3 --version`), and
how you obtained the kit: the canonical archive, a git clone, or
the ZIP download. -->

## Your results.json

<!-- Paste your unedited `results.json` in full, or attach the
file - not a summary. If no `results.json` was produced, say so. -->

## Failure detail

<!-- For a divergence: which test, which control, the expected code
(from `EXPECTED.json`) and the observed code. For a refusal: the
integrity message, verbatim. Delete this section for a clean pass. -->
