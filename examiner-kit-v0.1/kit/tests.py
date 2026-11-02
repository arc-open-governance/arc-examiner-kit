"""The six tests of GitHub Issue #35, as executable fixture examinations.

Each test runs against a fresh fixture Engine (kit/engine.py) built from the
frozen S0 (kit/fixtures.py). Each test carries:
  - a positive control: the flow behaving as the claim requires;
  - a negative control: the adversarial or tampered variant, whose expected
    outcome is a refusal, a failed verification, or an honestly-scoped limit;
  - a strength line, printed on the face of the results, stating exactly what
    a pass does and does not establish.

Control outcomes are short machine-readable codes; EXPECTED.json freezes the
expected code for every control, and the runner fails the kit if observed and
expected diverge — in either direction.

Outcome vocabulary follows Issue #35: a claim that cannot be expressed or
does not hold is reported FAILED / UNKNOWN / NOT EXPRESSIBLE, never rounded
up to a pass.
"""

import copy

from .canon import digest_of
from .engine import AckLost, Engine, Refusal, verify_receipt
from . import fixtures as F

APPROVER = F.APPROVER
STRENGTH_LOCAL = (
    "Local record-layer strength: a self-contained fixture engine in this kit "
    "implements the claimed semantics. A pass establishes that the semantics "
    "are coherent and reproducible against frozen inputs. It establishes "
    "nothing about any deployed system; run the same cases against a real "
    "stack under Issue #31 to test production behavior."
)


def _control(name, kind, expected_code, observed_code, expected_text, observed_text, extra=None):
    c = {
        "name": name,
        "kind": kind,
        "expected_code": expected_code,
        "observed_code": observed_code,
        "pass": expected_code == observed_code,
        "expected": expected_text,
        "observed": observed_text,
    }
    if extra:
        c.update(extra)
    return c


def _settle(engine, request):
    """propose -> approve -> release; returns (request_id, release)."""
    rid = engine.propose(request)["request_id"]
    engine.approve(rid, APPROVER)
    release = engine.issue_release(rid)
    return rid, release


def _attempt(fn):
    """Run fn; return ('ok', value) or ('refusal', code)."""
    try:
        return "ok", fn()
    except Refusal as r:
        return "refusal", r.code


# ---------------------------------------------------------------- T1

def test_t1():
    eng = Engine(F.S0)
    rid, release = _settle(eng, F.REQ_T1)
    status, receipt = _attempt(lambda: eng.execute(release["release_id"], F.REQ_T1))
    q = eng.query("obj-x")
    ok = (
        status == "ok"
        and receipt["kind"] == "settlement_receipt"
        and receipt["request_digest"] == digest_of(F.REQ_T1)
        and eng.state["obj-x"] == {"value": "beta", "version": 1}
        and len(eng.receipts) == 1
        and q["kind"] == "query_view"
    )
    pos = _control(
        "authorized_update_commits_with_request_bound_receipt",
        "positive",
        "committed_with_bound_receipt",
        "committed_with_bound_receipt" if ok else f"unexpected:{status}",
        "Exact authorized request executes once; the settlement receipt binds the request digest; a later query returns the new state and creates no receipt.",
        f"execute={status}; receipt_kind={receipt.get('kind') if status=='ok' else 'n/a'}; state={eng.state['obj-x']}; receipts={len(eng.receipts)}; query_kind={q['kind']}",
    )
    eng2 = Engine(F.S0)
    rid2 = eng2.propose(F.REQ_T1)["request_id"]
    eng2.approve(rid2, APPROVER)  # approval exists, but NO release is issued
    status2, code2 = _attempt(lambda: eng2.execute("rel-does-not-exist", F.REQ_T1))
    ok2 = status2 == "refusal" and code2 == "no_valid_release" and eng2.state == F.S0 and not eng2.receipts
    neg = _control(
        "execution_without_release_refused",
        "negative",
        "refused_no_valid_release",
        "refused_no_valid_release" if ok2 else f"unexpected:{status2}:{code2}",
        "Execution presented without a release is refused; state is unchanged; no receipt exists.",
        f"execute={status2}:{code2}; state_unchanged={eng2.state == F.S0}; receipts={len(eng2.receipts)}",
    )
    evidence = {"receipt": receipt if status == "ok" else None, "query_view": q}
    return {
        "test_id": "T1",
        "title": "Authorized update",
        "issue35_case": 1,
        "strength": STRENGTH_LOCAL,
        "claim": "A receipt is anchored to the consequential request and its settlement, not to the query that later retrieves the record.",
        "controls": [pos, neg],
        "evidence_digest": digest_of(evidence),
        "evidence": evidence,
    }


