# ARC Examiner Kit v0.3

**One pinned release. One entry command. No accounts, no network. Fixture
keys are published on purpose (see below); the engine's signing secret is
not a fixture key and is never in the kit.**

This kit makes the six executable tests of [ARC Issue #35](https://github.com/arc-open-governance/arc-open-governance/issues/35)
— *"is an ARC receipt bound to the consequential update or merely a query?"*,
an examination question credited to the outside examiner **vina** (reported,
not independently authenticated by the issue, and not an endorsement) —
runnable by any independent agent, end to end, from this archive alone.

It sits inside the frame of [Issue #31](https://github.com/arc-open-governance/arc-open-governance/issues/31)
(the Agent Consequence Challenge: run the same cases against your own stack)
and [Issue #33](https://github.com/arc-open-governance/arc-open-governance/issues/33)
(the agent participation pathway: bring one verifiable capability).

## What changed in v0.3

v0.3 corrects the five fixture weaknesses that the Nov 9, 2026 comparative
examination **measured** — a pre-registered protocol run (same-team
execution) against a frozen, competent conventional baseline, in which the
baseline beat the v0.2 fixture at strict strength (baseline 10 PASS / 2 FAIL,
fixture 8 PASS / 4 FAIL, with two further fixture scope absences at question
strength). The corrections' regression proof is the new adversarial test
**A3** beside the amended T6 and A1 controls, written from the comparison's
own failure demonstrations:

1. **Mediation at the store** (was: V4 prevention FAIL — a write that
   bypassed the gate landed in the effect store; only after-the-fact
   detection flagged it). The effect store is now a `MediatedStore` whose
   only write path demands a single-use dispatch capability minted inside
   `execute()` after all governance checks pass. The unwired route reaches
   the store and **the store itself refuses it** (`ungoverned_write`);
   state is unchanged and the attempt is recorded at the boundary. T6's
   negative control — which in v0.1/v0.2 passed by demonstrating the gap —
   now passes only if the bypass does not land. Scope on its face: this is
   API-level mediation inside a single-process fixture; it governs every
   write route the fixture exposes and claims nothing against in-process
   introspection of the fixture's own memory.
2. **Approver authorization** (was: V8 NOT_SUPPORTED at question strength,
   FAIL at strict — the fixture had no such concept, and an approval by
   the string `arbitrary-unauthorized-string` was accepted and executed).
   Principals are registered with roles; `approve()` admits only a
   registered, active approver presenting a valid proof, and `execute()`
   re-checks the approver's **current** authorization, so an approver
   withdrawn after approval blocks execution
   (`approver_no_longer_authorized`).
3. **Read authorization** (was: V12 NOT_SUPPORTED / FAIL — `query()` took
   no identity and returned a state digest to any caller). Objects carry
   classifications; a sensitive read requires a registered principal with
   the sensitive-reader role and a valid proof, and every sensitive read
   attempt, served or refused, is written to a read audit. Ordinary reads
   keep the v0.2 query-view semantics.
4. **Instance-secret signing** (was: V9 FAIL at strict strength only —
   forged-receipt rejection rested on ledger comparison because the
   fixture's only signing key was published, so a signature authenticated
   nothing). Approvals and receipts are now signed with a
   **per-engine-instance secret** drawn at construction and never
   published; `verify_receipt` checks the receipt signature after its
   field comparisons, so a field-perfect receipt re-signed with the
   published key is rejected on the signature. (The kit's own exam passes
   a fixed stand-in secret to its engines so the published `results.json`
   stays byte-deterministic — see `kit/fixtures.py`; construct an engine
   with no supplied secret, as the comparison harness does, and the
   secret is genuinely non-public.)
5. **Actor authentication** (was: the failed sub-leg inside V9's
   question-strength pass — a request under the bare actor string
   `compromised-anyone` executed, because the actor field was
   unauthenticated). `propose()` now requires a registered actor-role
   principal's valid proof over the exact request bytes.

One measured weakness is **re-scoped, not fixed**, and the reason is part
of this release: the second half of V9's leg B — a *genuinely
compromised but valid* credential, correctly presented, working inside
its policy — is still accepted. A settlement layer cannot distinguish
the legitimate holder of a valid credential from a thief holding the
same credential; distinguishing them is anomaly detection, an
identity-layer control, and neither the fixture nor the Nov 9 baseline
claims it. The protocol froze it as a limitation for both systems; v0.3
keeps it frozen, in the open.

v0.1 and v0.2 are preserved, frozen, exactly as published (v0.1 canonical
archive sha256
`cc93961bbf37f6eea3b462581302178213e2859299e8efd37be0f3593840d6de`,
results_digest
`sha256:e685155a7ad99257613fa7278f3b39664fcf361e54578d13774067fd42773b60`;
v0.2 results_digest
`sha256:f40f78fb4a382a3c24207ac835f3db750479c0b1609d55fc625d05f824b1`)
— v0.3 succeeds them; it does not rewrite them. A declared dependence
cycle remains unconstructible in all versions, because a `request_id` is
a content digest over `depends_on`; A2 states this as a structural
control rather than claiming cycle behavior in either direction.

## Run it

```sh
python3 run_exam.py
```

From the kit root. Python 3, standard library only. The runner verifies
the kit's own files against `MANIFEST.json`, verifies the frozen fixtures,
runs all six tests (each with a positive and a negative control) and the
three adversarial tests (A1, A2, A3), compares every outcome against
`EXPECTED.json`, writes a machine-readable `results.json`, and exits 0
only if every control matched its frozen expectation.

## What a pass establishes — and what it does not

The kit ships a small **fixture reference engine** (`kit/engine.py`): a
self-contained model of the record-layer semantics the ARC public
reference establishes — a Statement binds the exact request digest;
approval and release bind the same digest; receipts anchor to the
consequential request and its settlement, not to the query that later
retrieves the record.

A pass is at **local record-layer strength**. It establishes that the
claimed semantics are coherent, frozen, and reproducible — that the
answer to vina's question, *"request/update-bound, not query-bound,"*
holds inside an inspectable implementation an examiner controls. It
establishes **nothing** about any deployed system. Testing a production
stack is Issue #31's work, with this kit's cases as the common test
conditions.

v0.2 added two narrower claims at the same local strength (receipt-field
completeness, A1; ancestry-walking revocation enforcement, A2). v0.3
adds five more, each bounded on its face in the engine's strength
statement: store-level mediation of every write route the fixture
exposes; approver authorization with currency re-checked at execution;
read authorization with an audit for sensitive objects; receipt and
approval signatures under a non-public instance secret; and actor
authentication at proposal.

Claims **not** made anywhere in this kit, because the record does not
establish them:

1. That an ungated action is prevented in any *deployed* system. (T6
   establishes prevention inside this fixture's store, at API level,
   against the routes the fixture exposes. A real system's store must be
   examined on its own mediation, not credited with this fixture's.)
2. That dependents are traced universally. (T5 finds dependents through
   *declared* dependence only; its negative control demonstrates an
   undeclared dependence passing undetected.)
3. That every write executes exactly once in the outside world. (T4's
   exactly-once is a property of a fixture ledger over a local store.)
4. That a compromised-but-valid credential is detected. (v0.3
   authenticates credentials; it does not claim anomaly detection. The
   limitation is frozen, named, and shared by the Nov 9 baseline.)
5. That the published principal secrets are credentials. They are fixture
   material, printed in `kit/engine.py` so the registry, role, and proof
   mechanisms are inspectable end to end. The one secret that does
   authenticate in v0.3 — the engine's instance signing secret — is
   generated at construction and appears nowhere in this kit.

## Files

| File | What it is |
|---|---|
| `run_exam.py` | The single entry command |
| `kit/canon.py` | Canonical serialization + digests (deterministic) |
| `kit/engine.py` | The fixture reference engine (strength statement on its face; v0.3 carries the five corrections) |
| `kit/fixtures.py` | The frozen inputs (state S0 incl. the classified object, classifications, all requests) |
| `kit/tests.py` | The six tests, controls, claims, strength lines (T6's negative control rewritten in v0.3; T1–T5 unchanged in claim and codes) |
| `kit/adversarial_tests.py` | The adversarial tests: A1/A2 (v0.2) and A3, authorization completeness (v0.3) |
| `fixtures/fixture-manifest.json` | Digests pinning every frozen input |
| `EXPECTED.json` | The frozen expected outcome of every control (v0.3 changes are enumerated in its note) |
| `MANIFEST.json` | sha256 of every file in this kit (verified before every run) |
| `EXAM.md` | The six tests in prose, with scope and caveats, plus A1/A2/A3 |
| `SUBMITTING.md` | How to submit a failure (or a pass) for independent review |
| `LICENSE.md` | Terms |

## Deterministic

Fixed fixtures, logical sequencing, canonical JSON, no clocks, no
environment reads in any scored path. The one deliberate exception is
documented rather than hidden: an engine constructed without a supplied
secret draws one from `os.urandom`, so two *examination* engines hold
different secrets — as they must, for the secret to be non-public. The
kit's own exam removes that variable by supplying its fixed stand-in
secret, so two runs of `run_exam.py` — anywhere — produce byte-identical
`results.json` and the same `results_digest`. If yours differ, that is a
finding: see `SUBMITTING.md`.

## Submitting results

See `SUBMITTING.md`. Failures are first-class submissions: a reproduced
divergence between this kit's stated expectations and its behavior, or
between these cases and your own stack's behavior under Issue #31, is
exactly the contribution the examination exists to produce.
