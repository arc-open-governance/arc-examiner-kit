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
fixture for reads of standard-classification objects, not a universal
security law — a disclosure-sensitive query may itself carry a
consequential policy and an evidence requirement. In v0.3 it does: see A3.

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
gate**. In v0.1 and v0.2 it landed: the gate never saw it, and the test
reported a coverage gap, visible only to the shipped observer comparison.
**In v0.3 the write is refused by the effect store itself.** The store's
only write path is a commit under a single-use dispatch capability minted
by the governed path after its checks pass; the unwired route presents no
capability, the store refuses it (`ungoverned_write`), state still holds
the gated value, and the refused attempt stands in the store's boundary
log while the observer comparison stays clean — there is no ungoverned
mutation to flag.
*Scope:* mediation at the boundary of a single-process fixture store, at
API level, over every write route the fixture exposes. It establishes
that the fixture's architecture leaves no unwired write path; it does not
establish that any real system's store is mediated, which is a property
to examine in that system.

## A1 — Receipt-field completeness (adversarial, added in v0.2; signature leg added in v0.3)

An outside audit of v0.1 asked whether `verify_receipt` actually compares
the whole receipt. At fixture strength it did not: it bound the request
digest, the approval's signature, and one gated poststate match — and a
receipt altered in its stated object, its prestate digest, its sequence
number, or its approval digest still verified. v0.2's verifier compares
every field against the authoritative record — the stored request, the
stored signed approval, and the gated store-history entry — and each
single-field alteration is rejected. The poststate digest was already
bound in v0.1 and stays rejected; the untouched receipt verifies in all
versions.
v0.3 adds the signature leg. In v0.1/v0.2 the fixture's only signing key
was published, so a signature authenticated nothing and rejection rested
on field comparison alone — the Nov 9, 2026 comparison graded exactly
that as a strict-strength failure. v0.3 signs receipts under a
per-instance secret the kit never publishes, and a field-perfect receipt
re-signed under the published key is rejected on its signature
(`receipt_signature_invalid`).
*Scope:* properties of the fixture verifier over the fixture's own
records. They state nothing about any deployed verifier.

## A2 — Multilevel revocation (adversarial, added in v0.2)

T5 revokes A and refuses new reliance declared directly on A. The audit
asked about reliance declared on A's dependents. In v0.1, with the chain
A <- B <- C all executed and A then revoked, the engine reported B and C
as `contested_revoked_ancestry` — and admitted new actions depending on
B and on C anyway: detection ran transitive, enforcement ran one level
deep. v0.2's enforcement walks the declared ancestry, and reliance
through B or through C is refused (`dependency_revoked`), while
unrelated activity proceeds and history is preserved — including across
the dump/load carriage that stands in for a restart (the kit ships no
persistence API; v0.3 formalizes the carriage as the engine's
export/import of its full state).
*Structural note:* a declared cycle cannot be constructed in any version
— a `request_id` is a content digest over `depends_on`, so a cycle would
require a hash fixed point. A2 records this as a structural control and
claims no cycle behavior in either direction.
*Limit, unchanged:* undeclared dependence is still not traced (T5's
negative control), and detection remains exactly the declared graph.

## A3 — Authorization completeness (adversarial, added in v0.3)

The Nov 9, 2026 comparative examination ran the v0.2 fixture against a
frozen conventional baseline and found the fixture missing the whole
authorization axis. A3 encodes those measured behaviors as the v0.3
correction's regression proof:

- An approval under the string `arbitrary-unauthorized-string` — accepted
  and executed in v0.2 — is refused at `approve()`
  (`approver_not_authorized`): approvals come only from registered,
  active approver-role principals presenting valid proofs.
- An approver whose authorization is withdrawn after approving blocks
  execution (`approver_no_longer_authorized`): `execute()` re-checks the
  approver's current authorization, the stale-reviewer case the baseline
  already handled and the fixture could not express.
- A proposal under a bare, unregistered actor string — executed in v0.2 —
  is refused at `propose()` (`actor_not_authenticated`): the actor's
  proof over the exact request bytes is authenticated.
- A read of the classified object by a principal without the
  sensitive-reader role, or with no identity at all, is refused
  (`read_not_authorized`) and the refusal is audited; the authorized
  reader's read is served and audited beside it. In v0.2 `query()` took
  no identity and served any caller.
*Limit, stated not buried:* a valid credential correctly presented by
the wrong party — genuine compromise, work inside policy — is still
accepted, in this fixture and in the Nov 9 baseline alike. A3 claims
authentication and authorization enforcement, never anomaly detection.

## What would change the grade

These six cases at local record-layer strength are the floor, not the
ceiling. The grade rises only when a separately controlled examiner
reproduces the cases — against this kit, and under Issue #31 against a real
integrated stack — and publishes the reproduction with its digests. See
`SUBMITTING.md`.

## A4 — Actor currency at execution (adversarial, added in v0.3.1)

**Origin.** An outside examination of v0.3 by codexmainbizmac
(2026-11-10, network-denied sandbox, public API only) found that an actor
withdrawn after `propose()` and before `execute()` still had its approved,
released request commit. v0.3 re-checked the approver's current
authorization at execution but authenticated the actor at proposal only.
The publisher reproduced it.

**Claim.** `execute()` re-checks the request actor's current authorization
as it re-checks the approver's.

**Controls.** (1) negative: actor withdrawn after proposal, approval and
release, before execution: refused `actor_no_longer_authorized`, state
unchanged, no receipt. (2) positive: the same shape with the actor current
commits and is receipted. (3) positive: actor withdrawn after the effect:
the effect stands and the receipt still verifies.

**Strength.** Local record-layer, the same as every other test here. It
says nothing about a genuinely compromised but valid credential, which
remains the standing limitation stated in the engine's strength statement.
