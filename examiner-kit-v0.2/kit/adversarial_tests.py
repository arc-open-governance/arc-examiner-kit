"""Adversarial tests added in Examiner Kit v0.2.

Origin: an outside source-level audit of v0.1 (filed as an input, graded
INPUT) raised two candidate defects against the v0.1 fixture engine; a
governed reproduction on the issuing desk then CONFIRMED both at fixture
strength (examination record, 2026-11-01). v0.2 exists to correct exactly
those two defects, and this module is the correction's regression proof:
the negative controls below encode the reproduced v0.1 behaviors that
v0.2 must NOT reproduce, beside the controls that must keep holding (the
untouched receipt; transitive detection; the direct-edge refusal; the
unrelated action; the structural impossibility of a declared cycle).

A1 — receipt-field completeness. v0.1's verify_receipt compared the
request digest, the approval's signature, and one gated poststate match —
and nothing else in the receipt body. Altering the stated object, the
prestate digest, the sequence number, or the approval digest each left
the altered receipt verified. v0.2's verifier compares every receipt
field against the authoritative record; each single-field alteration
below must now be rejected.

A2 — multilevel revocation. v0.1 DETECTED revoked ancestry transitively
(dependents_of and derived_state_status) but ENFORCED revocation only at
the presented request's direct depends_on: after revoking A, new actions
depending on B or on C in the chain A <- B <- C were admitted. v0.2's
enforcement walks the declared ancestry; reliance through any declared
intermediate must now be refused with dependency_revoked, while
detection, the direct-edge refusal, and unrelated activity behave
exactly as in v0.1.

Strength: local record-layer, the same as the six original tests — see
STRENGTH_LOCAL in kit/tests.py. Nothing here establishes anything about
any deployed system.
"""

import copy
import json

from .canon import digest_of, request_id_for
from .engine import Engine, verify_receipt
from . import fixtures as F
from .tests import APPROVER, STRENGTH_LOCAL, _attempt, _control, _settle

ACTOR = F.ACTOR


def _req(obj, value, depends_on, idem):
    return {
        "actor": ACTOR,
        "action": "set",
        "object": obj,
        "value": value,
        "depends_on": list(depends_on),
        "idempotency_key": idem,
    }


def _set_field(field, value):
    def mutate(rec):
        rec[field] = value

    return mutate


def _set_effect_field(field, value):
    def mutate(rec):
        rec["effect"][field] = value

    return mutate


# ---------------------------------------------------------------- A1

def test_a1():
    eng = Engine(F.S0)
    rid, release = _settle(eng, F.REQ_T1)
    receipt = eng.execute(release["release_id"], F.REQ_T1)
    codes = {}

    def verdict(rec):
        ok, code = verify_receipt(eng, rec)
        return ok, code

    ok0, code0 = verdict(copy.deepcopy(receipt))
    codes["untouched"] = code0
    pos = _control(
        "untouched_receipt_verifies",
        "positive",
        "untouched_receipt_verified",
        "untouched_receipt_verified" if (ok0 and code0 == "verified") else f"unexpected:{ok0}:{code0}",
        "The receipt exactly as issued verifies against the authoritative record (the control proving the A1 setup itself is valid).",
        f"verify_receipt(untouched) = ({ok0}, {code0})",
    )

    def altered(name, mutate, expected_reject_code, field_desc):
        rec = copy.deepcopy(receipt)
        mutate(rec)
        ok, code = verdict(rec)
        codes[name] = code
        return _control(
            name,
            "negative",
            f"rejected_{expected_reject_code}",
            f"rejected_{code}" if not ok else "accepted_verified",
            f"A receipt altered in exactly one field — {field_desc} — is rejected by independent verification (verifier code: {expected_reject_code}). In v0.1 this alteration verified; the field is now compared against the authoritative record, not taken on trust.",
            f"verify_receipt(altered {field_desc}) = ({ok}, {code})",
        )

    neg_object = altered(
        "altered_stated_object_rejected",
        _set_effect_field("object", "obj-y"),
        "effect_object_mismatch",
        "the stated object (effect.object)",
    )
    neg_prestate = altered(
        "altered_prestate_digest_rejected",
        _set_effect_field("prestate_digest", digest_of({"value": "forged-prestate", "version": 999})),
        "prestate_digest_mismatch",
        "the prestate digest (effect.prestate_digest)",
    )
    neg_seq = altered(
        "altered_sequence_number_rejected",
        _set_field("seq", receipt["seq"] + 1000),
        "seq_mismatch",
        "the sequence number (seq)",
    )
    neg_approval = altered(
        "altered_approval_digest_rejected",
        _set_field("approval_digest", digest_of({"forged": "approval"})),
        "approval_digest_mismatch",
        "the approval digest (approval_digest)",
    )
    neg_poststate = altered(
        "altered_poststate_digest_rejected",
        _set_effect_field("poststate_digest", digest_of({"value": "forged-poststate", "version": 999})),
        "no_matching_gated_effect",
        "the poststate digest (effect.poststate_digest) — already bound in v0.1; it must stay rejected",
    )
    evidence = {"receipt": receipt, "alteration_verifier_codes": codes}
    return {
        "test_id": "A1",
        "title": "Receipt-field completeness (adversarial, v0.2)",
        "origin": "Outside-audit candidate, confirmed by governed reproduction at fixture strength (examination record, 2026-11-01); encoded here as the v0.2 correction's regression proof.",
        "strength": STRENGTH_LOCAL,
        "claim": "Independent receipt verification compares every field of a settlement receipt against the authoritative record — the stored request, the stored signed approval, and the gated store-history entry. A single-field alteration of the stated object, the prestate digest, the sequence number, or the approval digest is rejected; the poststate digest, already bound in v0.1, stays rejected.",
        "controls": [pos, neg_object, neg_prestate, neg_seq, neg_approval, neg_poststate],
        "evidence_digest": digest_of(evidence),
        "evidence": evidence,
    }