# ---------------------------------------------------------------- T2

def test_t2():
    eng = Engine(F.S0)
    rid, release = _settle(eng, F.REQ_T2)
    status, receipt = _attempt(lambda: eng.execute(release["release_id"], F.REQ_T2))
    ok = status == "ok" and eng.state["obj-x"] == {"value": "beta", "version": 1}
    pos = _control(
        "exact_request_executes",
        "positive",
        "committed_exact_request",
        "committed_exact_request" if ok else f"unexpected:{status}",
        "The exact approved-and-released request executes (control proving the T2 setup itself is valid).",
        f"execute={status}; state_x={eng.state['obj-x']}",
    )
    eng2 = Engine(F.S0)
    rid2, release2 = _settle(eng2, F.REQ_T2)
    status2, code2 = _attempt(lambda: eng2.execute(release2["release_id"], F.REQ_T2_MUTATED))
    ok2 = (
        status2 == "refusal"
        and code2 == "request_binding_mismatch"
        and eng2.state == F.S0
        and not eng2.receipts
    )
    neg = _control(
        "mutated_request_refused_no_effect",
        "negative",
        "refused_request_binding_mismatch",
        "refused_request_binding_mismatch" if ok2 else f"unexpected:{status2}:{code2}",
        "Same approval and release, but the presented request's target is changed X->Y: refusal (request_binding_mismatch), no effect on Y, no receipt.",
        f"execute={status2}:{code2}; state_unchanged={eng2.state == F.S0}; receipts={len(eng2.receipts)}",
    )
    evidence = {
        "approved_request_digest": digest_of(F.REQ_T2),
        "mutated_request_digest": digest_of(F.REQ_T2_MUTATED),
        "refusal_code": code2 if status2 == "refusal" else None,
    }
    return {
        "test_id": "T2",
        "title": "Altered request",
        "issue35_case": 2,
        "strength": STRENGTH_LOCAL,
        "claim": "Approval and release bind the exact request digest; altering the request after approval voids the authorization for the altered bytes.",
        "controls": [pos, neg],
        "evidence_digest": digest_of(evidence),
        "evidence": evidence,
    }


# ---------------------------------------------------------------- T3

def test_t3():
    eng = Engine(F.S0)
    q1 = eng.query("obj-x")
    q2 = eng.query("obj-x")
    receipts_before = len(eng.receipts)
    rid, release = _settle(eng, F.REQ_T3)
    receipt = eng.execute(release["release_id"], F.REQ_T3)
    distinct = (
        receipt["request_digest"] not in (q1["state_digest"], q2["state_digest"])
        and receipt["kind"] == "settlement_receipt"
        and q1["kind"] == q2["kind"] == "query_view"
        and receipts_before == 0
    )
    pos = _control(
        "queries_create_no_receipt_mutation_receipt_is_distinct",
        "positive",
        "query_views_only_mutation_receipt_distinct",
        "query_views_only_mutation_receipt_distinct" if distinct else "unexpected",
        "Two queries matching current state create query views and no receipts; the one authorized mutation produces a settlement receipt whose request digest differs from every query-view digest.",
        f"receipts_before_mutation={receipts_before}; query_kinds={q1['kind']},{q2['kind']}; receipt_kind={receipt['kind']}",
    )
    forged = dict(q1)
    forged["kind"] = "settlement_receipt"  # relabel a query view as a receipt
    ok_verify, vcode = verify_receipt(eng, forged)
    neg = _control(
        "relabeled_query_view_fails_receipt_verification",
        "negative",
        "verification_failed_no_request_binding",
        "verification_failed_no_request_binding" if (not ok_verify and vcode == "unknown_request") else f"unexpected:{ok_verify}:{vcode}",
        "A query view relabeled as a settlement receipt fails independent verification: the view carries no request binding at all (verifier code: unknown_request), so a query/view digest cannot be substituted for the mutation's authoritative transition receipt.",
        f"verify_receipt(forged) = ({ok_verify}, {vcode})",
    )
    evidence = {"query_views": [q1, q2], "receipt": receipt, "forged_verify_code": vcode}
    return {
        "test_id": "T3",
        "title": "Query-vs-update evidence",
        "issue35_case": 3,
        "strength": STRENGTH_LOCAL,
        "claim": "Query evidence and update evidence are different record kinds with different bindings; neither substitutes for the other. Scope note: that ordinary queries are unreceipted is this fixture's design convention for reads, not a universal security law — a disclosure-sensitive read can itself be consequential under a real policy.",
        "controls": [pos, neg],
        "evidence_digest": digest_of(evidence),
        "evidence": evidence,
    }


