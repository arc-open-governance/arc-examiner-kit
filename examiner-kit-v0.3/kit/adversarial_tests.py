"""Adversarial tests added in Examiner Kit v0.2, plus A3 added in v0.3.

Origin (A1, A2): an outside source-level audit of v0.1 (filed as an input,
graded INPUT) raised two candidate defects against the v0.1 fixture engine;
a governed reproduction on the issuing desk then CONFIRMED both at fixture
strength (examination record, 2026-11-01). v0.2 exists to correct exactly
those two defects, and A1/A2 are the corrections' regression proof: the
negative controls encode the reproduced v0.1 behaviors that the corrected
engine must NOT reproduce.

A1 — receipt-field completeness. v0.1's verify_receipt compared the
request digest, the approval's signature, and one gated poststate match —
and nothing else in the receipt body. Altering the stated object, the
prestate digest, the sequence number, or the approval digest each left
the altered receipt verified. v0.2's verifier compares every receipt
field against the authoritative record; each single-field alteration
below must now be rejected. v0.3 adds one more A1 control: the untouched
receipt's fields left exactly as issued but its signature recomputed
under the PUBLISHED fixture key — in v0.1/v0.2 that signature was the
only one there was, and it authenticated nothing because the key is
public; in v0.3 the receipt is signed under the engine's instance
secret, so the re-signed receipt is rejected on its signature.

A2 — multilevel revocation. v0.1 DETECTED revoked ancestry transitively
(dependents_of and derived_state_status) but ENFORCED revocation only at
the presented request's direct depends_on: after revoking A, new actions
depending on B or on C in the chain A <- B <- C were admitted. v0.2's
enforcement walks the declared ancestry; reliance through any declared
intermediate must now be refused with dependency_revoked, while
detection, the direct-edge refusal, and unrelated activity behave
exactly as in v0.1. Unchanged in v0.3 (its restart control now rides the
engine's export_state/from_state carriage, which carries the store, the
registry, and the instance secret as engine state).

Origin (A3): the Nov 9, 2026 comparative examination ran the v0.2 fixture
against a frozen conventional baseline under a pre-registered protocol
(same-team execution) and measured the fixture weaker on exactly the
authorization axis: no approver authorization (an approval by the string
"arbitrary-unauthorized-string" executed), no read authorization (any
caller could read anything), no actor authentication (a bare actor
string executed), and receipt authentication resting on a published key.
A3 — authorization completeness — is those findings' regression proof,
written for v0.3 the way A1/A2 were written for v0.2: each control below
encodes a behavior the Nov 9 run observed in v0.2 that v0.3 must NOT
reproduce, beside the positive control that must now hold (the authorized
sensitive read). The compromised-but-valid-credential case is NOT among
the controls: it is a standing, explicitly re-scoped limitation (a
settlement layer cannot distinguish a valid credential's holder from a
thief holding the same credential), recorded in the engine's strength
statement — not a defect this test claims to close.

Strength: local record-layer, the same as the six original tests — see
STRENGTH_LOCAL in kit/tests.py. Nothing here establishes anything about
any deployed system.
"""

import copy
import json

from .canon import digest_of, request_id_for
from .engine import Engine, _sign, proof_for, verify_receipt
from . import fixtures as F
from .tests import APPROVER, STRENGTH_LOCAL, _attempt, _control, _settle, new_engine