# ---------------------------------------------------------------- A2

def test_a2():
    eng = Engine(F.S0)
    A = _req("obj-y", {"value": "chain-base", "version": 1}, [], "adv-a2-a")
    A_ID = request_id_for(A)
    B = _req("obj-z", {"value": "chain-mid", "version": 1}, [A_ID], "adv-a2-b")
    B_ID = request_id_for(B)
    C = _req("obj-x", {"value": "chain-leaf", "version": 1}, [B_ID], "adv-a2-c")
    C_ID = request_id_for(C)
    for r in (A, B, C):
        rid_r, rel_r = _settle(eng, r)
        eng.execute(rel_r["release_id"], r)
    eng.revoke(A_ID)

    def reliance(engine, request):
        rid_r, rel_r = _settle(engine, request)
        status, val = _attempt(lambda: engine.execute(rel_r["release_id"], request))
        return status, (val if status == "refusal" else "admitted")

    dependents = eng.dependents_of(A_ID)
    status_b = eng.derived_state_status(B_ID)
    status_c = eng.derived_state_status(C_ID)
    detection_ok = (
        dependents == sorted([B_ID, C_ID])
        and status_b == "contested_revoked_ancestry"
        and status_c == "contested_revoked_ancestry"
    )
    pos_detection = _control(
        "transitive_detection_reports_revoked_ancestry",
        "positive",
        "detection_transitive_contested_ancestry",
        "detection_transitive_contested_ancestry" if detection_ok else "unexpected",
        "Detection is unchanged from v0.1: dependents_of(A) reports both B and C, and both derived statuses read contested_revoked_ancestry. The v0.1 defect was never detection — it was enforcement stopping at the direct edge.",
        f"dependents_of(A)={dependents}; status_B={status_b}; status_C={status_c}",
    )

    def reliance_control(name, dep_id, idem, label):
        request = _req("obj-x", {"value": "reliance", "version": 2}, [dep_id], idem)
        status, outcome = reliance(eng, request)
        refused = status == "refusal" and outcome == "dependency_revoked"
        return _control(
            name,
            "negative",
            "refused_dependency_revoked",
            "refused_dependency_revoked" if refused else f"unexpected:{status}:{outcome}",
            f"A new action declaring dependence on {label}, executed after A was revoked, is refused (dependency_revoked): enforcement walks the declared ancestry to the revoked request. In v0.1 this reliance was admitted whenever {label} was not itself the revoked request.",
            f"execute(reliance via {label}) = {status}:{outcome}",
        )

    neg_c = reliance_control("reliance_through_c_refused", C_ID, "adv-a2-dc", "C (two declared intermediates from A)")
    neg_b = reliance_control("reliance_through_b_refused", B_ID, "adv-a2-db", "B (one declared intermediate from A)")
    neg_a = reliance_control("direct_reliance_on_revoked_refused", A_ID, "adv-a2-da", "A itself (the direct edge — already refused in v0.1)")

    U = _req("obj-y", {"value": "unrelated", "version": 9}, [], "adv-a2-u")
    s_u, o_u = reliance(eng, U)
    pos_unrelated = _control(
        "unrelated_action_admitted",
        "positive",
        "unrelated_admitted",
        "unrelated_admitted" if s_u == "ok" else f"unexpected:{s_u}:{o_u}",
        "An authorized action declaring no dependence on the revoked chain still executes after the revocation; the ancestry walk refuses reliance on revoked authority, not unrelated work.",
        f"execute(unrelated) = {s_u}",
    )

    # Structural control: a declared cycle cannot be constructed. A
    # request_id is a content digest of the request including depends_on,
    # so a 2-cycle X<->Y would require X's id to be known before X's
    # content (which contains Y's id, which contains X's id) exists — a
    # hash fixed point. Assert the construction fails to close, exactly
    # as the examination record demonstrated; do not fake a cycle.
    placeholder = "req-0000000000000000"
    y_req = _req("obj-x", {"value": "cycle-y", "version": 1}, [placeholder], "adv-a2-cy")
    y_id = request_id_for(y_req)
    x_req = _req("obj-z", {"value": "cycle-x", "version": 1}, [y_id], "adv-a2-cx")
    x_id = request_id_for(x_req)
    cur = placeholder
    fixed_point = False
    for _ in range(3):
        nxt = request_id_for(_req("obj-x", {"value": "cycle-self", "version": 1}, [cur], "adv-a2-cs"))
        if nxt == cur:
            fixed_point = True
        cur = nxt
    cycle_ok = (x_id != placeholder) and not fixed_point
    pos_cycle = _control(
        "declared_cycle_unconstructible",
        "structural",
        "cycle_unconstructible_content_digest_ids",
        "cycle_unconstructible_content_digest_ids" if cycle_ok else "unexpected:cycle_constructed",
        "STRUCTURAL, on the record: a declared dependence cycle cannot be constructed with this kit's API, because a request_id is a content digest over depends_on — closing a cycle would require a hash fixed point. The pair built against a placeholder does not close (the computed id differs from the placeholder it would have to equal), and iterated self-dependence reaches no fixed point. There is therefore no cycle-revocation behavior to claim, in either direction.",
        f"placeholder={placeholder}; computed_counterpart_id={x_id}; self_dependence_fixed_point={fixed_point}",
    )

    # Restart control: the kit ships no persistence API, so state is
    # carried by the harness dump/load the examination record used (there,
    # across two processes; here, the same dump/load carriage through a
    # JSON round-trip into a fresh Engine). Post-carriage behavior must
    # be identical: detection still transitive, reliance through C and
    # direct reliance on A both refused.
    eng2 = Engine(F.S0)
    for r in (A, B, C):
        rid_r, rel_r = _settle(eng2, r)
        eng2.execute(rel_r["release_id"], r)
    eng2.revoke(A_ID)
    dump = {
        "initial_state": eng2.initial_state,
        "state": eng2.state,
        "store_history": eng2.store_history,
        "requests": eng2.requests,
        "approvals": eng2.approvals,
        "releases": eng2.releases,
        "receipts": eng2.receipts,
        "revoked": sorted(eng2.revoked),
    }
    carried = json.loads(json.dumps(dump))
    eng3 = Engine(carried["initial_state"])
    eng3.state = carried["state"]
    eng3.store_history = carried["store_history"]
    eng3.requests = carried["requests"]
    eng3.approvals = carried["approvals"]
    eng3.releases = carried["releases"]
    eng3.receipts = carried["receipts"]
    eng3.revoked = set(carried["revoked"])
    s_rc, o_rc = reliance(eng3, _req("obj-x", {"value": "through-c", "version": 2}, [C_ID], "adv-a2-rdc"))
    s_ra, o_ra = reliance(eng3, _req("obj-y", {"value": "through-a", "version": 2}, [A_ID], "adv-a2-rda"))
    restart_ok = (
        s_rc == "refusal" and o_rc == "dependency_revoked"
        and s_ra == "refusal" and o_ra == "dependency_revoked"
        and eng3.derived_state_status(C_ID) == "contested_revoked_ancestry"
    )
    pos_restart = _control(
        "restart_carriage_preserves_enforcement",
        "positive",
        "post_restart_reliance_refused_identical",
        "post_restart_reliance_refused_identical" if restart_ok else f"unexpected:through_C={s_rc}:{o_rc};direct_A={s_ra}:{o_ra}",
        "After the engine's public state is carried through the harness dump/load into a fresh Engine (the restart carriage of the examination record), enforcement is identical: reliance through C and direct reliance on A are both refused, and C's derived status still reads contested_revoked_ancestry. In v0.1 the through-C reliance was admitted after the same carriage.",
        f"post-carriage: through_C={s_rc}:{o_rc}; direct_A={s_ra}:{o_ra}; status_C={eng3.derived_state_status(C_ID)}",
    )

    evidence = {
        "chain": {"A": A_ID, "B": B_ID, "C": C_ID},
        "dependents_of_revoked": dependents,
        "derived_statuses": {"B": status_b, "C": status_c},
        "post_carriage_status_c": eng3.derived_state_status(C_ID),
    }
    return {
        "test_id": "A2",
        "title": "Multilevel revocation (adversarial, v0.2)",
        "origin": "Outside-audit candidate, confirmed by governed reproduction at fixture strength (examination record, 2026-11-01); encoded here as the v0.2 correction's regression proof.",
        "strength": STRENGTH_LOCAL,
        "claim": "Revocation enforcement walks the declared ancestry: after an upstream request is revoked, new reliance on it through any declared intermediate is refused with dependency_revoked — enforcement now matches the transitive detection the engine already reported. Unrelated authorized activity is unaffected, and the structural impossibility of a declared cycle is stated, not papered over.",
        "controls": [pos_detection, neg_c, neg_b, neg_a, pos_unrelated, pos_cycle, pos_restart],
        "evidence_digest": digest_of(evidence),
        "evidence": evidence,
    }


ALL_ADVERSARIAL = [test_a1, test_a2]