# ---------------------------------------------------------------- T4

def test_t4():
    eng = Engine(F.S0)
    rid, release = _settle(eng, F.REQ_T4)
    caller_status = "response_received"
    try:
        eng.execute(release["release_id"], F.REQ_T4, drop_ack=True)
        caller_status = "response_received"
    except AckLost:
        caller_status = "unknown_effect"  # the caller saw no response at all
    history_before_retry = len(eng.store_history)
    rec = eng.retry(rid)
    single = (
        caller_status == "unknown_effect"
        and rec["status"] == "already_committed"
        and len(eng.store_history) == history_before_retry == 1
        and eng.state["obj-x"] == {"value": "delta", "version": 3}
    )
    pos = _control(
        "lost_ack_reconciles_by_readback_effect_applied_once",
        "positive",
        "unknown_effect_reconciled_single_application",
        "unknown_effect_reconciled_single_application" if single else "unexpected",
        "Effect commits; acknowledgment is lost, so the caller's status is UNKNOWN_EFFECT; readback reconciliation returns the standing receipt and the effect stands applied exactly once in this fixture's store.",
        f"caller_status_after_loss={caller_status}; retry={rec['status']}; store_mutations={len(eng.store_history)}",
    )
    rid2, release2 = _settle(eng, F.REQ_T4_CONFLICT)
    status2, code2 = _attempt(lambda: eng.execute(release2["release_id"], F.REQ_T4_CONFLICT))
    ok2 = status2 == "refusal" and code2 == "idempotency_conflict" and len(eng.store_history) == 1
    neg = _control(
        "second_mutation_under_same_idempotency_key_refused",
        "negative",
        "refused_idempotency_conflict",
        "refused_idempotency_conflict" if ok2 else f"unexpected:{status2}:{code2}",
        "A second, different mutation presented under the same idempotency key — the 'no response was seen, so send another' move — is refused; no second effect is authorized on the basis of a lost response.",
        f"execute={status2}:{code2}; store_mutations={len(eng.store_history)}",
    )
    evidence = {"receipt": rec.get("receipt"), "caller_status_after_loss": caller_status}
    return {
        "test_id": "T4",
        "title": "Lost acknowledgment",
        "issue35_case": 4,
        "strength": STRENGTH_LOCAL + " Exactly-once here is a property of this fixture's idempotency ledger over a local store; it is NOT evidence of exactly-once effects in any outside world.",
        "claim": "A lost acknowledgment leaves the effect UNKNOWN_EFFECT until independent readback; reconciliation resolves it from the record and never authorizes a second mutation on the strength of the lost response.",
        "controls": [pos, neg],
        "evidence_digest": digest_of(evidence),
        "evidence": evidence,
    }


# ---------------------------------------------------------------- T5

