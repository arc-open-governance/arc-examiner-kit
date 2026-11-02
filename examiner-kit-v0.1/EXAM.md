# The examination — Issue #35's six tests, in prose

Origin: an outside examiner, **vina**, asked whether an ARC receipt is keyed
to the update or only to the query. Issue #35 turned that question into six
machine-checkable cases. This kit is those six cases, frozen and runnable.
The narrowest reproducible answer the cases support:

> **A receipt is anchored to the consequential request and its settlement,
> not to the query that later retrieves the record. The observed external
> effect is a separate claim that must be established by evidence.**

Every test below names its scope. Outcomes are reported as observed —
FAILED, UNKNOWN, or NOT EXPRESSIBLE are honest results, never rounded up.

## T1 — Authorized update
Frozen state S0; an exact signed request for a synthetic mutation; valid
authority and a current release; one committed effect. The settlement
receipt binds the request digest. An observer verifies before/after state.
A read-only query afterward returns the new state and creates **no**
settlement receipt.
*Negative control:* execution presented without a release is refused; state
unchanged.

## T2 — Altered request
The same approval and release as T1's shape, but the presented request's
target is changed (X→Y) after approval. Expected: refusal
(`request_binding_mismatch`), no effect on Y, decision/receipt evidence
showing the authentic reason.
*Positive control:* the exact, unaltered request executes — proving the
setup was valid and the refusal is caused by the alteration.

## T3 — Query-vs-update evidence
Two queries whose results match current state, and one distinct authorized
mutation. The queries produce query views and no receipts; the mutation's
receipt binds a request digest that no query view can substitute for.
*Negative control:* a query view relabeled as a settlement receipt fails
independent receipt verification.
*Scope:* unreceipted ordinary queries are a design convention of this
fixture for reads, not a universal security law — a disclosure-sensitive
query may itself carry a consequential policy and an evidence requirement.

## T4 — Lost acknowledgment
The synthetic effect commits; the caller's response is lost. The caller's
honest status is `UNKNOWN_EFFECT` until independent readback reconciles it
against the standing receipt. No second mutation is authorized on the basis
of the lost response.
*Negative control:* a different mutation reusing the same idempotency key is
refused (`idempotency_conflict`).
*Scope:* exactly-once inside this fixture is a property of its idempotency
ledger over a local store. It is not evidence of exactly-once effects in any
outside world.

## T5 — Derived-state revocation
A derived assertion D names its exact upstream update A. A's authority is
then revoked — **without erasing history**. A cold check over the declared
dependence graph detects D, flags it `contested_revoked_ancestry`, and
prevents **new reliance** on A while permitting unrelated authorized
activity.
*Negative control (a demonstrated limit):* a write whose payload copies A's
output but declares no dependence on A is **not detected**. Dependents are
found through declared dependence, or through independent discoverability
inside a system actually examined — never by universal tracing. This kit
does not state complete reverse traversal, because it does not demonstrate
it.

## T6 — Ungated bypass (negative control for the whole exam)
A synthetic write is attempted through an allowed route **not wired to the
gate**. It lands. That is a coverage gap, and this test reports it as one:
the gate governs the routes wired through it, and no automatic detection is
claimed. The kit ships an explicit observer comparison (effect-store history
vs the receipt ledger); running it flags exactly the bypass mutation as
unreceipted. Detection is exactly as strong as that comparison — in a real
system, exactly as strong as whatever observer coverage is independently
proven there.

## What would change the grade

These six cases at local record-layer strength are the floor, not the
ceiling. The grade rises only when a separately controlled examiner
reproduces the cases — against this kit, and under Issue #31 against a real
integrated stack — and publishes the reproduction with its digests. See
`SUBMITTING.md`.
