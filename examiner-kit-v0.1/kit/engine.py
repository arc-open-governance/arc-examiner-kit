"""Fixture reference engine for the ARC Examiner Kit.

STRENGTH — READ THIS FIRST. This engine is a small, self-contained model of
the record-layer semantics that the ARC public reference establishes
(`statement5.py`: a Statement binds sha(request); signed reserve/commit/
observe envelopes bind the same request digest; `arcnet2.py`: a signed
approval carries request_digest) and that the live VALIS wrapper exposes at
v0.1 (propose -> settlement -> release -> execute -> evidence -> receipt;
single-use releases; revocation with declared dependence via
bounds.depends_on, deployed as release 254).

It is NOT the production wrapper, NOT the published reference implementation,
and it proves nothing about any deployed system. It exists so an examiner can
run Issue #35's six tests against a frozen, inspectable implementation of the
*claimed semantics* and check that the claims are coherent, reproducible, and
honestly scoped — and so the same tests can be pointed at a real stack under
Issue #31's Agent Consequence Challenge.

Signatures here are HMAC-SHA256 over canonical bytes with a PUBLISHED fixture
key (below). They demonstrate digest binding structure only. They are not
credentials, not identity, and not production cryptography.

What this engine deliberately does NOT do (matching Issue #35's "Do not
claim" list):
- It does not detect ungated actions by itself. Test T6 ships an explicit
  observer comparison; detection is exactly as strong as that comparison.
- It does not trace undeclared dependencies. Dependency checks use the
  declared `depends_on` graph only (Test T5's negative control shows an
  undeclared dependence passing undetected — a limit, on the record).
- It does not promise exactly-once effects in any outside world. Its effect
  store is a local dictionary; exactly-once here is a property of this
  fixture's idempotency ledger, nothing more.
"""

import copy
import hashlib
import hmac

from .canon import canonical, digest_of, request_id_for

# Published fixture key. Not a credential. Anyone may recompute every
# signature in this kit; that is the point.
FIXTURE_KEY = b"arc-examiner-kit-fixture-key-v0.1"


def _sign(payload: dict) -> str:
    return hmac.new(FIXTURE_KEY, canonical(payload), hashlib.sha256).hexdigest()


class Refusal(Exception):
    """A governed refusal. `code` is the machine-readable reason."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail


class AckLost(Exception):
    """The effect committed; the caller's response was lost in transit."""

    def __init__(self, request_id: str):
        super().__init__("ack_lost")
        self.request_id = request_id


