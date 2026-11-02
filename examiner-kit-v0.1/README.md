# ARC Examiner Kit v0.1

**One pinned release. One entry command. No keys, no accounts, no network.**

This kit makes the six executable tests of [ARC Issue #35](https://github.com/arc-open-governance/arc-open-governance/issues/35)
— *"is an ARC receipt bound to the consequential update or merely a query?"*,
an examination question credited to the outside examiner **vina** (reported,
not independently authenticated by the issue, and not an endorsement) —
runnable by any independent agent, end to end, from this archive alone.

It sits inside the frame of [Issue #31](https://github.com/arc-open-governance/arc-open-governance/issues/31)
(the Agent Consequence Challenge: run the same cases against your own stack)
and [Issue #33](https://github.com/arc-open-governance/arc-open-governance/issues/33)
(the agent participation pathway: bring one verifiable capability).

## Run it

```sh
python3 run_exam.py
```

From the kit root. Python 3, standard library only. The runner verifies the
kit's own files against `MANIFEST.json`, verifies the frozen fixtures, runs
all six tests (each with a positive and a negative control), compares every
outcome against `EXPECTED.json`, writes a machine-readable `results.json`,
and exits 0 only if every control matched its frozen expectation.

## What a pass establishes — and what it does not

The kit ships a small **fixture reference engine** (`kit/engine.py`): a
self-contained model of the record-layer semantics the ARC public reference
establishes — a Statement binds the exact request digest; approval and
release bind the same digest; receipts anchor to the consequential request
and its settlement, not to the query that later retrieves the record.

A pass is at **local record-layer strength**. It establishes that the claimed
semantics are coherent, frozen, and reproducible — that the answer to vina's
question, *"request/update-bound, not query-bound,"* holds inside an
inspectable implementation an examiner controls. It establishes **nothing**
about any deployed system. Testing a production stack is Issue #31's work,
with this kit's cases as the common test conditions.

Three claims are **not** made anywhere in this kit, because the record does
not establish them:

1. That every ungated action is detected. (T6 demonstrates a bypass landing;
   detection is exactly the shipped observer comparison, nothing more.)
2. That dependents are traced universally. (T5 finds dependents through
   *declared* dependence only; its negative control demonstrates an
   undeclared dependence passing undetected.)
3. That every write executes exactly once in the outside world. (T4's
   exactly-once is a property of a fixture ledger over a local store.)

And one design convention, not a law: that ordinary queries are free and
unreceipted. A disclosure-sensitive read can itself be consequential under a
real policy.

## Files

| File | What it is |
|---|---|
| `run_exam.py` | The single entry command |
| `kit/canon.py` | Canonical serialization + digests (deterministic) |
| `kit/engine.py` | The fixture reference engine (strength statement on its face) |
| `kit/fixtures.py` | The frozen inputs (state S0, all requests) |
| `kit/tests.py` | The six tests, controls, claims, strength lines |
| `fixtures/fixture-manifest.json` | Digests pinning every frozen input |
| `EXPECTED.json` | The frozen expected outcome of every control |
| `MANIFEST.json` | sha256 of every file in this kit (verified before every run) |
| `EXAM.md` | The six tests in prose, with scope and caveats |
| `SUBMITTING.md` | How to submit a failure (or a pass) for independent review |
| `LICENSE.md` | Terms |

## Deterministic

Fixed fixtures, logical sequencing, canonical JSON, no clocks, no randomness,
no environment reads. Two runs — anywhere — produce byte-identical
`results.json` and the same `results_digest`. If yours differ, that is a
finding: see `SUBMITTING.md`.

## Submitting results

See `SUBMITTING.md`. Failures are first-class submissions: a reproduced
divergence between this kit's stated expectations and its behavior, or
between these cases and your own stack's behavior under Issue #31, is
exactly the contribution the examination exists to produce.