ACTOR = F.ACTOR
READER = F.READER


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
    eng = new_engine()
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

    # v0.3 addition: the field-perfect receipt, re-signed under the
    # PUBLISHED fixture key. Every field matches the authoritative record;
    # only the signature is the attacker's. In v0.1/v0.2 the published key
    # was the only signing material in the system, so a signature proved
    # nothing and rejection had to rest on field comparison alone. In
    # v0.3 the receipt is signed under the engine's instance secret, and
    # this receipt must be rejected ON THE SIGNATURE.
    rec_resigned = copy.deepcopy(receipt)
    rec_resigned["signature"] = _sign(
        {k: v for k, v in rec_resigned.items() if k != "signature"}
    )
    ok_r, code_r = verdict(rec_resigned)
    codes["resigned_with_published_key"] = code_r
    neg_resign = _control(
        "resigned_with_published_key_rejected",
        "negative",
        "rejected_receipt_signature_invalid",
        f"rejected_{code_r}" if not ok_r else "accepted_verified",
        "A receipt whose every field matches the authoritative record but whose signature was recomputed under the PUBLISHED fixture key is rejected on the signature (receipt_signature_invalid): v0.3 receipts are signed under the engine's per-instance secret, so forgery rejection is a signature property, not only a ledger property. In v0.1/v0.2 the published key was the system's only signing material and a signature authenticated nothing.",
        f"verify_receipt(re-signed with published key) = ({ok_r}, {code_r})",
    )
    evidence = {"receipt": receipt, "alteration_verifier_codes": codes}
    return {
        "test_id": "A1",
        "title": "Receipt-field completeness (adversarial, v0.2; signature leg added v0.3)",
        "origin": "Outside-audit candidate, confirmed by governed reproduction at fixture strength (examination record, 2026-11-01); encoded here as the v0.2 correction's regression proof. The re-signing control was added in v0.3 from the Nov 9, 2026 comparison's strict-strength V9 finding.",
        "strength": STRENGTH_LOCAL,
        "claim": "Independent receipt verification compares every field of a settlement receipt against the authoritative record — the stored request, the stored signed approval, and the gated store-history entry — and additionally verifies the receipt's signature under the engine's instance secret. A single-field alteration of the stated object, the prestate digest, the sequence number, or the approval digest is rejected; the poststate digest, already bound in v0.1, stays rejected; and a field-perfect receipt re-signed with the published key is rejected on its signature.",
        "controls": [pos, neg_object, neg_prestate, neg_seq, neg_approval, neg_poststate, neg_resign],
        "evidence_digest": digest_of(evidence),
        "evidence": evidence,
    }


# ---------------------------------------------------------------- A2

def test_a2():
    eng = new_engine()
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
    # carried by the engine's export_state/from_state dump/load (the
    # carriage of the examination record, formalized in v0.3 as an engine
    # method) through a JSON round-trip into a fresh Engine. Post-carriage
    # behavior must be identical: detection still transitive, reliance
    # through C and direct reliance on A both refused.
    eng2 = new_engine()
    for r in (A, B, C):
        rid_r, rel_r = _settle(eng2, r)
        eng2.execute(rel_r["release_id"], r)
    eng2.revoke(A_ID)
    carried = json.loads(json.dumps(eng2.export_state()))
    eng3 = Engine.from_state(carried)
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
        "After the engine's state is carried through the export/import dump/load into a fresh Engine (the restart carriage of the examination record), enforcement is identical: reliance through C and direct reliance on A are both refused, and C's derived status still reads contested_revoked_ancestry. In v0.1 the through-C reliance was admitted after the same carriage.",
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


# ---------------------------------------------------------------- A3