def test_t5():
    eng = Engine(F.S0)
    rid_a, rel_a = _settle(eng, F.REQ_T5_A)
    eng.execute(rel_a["release_id"], F.REQ_T5_A)
    rid_d, rel_d = _settle(eng, F.REQ_T5_D)
    eng.execute(rel_d["release_id"], F.REQ_T5_D)
    history_len_before_revoke = len(eng.store_history)
    eng.revoke(rid_a)
    history_preserved = len(eng.store_history) == history_len_before_revoke and rid_a in eng.receipts
    dependents = eng.dependents_of(rid_a)
    status_d = eng.derived_state_status(rid_d)
    rid_d2, rel_d2 = _settle(eng, F.REQ_T5_D2)
    s_d2, c_d2 = _attempt(lambda: eng.execute(rel_d2["release_id"], F.REQ_T5_D2))
    rid_u, rel_u = _settle(eng, F.REQ_T5_U)
    s_u, _ = _attempt(lambda: eng.execute(rel_u["release_id"], F.REQ_T5_U))
    ok = (
        history_preserved
        and dependents == [rid_d]
        and status_d == "contested_revoked_ancestry"
        and s_d2 == "refusal"
        and c_d2 == "dependency_revoked"
        and s_u == "ok"
    )
    pos = _control(
        "revocation_flags_declared_dependents_blocks_new_reliance_allows_unrelated",
        "positive",
        "declared_dependents_detected_new_reliance_refused_unrelated_allowed",
        "declared_dependents_detected_new_reliance_refused_unrelated_allowed" if ok else "unexpected",
        "Revoking upstream A (history and A's receipt preserved, nothing erased) flags declared dependent D as contested, refuses new reliance on A (dependency_revoked), and still permits unrelated authorized activity.",
        f"history_preserved={history_preserved}; dependents_of_A={dependents}; D_status={status_d}; D2={s_d2}:{c_d2}; unrelated={s_u}",
    )
    # Negative control: an UNDECLARED dependence. SNEAK's payload copies A's
    # output value but declares depends_on=[]. The expected, honest outcome
    # is that the engine does not detect it — the declared-dependence limit.
    rid_s, rel_s = _settle(eng, F.REQ_T5_SNEAK)
    s_s, _ = _attempt(lambda: eng.execute(rel_s["release_id"], F.REQ_T5_SNEAK))
    not_detected = s_s == "ok" and eng.derived_state_status(rid_s) == "settled"
    neg = _control(
        "undeclared_dependence_limit_demonstrated",
        "negative",
        "undeclared_dependence_not_detected_limit",
        "undeclared_dependence_not_detected_limit" if not_detected else f"unexpected:{s_s}",
        "LIMIT, on the record: a write whose payload copies the revoked upstream's output but declares no dependence executes undetected. Dependents are found through declared dependence (or independent discoverability in a real system), never by universal tracing. This control passes by demonstrating the limit, not by denying it.",
        f"sneak_execute={s_s}; sneak_status={eng.derived_state_status(rid_s)}",
        {"limit_demonstrated": True},
    )
    evidence = {
        "revoked_request": rid_a,
        "dependents_of_revoked": dependents,
        "derived_status_after_revocation": status_d,
        "d2_refusal": c_d2 if s_d2 == "refusal" else None,
    }
    return {
        "test_id": "T5",
        "title": "Derived-state revocation",
        "issue35_case": 5,
        "strength": STRENGTH_LOCAL,
        "claim": "Revoking an upstream authority contests derived state built on it through DECLARED dependencies, prevents new reliance on the revoked request, and leaves history and unrelated activity intact.",
        "controls": [pos, neg],
        "evidence_digest": digest_of(evidence),
        "evidence": evidence,
    }


# ---------------------------------------------------------------- T6

def test_t6():
    eng = Engine(F.S0)
    rid, release = _settle(eng, F.REQ_T6)
    eng.execute(release["release_id"], F.REQ_T6)
    scan_clean = eng.observer_scan()
    pos = _control(
        "gated_write_receipted_observer_clean",
        "positive",
        "gated_write_receipted_observer_clean",
        "gated_write_receipted_observer_clean" if scan_clean == [] else "unexpected",
        "A write through the gate produces a receipt, and the observer comparison (store history vs receipt ledger) reports no unreceipted mutations.",
        f"observer_flags={scan_clean}",
    )
    eng.direct_write("obj-x", copy.deepcopy(F.BYPASS_VALUE))
    scan_after = eng.observer_scan()
    landed = eng.state["obj-x"] == F.BYPASS_VALUE
    flagged = len(scan_after) == 1 and scan_after[0]["via"] == "direct"
    neg = _control(
        "bypass_lands_and_observer_flags_the_gap",
        "negative",
        "bypass_landed_observer_flagged_gap",
        "bypass_landed_observer_flagged_gap" if (landed and flagged) else "unexpected",
        "COVERAGE GAP, demonstrated honestly: a write through a route not wired to the gate LANDS (the gate cannot refuse what it never sees). No automatic detection is claimed: the gap is visible only because the shipped observer comparison is run, and it flags exactly the bypass mutation as unreceipted.",
        f"bypass_landed={landed}; observer_flags={scan_after}; receipts={len(eng.receipts)}",
        {"coverage_gap_demonstrated": True},
    )
    evidence = {"observer_flags_after_bypass": scan_after, "gated_receipt_request": rid}
    return {
        "test_id": "T6",
        "title": "Ungated bypass (negative control)",
        "issue35_case": 6,
        "strength": STRENGTH_LOCAL + " This test measures coverage; it does not assert prevention, and it does not establish that every ungated action in any real system is detected.",
        "claim": "The gate governs the routes wired through it. A bypass route's write is a coverage gap, visible to an explicit observer comparison of effects against receipts — not something the gate prevents or automatically detects.",
        "controls": [pos, neg],
        "evidence_digest": digest_of(evidence),
        "evidence": evidence,
    }


ALL_TESTS = [test_t1, test_t2, test_t3, test_t4, test_t5, test_t6]
