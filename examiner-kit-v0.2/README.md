# ARC Examiner Kit v0.2

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

## What changed in v0.2

v0.2 corrects exactly two defects, and nothing else. Both were raised as
candidates by an outside source-level audit of v0.1 and then CONFIRMED at
fixture strength by a governed reproduction run by the issuing desk
(examination record, 2026-11-01) before any correction was written. The
adversarial tests that encode the reproductions (`kit/adversarial_tests.py`,
tests A1 and A2) were written first and run against the uncorrected
engine — where they failed in exactly the reproduced places — before the
engine was changed.

1. **Receipt-field completeness (A1).** v0.1's `verify_receipt` compared
   the request digest, the approval's signature, and one gated poststate
   match — and nothing else in the receipt body. Altering a receipt's
   stated object, prestate digest, sequence number, or approval digest
   each left the altered receipt verified. v0.2's verifier compares
   every receipt field against the authoritative record (the stored
   request, the stored signed approval, and the gated store-history
   entry), and each single-field alteration is now rejected.
2. **Multilevel revocation (A2).** v0.1 detected revoked ancestry
   transitively but enforced revocation only at the presented request's
   direct `depends_on`: after revoking A in the chain A <- B <- C, new
   actions depending on B or on C were admitted. v0.2's enforcement
   walks the declared ancestry, so reliance on a revoked request
   through any declared intermediate is refused (`dependency_revoked`) —
   enforcement now matches the detection v0.1 already reported.

The six original tests are byte-identical to v0.1 and their frozen
expectations are unchanged; all twelve original controls pass with the
same outcome codes. v0.1 is preserved, frozen, exactly as published
(canonical archive sha256
`cc93961bbf37f6eea3b462581302178213e2859299e8efd37be0f3593840d6de`;
v0.1 results_digest
`sha256:e685155a7ad99257613fa7278f3b39664fcf361e54578d13774067fd42773b60`)
— v0.2 succeeds it; it does not rewrite it. A declared dependence cycle
remains unconstructible in both versions, because a `request_id` is a
content digest over `depends_on`; A2 states this as a structural
control rather than claiming cycle behavior in either direction.

## Run it

```sh
python3 run_exam.py
```

From the kit root. Python 3, standard library only. The runner verifies the
kit's own files against `MANIFEST.json`, verifies the frozen fixtures, runs
all six tests (each with a positive and a negative control) and the two
v0.2 adversarial tests, compares every outcome against `EXPECTED.json`,
writes a machine-readable `results.json`, and exits 0 only if every
control matched its frozen expectation.

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

v0.2 adds two narrower claims, at the same local strength: that the fixture
verifier compares every receipt field against the authoritative record
(A1), and that fixture revocation enforcement walks the declared ancestry
(A2). Both are properties of this fixture, established by the adversarial
tests shipped in this kit — and by nothing else.

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
| `kit/engine.py` | The fixture reference engine (strength statement on its face; v0.2 carries the two corrections) |
| `kit/fixtures.py` | The frozen inputs (state S0, all requests) |
| `kit/tests.py` | The six tests, controls, claims, strength lines (byte-identical to v0.1) |
| `kit/adversarial_tests.py` | The two v0.2 adversarial tests (A1, A2): the corrections' regression proof |
| `fixtures/fixture-manifest.json` | Digests pinning every frozen input |
| `EXPECTED.json` | The frozen expected outcome of every control (original section unchanged from v0.1; v0.2 adds the adversarial section) |
| `MANIFEST.json` | sha256 of every file in this kit (verified before every run) |
| `EXAM.md` | The six tests in prose, with scope and caveats, plus A1/A2 |
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