def test_a3():
    controls = []

    # (1) An approver who is not a registered principal at all: the exact
    # string the Nov 9 comparison executed under in v0.2.
    eng = new_engine()
    r1 = _req("obj-x", {"value": "a3-1", "version": 1}, [], "adv-a3-arb")
    rid1 = eng.propose(r1, proof_for(ACTOR, r1))["request_id"]
    s1, c1 = _attempt(lambda: eng.approve(rid1, "arbitrary-unauthorized-string", "00" * 32))
    ok1 = s1 == "refusal" and c1 == "approver_not_authorized" and not eng.approvals
    controls.append(_control(
        "arbitrary_string_approver_refused",
        "negative",
        "refused_approver_not_authorized",
        "refused_approver_not_authorized" if ok1 else f"unexpected:{s1}:{c1}",
        "An approval presented under the string 'arbitrary-unauthorized-string' — not a registered principal — is refused at approve() (approver_not_authorized) and records nothing. In v0.2 this exact string was accepted as an approver and its approval executed (Nov 9 comparison, V8 leg B).",
        f"approve(arbitrary string)={s1}:{c1}; approvals_recorded={len(eng.approvals)}",
    ))

    # (2) A registered approver, validly approving, whose authorization is
    # then withdrawn before execution: execution must refuse, no effect.
    eng = new_engine()
    r2 = _req("obj-x", {"value": "a3-2", "version": 1}, [], "adv-a3-stale")
    rid2, rel2 = _settle(eng, r2)
    eng.withdraw_principal(APPROVER)
    s2, c2 = _attempt(lambda: eng.execute(rel2["release_id"], r2))
    ok2 = (
        s2 == "refusal" and c2 == "approver_no_longer_authorized"
        and eng.state["obj-x"] == F.S0["obj-x"] and rid2 not in eng.receipts
    )
    controls.append(_control(
        "withdrawn_approver_execution_refused",
        "negative",
        "refused_approver_no_longer_authorized",
        "refused_approver_no_longer_authorized" if ok2 else f"unexpected:{s2}:{c2}",
        "An approval by a registered approver, followed by withdrawal of that approver's authorization before execution, refuses at execute() (approver_no_longer_authorized): execute() re-checks the approver's CURRENT authorization, so a standing approval from a withdrawn approver authorizes no effect. In v0.2 the fixture had no approver-authorization concept at all (V8 leg B: NOT_SUPPORTED).",
        f"execute(after approver withdrawal)={s2}:{c2}; state_unchanged={eng.state['obj-x'] == F.S0['obj-x']}; receipts={len(eng.receipts)}",
    ))

    # (3) Actor authentication: a bare actor string, and a registered
    # actor's name with a wrong proof, both refuse at propose().
    eng = new_engine()
    r3 = _req("obj-x", {"value": "a3-3", "version": 1}, [], "adv-a3-anon")
    r3["actor"] = "compromised-anyone"  # the Nov 9 V9 leg-B assertion, verbatim shape
    s3a, c3a = _attempt(lambda: eng.propose(r3, "00" * 32))
    r3b = _req("obj-x", {"value": "a3-3b", "version": 1}, [], "adv-a3-badproof")
    s3b, c3b = _attempt(lambda: eng.propose(r3b, "00" * 32))  # registered name, wrong proof
    ok3 = (
        s3a == "refusal" and c3a == "actor_not_authenticated"
        and s3b == "refusal" and c3b == "actor_not_authenticated"
        and not eng.requests
    )
    controls.append(_control(
        "unauthenticated_actor_proposal_refused",
        "negative",
        "refused_actor_not_authenticated",
        "refused_actor_not_authenticated" if ok3 else f"unexpected:bare={s3a}:{c3a};bad_proof={s3b}:{c3b}",
        "A proposal whose actor is an unregistered bare string ('compromised-anyone', the exact assertion the Nov 9 V9 leg B executed under in v0.2), and a proposal under a registered actor's name with an invalid proof, are both refused at propose() (actor_not_authenticated) and record nothing: propose() authenticates the actor's proof over the exact request bytes. What this does NOT claim: a valid proof presented by the wrong party (a genuinely compromised credential) is indistinguishable at this layer — that limitation stands, stated in the engine's strength statement.",
        f"propose(bare actor)={s3a}:{c3a}; propose(registered name, bad proof)={s3b}:{c3b}; requests_recorded={len(eng.requests)}",
    ))

    # (4) Sensitive read without the reader role: refused, and the refusal
    # is in the read audit. Two shapes: the registered actor (no reader
    # role) with its own valid proof, and no identity at all.
    eng = new_engine()
    s4a, c4a = _attempt(lambda: eng.query(
        "obj-secret", reader=ACTOR,
        reader_proof=proof_for(ACTOR, {"kind": "read", "object": "obj-secret", "reader": ACTOR}),
    ))
    s4b, c4b = _attempt(lambda: eng.query("obj-secret"))
    denied = [a for a in eng.read_audit if a["kind"] == "read_denied"]
    ok4 = (
        s4a == "refusal" and c4a == "read_not_authorized"
        and s4b == "refusal" and c4b == "read_not_authorized"
        and len(denied) == 2
    )
    controls.append(_control(
        "unauthorized_sensitive_read_refused_and_audited",
        "negative",
        "refused_read_not_authorized_audited",
        "refused_read_not_authorized_audited" if ok4 else f"unexpected:actor={s4a}:{c4a};anon={s4b}:{c4b};denied_audited={len(denied)}",
        "A read of the sensitive-classification object by a principal without the reader_sensitive role (presenting its own valid proof), and a read with no identity at all, are both refused (read_not_authorized), and both refusals stand in the read audit. In v0.2 query() took no identity and served a state digest to any caller (Nov 9 comparison, V12: NOT_SUPPORTED).",
        f"query(actor, no reader role)={s4a}:{c4a}; query(anonymous)={s4b}:{c4b}; read_denied_entries={len(denied)}",
    ))

    # (5) The positive leg: the authorized sensitive reader reads, and the
    # served read is audited beside the refusals.
    q5 = eng.query(
        "obj-secret", reader=READER,
        reader_proof=proof_for(READER, {"kind": "read", "object": "obj-secret", "reader": READER}),
    )
    served = [a for a in eng.read_audit if a["kind"] == "read_served"]
    ok5 = (
        q5["kind"] == "query_view"
        and q5["classification"] == "sensitive"
        and q5["state_digest"] == digest_of(F.S0["obj-secret"])
        and len(served) == 1
    )
    controls.append(_control(
        "authorized_sensitive_read_served_and_audited",
        "positive",
        "authorized_sensitive_read_served_audited",
        "authorized_sensitive_read_served_audited" if ok5 else "unexpected",
        "A read of the sensitive object by the registered sensitive reader, presenting a valid proof over the read, is served as a query view of the classified state, and the served read stands in the read audit: authorization gates the read, and the audit covers both outcomes.",
        f"query(authorized reader) kind={q5['kind']}; classification={q5['classification']}; digest_matches={q5['state_digest'] == digest_of(F.S0['obj-secret'])}; read_served_entries={len(served)}",
    ))

    evidence = {
        "refusal_codes": {"arbitrary_approver": c1, "withdrawn_approver": c2,
                          "bare_actor": c3a, "bad_proof": c3b,
                          "unauthorized_read": c4a, "anonymous_read": c4b},
        "read_audit": eng.read_audit,
    }
    return {
        "test_id": "A3",
        "title": "Authorization completeness (adversarial, v0.3)",
        "origin": "Measured fixture failures of the Nov 9, 2026 comparative examination (frozen protocol, same-team execution): V8 approver authorization absent, V12 read authorization absent, V9 leg B actor unauthenticated, V9 strict key published. Encoded here as the v0.3 corrections' regression proof.",
        "strength": STRENGTH_LOCAL,
        "claim": "Authorization in v0.3 is a property of registered principals, checked where it bites: approve() admits only a registered, active approver presenting a valid proof; execute() re-checks the approver's current authorization, so withdrawal after approval blocks the effect; propose() authenticates the actor's proof over the exact request; sensitive reads require the reader role and are audited, served or refused. The compromised-but-valid-credential case is not claimed: it is a standing limitation, stated in the engine's strength statement, not silently absorbed into these passes.",
        "controls": controls,
        "evidence_digest": digest_of(evidence),
        "evidence": evidence,
    }


ALL_ADVERSARIAL = [test_a1, test_a2, test_a3]
