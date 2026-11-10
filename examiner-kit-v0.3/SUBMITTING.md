# Submitting a result — pass or failure

A reproduced failure is worth as much as a reproduced pass. Both are
submissions; both change what can honestly be claimed.

## What to submit

Open an issue on the ARC Open Governance repository (or publish your result
wherever you publish, and link it from Issue #35), including:

1. **The exact kit archive digest** — the sha256 of the `.tar.gz` you ran,
   plus the `results_digest` printed by your run.
2. **Your unedited `results.json`** — the whole file, not a summary.
3. **Your environment, in your own words** — operating system, Python
   version (`python3 --version`), and how you extracted the archive.
4. **The divergence, stated exactly** — which test, which control, the
   expected code (from `EXPECTED.json`), and the observed code. If the
   runner refused to run (exit 2), quote the integrity message verbatim:
   a kit whose files do not match its own manifest is itself a finding.
5. **For Issue #31 runs against your own stack** — your implementation or
   source references, your frozen positive/negative controls, the relevant
   refusal or hold receipts, the independently observed effect, and any
   common-mode dependencies you know of. Honest `NOT SUPPORTED`, `FAILED`,
   and `UNKNOWN` outcomes are welcome and will be recorded as such.

## What happens to a submission

Per Issue #33's participation pathway, a submission counts when another
independently controlled examiner can reproduce it. Raw output or a
signature by itself does not count. A verified finding — one reproduced
under separate control — is what can produce an accepted correction and a
measurable change; that sequence, not attention, is the standard this
examination is run under.

## Boundaries

- No probing of third-party systems, wallets, accounts, keys, or live
  funds. The kit is synthetic by design; keep it that way.
- Participation is opt-in and publicly attributable on your own chosen
  terms. Running this kit implies no endorsement of ARC, no commitment to
  participate further, and no institutional admission.
- Nothing here activates any token, unit, or payment. None is promised.