class Engine:
    def __init__(self, initial_state: dict):
        self.initial_state = copy.deepcopy(initial_state)
        self.state = copy.deepcopy(initial_state)  # the synthetic effect store
        self.store_history = []  # every store mutation, gated or direct
        self.requests = {}  # request_id -> request (as proposed)
        self.approvals = {}  # approval_id -> approval record
        self.releases = {}  # release_id -> release record
        self.receipts = {}  # request_id -> settlement receipt
        self.revoked = set()  # request_ids whose authority was revoked

    # -- proposal / settlement -------------------------------------------------

    def propose(self, request: dict) -> dict:
        rid = request_id_for(request)
        if rid not in self.requests:
            self.requests[rid] = copy.deepcopy(request)
        return {"request_id": rid, "request_digest": digest_of(request)}

    def approve(self, request_id: str, approver: str) -> dict:
        if request_id not in self.requests:
            raise Refusal("unknown_request", request_id)
        req_digest = digest_of(self.requests[request_id])
        payload = {
            "request_digest": req_digest,
            "decision": "approve",
            "approver": approver,
        }
        approval = dict(payload)
        approval["approval_id"] = "appr-" + digest_of(payload)[7:23]
        approval["signature"] = _sign(payload)
        self.approvals[approval["approval_id"]] = approval
        return copy.deepcopy(approval)

    def _approval_for(self, request_id: str):
        for a in self.approvals.values():
            if a["request_digest"] == digest_of(self.requests[request_id]):
                return a
        return None

    def issue_release(self, request_id: str) -> dict:
        if request_id not in self.requests:
            raise Refusal("unknown_request", request_id)
        if request_id in self.receipts:
            raise Refusal("already_committed", request_id)
        for r in self.releases.values():
            if r["request_digest"] == digest_of(self.requests[request_id]) and not r["consumed"]:
                raise Refusal("release_already_issued", request_id)
        approval = self._approval_for(request_id)
        if approval is None:
            raise Refusal("no_valid_release", "no approval on record")
        payload = {
            "request_digest": digest_of(self.requests[request_id]),
            "approval_digest": digest_of(
                {k: approval[k] for k in ("request_digest", "decision", "approver", "signature")}
            ),
        }
        release = dict(payload)
        release["release_id"] = "rel-" + digest_of(payload)[7:23]
        release["consumed"] = False
        self.releases[release["release_id"]] = release
        return copy.deepcopy(release)

    # -- execution ---------------------------------------------------------------

    def _check_dependencies(self, request: dict):
        for dep in request.get("depends_on", []):
            if dep not in self.requests:
                raise Refusal("dependency_unknown", dep)
            if dep in self.revoked:
                raise Refusal("dependency_revoked", dep)
            if dep not in self.receipts:
                raise Refusal("dependency_unsettled", dep)

    def execute(self, release_id: str, presented_request: dict, drop_ack: bool = False) -> dict:
        release = self.releases.get(release_id)
        if release is None:
            raise Refusal("no_valid_release", release_id)
        if release["consumed"]:
            raise Refusal("release_already_consumed", release_id)
        presented_digest = digest_of(presented_request)
        if presented_digest != release["request_digest"]:
            raise Refusal("request_binding_mismatch", presented_digest)
        request_id = request_id_for(presented_request)
        if request_id in self.revoked:
            raise Refusal("request_revoked", request_id)
        self._check_dependencies(presented_request)
        # Idempotency: one idempotency key binds exactly one request digest.
        for other_id, other in self.requests.items():
            if (
                other.get("idempotency_key") == presented_request.get("idempotency_key")
                and other_id in self.receipts
                and other_id != request_id
            ):
                raise Refusal("idempotency_conflict", presented_request.get("idempotency_key", ""))
        approval = self._approval_for(request_id)
        if approval is None or approval["signature"] != _sign(
            {k: approval[k] for k in ("request_digest", "decision", "approver")}
        ):
            raise Refusal("approval_signature_invalid", request_id)
        # Commit the synthetic effect.
        obj = presented_request["object"]
        prestate = copy.deepcopy(self.state.get(obj))
        self.state[obj] = copy.deepcopy(presented_request["value"])
        poststate = copy.deepcopy(self.state[obj])
        self.store_history.append(
            {
                "object": obj,
                "value": copy.deepcopy(presented_request["value"]),
                "via": "gate",
                "request_id": request_id,
                "poststate_digest": digest_of(poststate),
            }
        )
        receipt = {
            "kind": "settlement_receipt",
            "request_id": request_id,
            "request_digest": presented_digest,
            "approval_digest": release["approval_digest"],
            "effect": {
                "object": obj,
                "prestate_digest": digest_of(prestate),
                "poststate_digest": digest_of(poststate),
            },
            "seq": len(self.store_history) - 1,
        }
        self.receipts[request_id] = receipt
        release["consumed"] = True
        if drop_ack:
            raise AckLost(request_id)
        return copy.deepcopy(receipt)

    def retry(self, request_id: str) -> dict:
        """Reconciliation after a lost acknowledgment: read the record back.

        Never re-applies an effect. Returns the standing receipt if one
        committed, so the caller can resolve UNKNOWN_EFFECT by evidence.
        """
        if request_id in self.receipts:
            return {"status": "already_committed", "receipt": copy.deepcopy(self.receipts[request_id])}
        return {"status": "not_committed", "receipt": None}

    # -- observation ---------------------------------------------------------------

    def query(self, obj: str) -> dict:
        """A read. Typed as a query view; it is not, and cannot become, a
        settlement receipt. (Design convention for ordinary queries in this
        fixture — not a universal security law: a disclosure-sensitive read
        can itself be consequential under a real policy.)"""
        return {
            "kind": "query_view",
            "object": obj,
            "state_digest": digest_of(self.state.get(obj)),
            "history_len": len(self.store_history),
        }

    # -- revocation / dependence ---------------------------------------------------

    def revoke(self, request_id: str) -> dict:
        if request_id not in self.requests:
            raise Refusal("unknown_request", request_id)
        self.revoked.add(request_id)
        return {
            "kind": "revocation",
            "request_id": request_id,
            "request_digest": digest_of(self.requests[request_id]),
            "history_len": len(self.store_history),  # history is NOT erased
        }

    def dependents_of(self, request_id: str) -> list:
        """Declared-dependence traversal only. Undeclared dependents are
        invisible to this function — see Test T5's negative control."""
        found = []
        frontier = {request_id}
        seen = set()
        while frontier:
            nxt = set()
            for rid, req in self.requests.items():
                if rid in seen:
                    continue
                if any(dep in frontier for dep in req.get("depends_on", [])):
                    found.append(rid)
                    seen.add(rid)
                    nxt.add(rid)
            frontier = nxt
        return sorted(found)

    def derived_state_status(self, request_id: str) -> str:
        deps = []
        stack = list(self.requests[request_id].get("depends_on", []))
        while stack:
            dep = stack.pop()
            deps.append(dep)
            if dep in self.requests:
                stack.extend(self.requests[dep].get("depends_on", []))
        if any(dep in self.revoked for dep in deps):
            return "contested_revoked_ancestry"
        if all(dep in self.receipts for dep in deps):
            return "settled"
        return "unsettled"

    # -- the unwired route / observer ----------------------------------------------

    def direct_write(self, obj: str, value) -> dict:
        """A write through a route NOT wired to the gate (Test T6's bypass).

        The gate cannot refuse this: it never sees it. The write lands in the
        same effect store with no request, no approval, and no receipt.
        """
        self.state[obj] = copy.deepcopy(value)
        entry = {
            "object": obj,
            "value": copy.deepcopy(value),
            "via": "direct",
            "request_id": None,
            "poststate_digest": digest_of(value),
        }
        self.store_history.append(entry)
        return copy.deepcopy(entry)

    def observer_scan(self) -> list:
        """Explicit observer comparison: store mutations vs the receipt
        ledger. This comparison IS the detection mechanism in this fixture —
        nothing detects anything while it is not run."""
        flagged = []
        for i, h in enumerate(self.store_history):
            if h["request_id"] is None or h["request_id"] not in self.receipts:
                flagged.append({"history_index": i, "object": h["object"], "via": h["via"]})
        return flagged


def verify_receipt(engine: Engine, record: dict) -> tuple:
    """Independent receipt verification, as an examiner would run it.

    Returns (ok, code). A record verifies only if it is a settlement receipt
    bound to a proposed request's digest, backed by a validly signed approval,
    and matched by a gated store mutation with the same poststate digest.
    """
    if record.get("kind") != "settlement_receipt":
        return False, "not_a_settlement_receipt"
    rid = record.get("request_id")
    if rid not in engine.requests:
        return False, "unknown_request"
    if record.get("request_digest") != digest_of(engine.requests[rid]):
        return False, "request_digest_mismatch"
    approval = engine._approval_for(rid)
    if approval is None:
        return False, "no_approval_on_record"
    if approval["signature"] != _sign(
        {k: approval[k] for k in ("request_digest", "decision", "approver")}
    ):
        return False, "approval_signature_invalid"
    for h in engine.store_history:
        if (
            h["request_id"] == rid
            and h["via"] == "gate"
            and h["poststate_digest"] == record.get("effect", {}).get("poststate_digest")
        ):
            return True, "verified"
    return False, "no_matching_gated_effect"
