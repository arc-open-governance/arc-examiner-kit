"""Fixture reference engine for the ARC Examiner Kit — v0.3.

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

Version note (v0.3): this engine corrects the five fixture weaknesses that the
Nov 9, 2026 comparative examination measured against a frozen conventional
baseline (same-team execution; the baseline beat the v0.2 fixture at strict
strength, 10 PASS / 2 FAIL against the fixture's 8 PASS / 4 FAIL). The
corrections, each proven by adversarial test A3 and by the frozen-protocol
rerun recorded beside the original comparison:

1. MEDIATION AT THE STORE (was: V4 prevention FAIL). The effect store is now
   a MediatedStore. Its only write path is `commit()`, which demands a
   single-use dispatch capability minted inside `execute()` after every
   governance check has passed, bound to the exact object, value digest,
   and request. The unwired route (`direct_write`) reaches the store's raw
   entry and is refused BY THE STORE (`ungoverned_write`); state is
   unchanged and the refused attempt is recorded at the boundary. Scope,
   stated plainly: this is API-level mediation inside a single-process
   fixture. It demonstrates the architectural property — no write route
   the fixture exposes bypasses the gate — at semantics strength. It does
   not demonstrate OS-level isolation: a hostile caller with Python
   introspection over the fixture's own process is outside this fixture's
   threat model, exactly as it would be for any in-process model.
2. APPROVER AUTHORIZATION (was: V8 NOT_SUPPORTED / strict FAIL). Principals
   are registered with roles and per-principal secrets. `approve()` admits
   only a registered, currently active approver-role principal presenting
   a valid proof over the approval payload; any other approver string is
   refused (`approver_not_authorized`) before anything is recorded.
   `execute()` re-checks the approver's CURRENT authorization, so an
   approver withdrawn after approval blocks execution
   (`approver_no_longer_authorized`) with no effect.
3. READ AUTHORIZATION (was: V12 NOT_SUPPORTED / strict FAIL). Objects carry
   a classification. A sensitive read requires a registered principal
   holding the sensitive-reader role and a valid proof over the read;
   unauthorized sensitive reads are refused (`read_not_authorized`) and
   every sensitive read attempt, served or refused, is written to the read
   audit. Ordinary reads of standard-classification objects keep the v0.2
   query-view semantics.
4. INSTANCE-SECRET SIGNING (was: V9 strict FAIL). Approvals and receipts
   are signed with a per-engine-instance secret drawn from `os.urandom`
   at construction. That secret is never published in this kit and never
   leaves the engine. `verify_receipt` checks the receipt's signature
   after comparing every field against the authoritative record, so a
   field-perfect receipt re-signed with the published fixture key is
   rejected on the signature (`receipt_signature_invalid`): forgery
   rejection is now a signature property, not only a ledger property.
   (The kit's own exam passes an explicit fixed stand-in secret to the
   engines it constructs, purely so the kit's published `results.json`
   stays byte-deterministic. The mechanism under examination — sign with
   a secret the attacker does not hold — is identical; the comparison
   harness constructs its engine with no supplied secret, so the secret
   there is genuinely non-public.)
5. ACTOR AUTHENTICATION (was: V9 leg B, failed sub-leg, unauthenticated
   half). `propose()` requires the request's actor to be a registered,
   active actor-role principal presenting a valid proof over the exact
   request bytes (`actor_not_authenticated` otherwise). A bare actor
   string no longer executes. What is NOT fixed, by explicit re-scope:
   a credential that is valid and correctly presented but held by the
   wrong party (a genuinely compromised credential, work inside policy)
   is still accepted — a settlement layer cannot distinguish the holder
   from a thief holding the same credential, and anomaly detection is an
   identity-layer control this fixture does not claim. That limitation
   was frozen for both systems in the Nov 9 protocol and stands.

The principal secrets in DEFAULT_PRINCIPALS are PUBLISHED fixture material,
like the v0.1/v0.2 FIXTURE_KEY: anyone may recompute a fixture principal's
proof, and that is the point — the registry, role, proof, and currency
*mechanisms* are what v0.3 adds and demonstrates. FIXTURE_KEY itself is
retained, and signs nothing in v0.3, so the frozen V9 attack (forge with
the best published key) can be run exactly as specified.

What this engine still deliberately does NOT do:
- It does not trace undeclared dependencies. Dependency checks use the
  declared `depends_on` graph only (Test T5's negative control shows an
  undeclared dependence passing undetected — a limit, on the record).
- It does not promise exactly-once effects in any outside world. Its
  effect store is a local object; exactly-once here is a property of this
  fixture's idempotency ledger, nothing more.
- It does not detect compromised-but-valid credentials (item 5 above).
"""

import copy
import hashlib
import hmac
import os

from .canon import canonical, digest_of, request_id_for

# Published fixture key (v0.1/v0.2). In v0.3 it signs NOTHING. It is retained
# so an examiner can run the frozen forgery attack — sign with the best key
# available to an attacker — against a kit whose real signatures no longer
# depend on anything published.
FIXTURE_KEY = b"arc-examiner-kit-fixture-key-v0.1"


def _sign(payload: dict) -> str:
    """HMAC under the PUBLISHED fixture key. Attacker-grade material in
    v0.3: useful for constructing forgeries, useless for making one verify."""
    return hmac.new(FIXTURE_KEY, canonical(payload), hashlib.sha256).hexdigest()


def _hmac_hex(secret: bytes, payload: dict) -> str:
    return hmac.new(secret, canonical(payload), hashlib.sha256).hexdigest()


# Published fixture principal registry. Roles:
#   "actor"             — may propose requests (as the request's actor);
#   "approver"          — may approve requests;
#   "reader_sensitive"  — may read sensitive-classification objects.
# The secrets are published so the mechanism is inspectable end to end.
DEFAULT_PRINCIPALS = {
    "examiner-fixture": {
        "roles": ["actor"],
        "secret_hex": b"arc-examiner-kit-actor-secret-v0.3".hex(),
        "active": True,
    },
    "fixture-authority": {
        "roles": ["approver"],
        "secret_hex": b"arc-examiner-kit-approver-secret-v0.3".hex(),
        "active": True,
    },
    "fixture-reader": {
        "roles": ["reader_sensitive"],
        "secret_hex": b"arc-examiner-kit-reader-secret-v0.3".hex(),
        "active": True,
    },
}


def proof_for(principal_name: str, payload: dict) -> str:
    """The proof a fixture principal presents: HMAC of the canonical payload
    under the principal's (published, fixture) secret. Raises KeyError for an
    unregistered name — an unregistered principal has no proof to present."""
    secret = bytes.fromhex(DEFAULT_PRINCIPALS[principal_name]["secret_hex"])
    return _hmac_hex(secret, payload)


class Refusal(Exception):
    """A governed refusal. `code` is the machine-readable reason."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail


class StoreRefusal(Refusal):
    """A refusal issued by the effect store itself, at the store boundary,
    for a write that did not arrive through the governed dispatch path."""


class AckLost(Exception):
    """The effect committed; the caller's response was lost in transit."""

    def __init__(self, request_id: str):
        super().__init__("ack_lost")
        self.request_id = request_id


class _DispatchCapability:
    """Single-use write capability, minted only inside Engine.execute()
    after every governance check has passed, bound to one object, one value
    digest, and one request. The MediatedStore accepts no write without one."""

    def __init__(self, obj: str, value_digest: str, request_id: str):
        self.obj = obj
        self.value_digest = value_digest
        self.request_id = request_id
        self.consumed = False


class MediatedStore:
    """The synthetic effect store, mediated at its own boundary.

    `commit()` is the only route that mutates state, and it demands a valid,
    unconsumed _DispatchCapability. `raw_write()` is the unwired route an
    ungated writer would take; the store refuses it itself, records the
    refused attempt, and leaves state unchanged. Reads of state are served
    as deep copies; nothing outside this class holds a reference to the
    live state dict.
    """

    def __init__(self, initial_state: dict):
        self._state = copy.deepcopy(initial_state)
        self._history = []  # gated mutations only
        self.refused_attempts = []  # writes the store itself turned away

    def snapshot(self) -> dict:
        return copy.deepcopy(self._state)

    def get(self, obj: str):
        return copy.deepcopy(self._state.get(obj))

    def history(self) -> list:
        return copy.deepcopy(self._history)

    def commit(self, capability, obj: str, value, request_id: str) -> dict:
        if (
            not isinstance(capability, _DispatchCapability)
            or capability.consumed
            or capability.obj != obj
            or capability.value_digest != digest_of(value)
            or capability.request_id != request_id
        ):
            self.refused_attempts.append(
                {"object": obj, "via": "store_commit_without_valid_capability",
                 "request_id": request_id}
            )
            raise StoreRefusal("ungoverned_write", obj)
        capability.consumed = True
        self._state[obj] = copy.deepcopy(value)
        entry = {
            "object": obj,
            "value": copy.deepcopy(value),
            "via": "gate",
            "request_id": request_id,
            "poststate_digest": digest_of(self._state[obj]),
        }
        self._history.append(entry)
        return copy.deepcopy(entry)

    def raw_write(self, obj: str, value) -> dict:
        """The unwired route. The store refuses it at its own boundary:
        no capability, no write — whoever calls, however they call."""
        self.refused_attempts.append(
            {"object": obj, "via": "direct", "request_id": None}
        )
        raise StoreRefusal("ungoverned_write", obj)


class Engine:
    def __init__(self, initial_state: dict, principals: dict = None,
                 classifications: dict = None, engine_secret: bytes = None):
        self.initial_state = copy.deepcopy(initial_state)
        self._store = MediatedStore(initial_state)
        self.requests = {}  # request_id -> request (as proposed)
        self.approvals = {}  # approval_id -> approval record
        self.releases = {}  # release_id -> release record
        self.receipts = {}  # request_id -> settlement receipt
        self.revoked = set()  # request_ids whose authority was revoked
        self.principals = copy.deepcopy(
            principals if principals is not None else DEFAULT_PRINCIPALS
        )
        self.classifications = dict(classifications or {})  # obj -> "sensitive"
        self.read_audit = []  # every sensitive read attempt, served or refused
        # Per-instance signing secret. Never published, never leaves the
        # engine except inside export_state() carriage (where it travels
        # as engine state, to the engine's own successor instance).
        self._engine_secret = (
            engine_secret if engine_secret is not None else os.urandom(32)
        )

    # -- read-only views of store state ------------------------------------

    @property
    def state(self) -> dict:
        return self._store.snapshot()

    @property
    def store_history(self) -> list:
        return self._store.history()

    @property
    def store_refused_attempts(self) -> list:
        return copy.deepcopy(self._store.refused_attempts)

    def _engine_sign(self, payload: dict) -> str:
        return _hmac_hex(self._engine_secret, payload)

    # -- principals ----------------------------------------------------------

    def _principal(self, name: str):
        return self.principals.get(name)

    def _check_proof(self, name: str, role: str, payload: dict, proof) -> dict:
        """Return the principal record iff `name` is registered, active,
        holds `role`, and `proof` is its valid HMAC over `payload`."""
        p = self._principal(name)
        if p is None or not p.get("active") or role not in p.get("roles", []):
            return None
        expected = _hmac_hex(bytes.fromhex(p["secret_hex"]), payload)
        if not isinstance(proof, str) or not hmac.compare_digest(expected, proof):
            return None
        return p

    def withdraw_principal(self, name: str) -> dict:
        """Withdraw a principal's authorization (e.g. a reviewer who has
        left the role). Standing approvals are NOT erased; execute()
        re-checks currency, which is what makes the withdrawal bite."""
        if name not in self.principals:
            raise Refusal("unknown_principal", name)
        self.principals[name]["active"] = False
        return {"kind": "principal_withdrawal", "principal": name}

    # -- proposal / settlement -------------------------------------------------

    def propose(self, request: dict, actor_proof: str = None) -> dict:
        actor = request.get("actor")
        if self._check_proof(actor, "actor", request, actor_proof) is None:
            raise Refusal("actor_not_authenticated", str(actor))
        rid = request_id_for(request)
        if rid not in self.requests:
            self.requests[rid] = copy.deepcopy(request)
        return {"request_id": rid, "request_digest": digest_of(request)}

    def approve(self, request_id: str, approver: str, approver_proof: str = None) -> dict:
        if request_id not in self.requests:
            raise Refusal("unknown_request", request_id)
        req_digest = digest_of(self.requests[request_id])
        payload = {
            "request_digest": req_digest,
            "decision": "approve",
            "approver": approver,
        }
        if self._check_proof(approver, "approver", payload, approver_proof) is None:
            raise Refusal("approver_not_authorized", str(approver))
        approval = dict(payload)
        approval["approval_id"] = "appr-" + digest_of(payload)[7:23]
        approval["signature"] = self._engine_sign(payload)
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

    def _revoked_in_declared_ancestry(self, request_id: str):
        """The first revoked request in request_id's declared ancestry —
        request_id itself included — or None. Declared depends_on only,
        transitive: the same traversal derived_state_status performs, so
        enforcement sees exactly what detection reports."""
        seen = set()
        stack = [request_id]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            if cur in self.revoked:
                return cur
            if cur in self.requests:
                stack.extend(self.requests[cur].get("depends_on", []))
        return None

    def _check_dependencies(self, request: dict):
        for dep in request.get("depends_on", []):
            if dep not in self.requests:
                raise Refusal("dependency_unknown", dep)
            revoked_hit = self._revoked_in_declared_ancestry(dep)
            if revoked_hit is not None:
                raise Refusal("dependency_revoked", revoked_hit)
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
        if approval is None or approval["signature"] != self._engine_sign(
            {k: approval[k] for k in ("request_digest", "decision", "approver")}
        ):
            raise Refusal("approval_signature_invalid", request_id)
        # Approver currency: the approver who approved must STILL be a
        # registered, active approver at execution time. A withdrawn
        # approver's standing approval no longer authorizes an effect.
        approver_now = self._principal(approval["approver"])
        if (
            approver_now is None
            or not approver_now.get("active")
            or "approver" not in approver_now.get("roles", [])
        ):
            raise Refusal("approver_no_longer_authorized", approval["approver"])
        # Commit the synthetic effect — through the store's only write
        # path, under a single-use capability minted here, after every
        # check above has passed.
        obj = presented_request["object"]
        prestate = self._store.get(obj)
        capability = _DispatchCapability(obj, digest_of(presented_request["value"]), request_id)
        entry = self._store.commit(capability, obj, presented_request["value"], request_id)
        poststate = self._store.get(obj)
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
            "seq": len(self._store.history()) - 1,
        }
        receipt["signature"] = self._engine_sign(receipt)
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

    def query(self, obj: str, reader: str = None, reader_proof: str = None) -> dict:
        """A read. Typed as a query view; it is not, and cannot become, a
        settlement receipt.

        Standard-classification objects keep the v0.2 semantics: any
        caller may take the view. A SENSITIVE-classification object is
        disclosure-sensitive: the read is itself consequential, so it
        requires a registered principal holding the reader_sensitive role
        and a valid proof over the read, and every attempt — served or
        refused — is written to the read audit."""
        classification = self.classifications.get(obj, "standard")
        if classification == "sensitive":
            payload = {"kind": "read", "object": obj, "reader": reader}
            if self._check_proof(reader, "reader_sensitive", payload, reader_proof) is None:
                self.read_audit.append(
                    {"kind": "read_denied", "object": obj, "reader": reader}
                )
                raise Refusal("read_not_authorized", obj)
            self.read_audit.append(
                {"kind": "read_served", "object": obj, "reader": reader}
            )
        return {
            "kind": "query_view",
            "object": obj,
            "classification": classification,
            "state_digest": digest_of(self._store.get(obj)),
            "history_len": len(self._store.history()),
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
            "history_len": len(self._store.history()),  # history is NOT erased
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

        In v0.2 this landed: the gate never saw it. In v0.3 the route
        reaches the store, and THE STORE refuses it (`ungoverned_write`)
        — mediation lives at the storage boundary, not in the gate's
        field of view. State is unchanged; the attempt is recorded in
        the store's refused-attempt log."""
        return self._store.raw_write(obj, value)

    def observer_scan(self) -> list:
        """Explicit observer comparison: store mutations vs the receipt
        ledger. This comparison IS the detection mechanism in this fixture —
        nothing detects anything while it is not run."""
        flagged = []
        for i, h in enumerate(self._store.history()):
            if h["request_id"] is None or h["request_id"] not in self.receipts:
                flagged.append({"history_index": i, "object": h["object"], "via": h["via"]})
        return flagged

    # -- carriage (restart by dump/load; the kit ships no persistence API) --------

    def export_state(self) -> dict:
        """The engine's full state as JSON-able data — the carriage the
        A2 restart control and the comparison harness use in place of a
        persistence API. Includes the instance secret and the principal
        registry: they ARE engine state, and a successor instance that
        could not verify standing receipts would not be the same engine."""
        return {
            "initial_state": copy.deepcopy(self.initial_state),
            "store": {
                "state": self._store.snapshot(),
                "history": self._store.history(),
                "refused_attempts": copy.deepcopy(self._store.refused_attempts),
            },
            "requests": copy.deepcopy(self.requests),
            "approvals": copy.deepcopy(self.approvals),
            "releases": copy.deepcopy(self.releases),
            "receipts": copy.deepcopy(self.receipts),
            "revoked": sorted(self.revoked),
            "principals": copy.deepcopy(self.principals),
            "classifications": dict(self.classifications),
            "read_audit": copy.deepcopy(self.read_audit),
            "engine_secret_hex": self._engine_secret.hex(),
        }

    @classmethod
    def from_state(cls, dump: dict) -> "Engine":
        eng = cls(
            dump["initial_state"],
            principals=dump["principals"],
            classifications=dump["classifications"],
            engine_secret=bytes.fromhex(dump["engine_secret_hex"]),
        )
        eng._store._state = copy.deepcopy(dump["store"]["state"])
        eng._store._history = copy.deepcopy(dump["store"]["history"])
        eng._store.refused_attempts = copy.deepcopy(dump["store"]["refused_attempts"])
        eng.requests = copy.deepcopy(dump["requests"])
        eng.approvals = copy.deepcopy(dump["approvals"])
        eng.releases = copy.deepcopy(dump["releases"])
        eng.receipts = copy.deepcopy(dump["receipts"])
        eng.revoked = set(dump["revoked"])
        eng.read_audit = copy.deepcopy(dump["read_audit"])
        return eng


def verify_receipt(engine: Engine, record: dict) -> tuple:
    """Independent receipt verification, as an examiner would run it.

    Returns (ok, code). A record verifies only if EVERY field of the
    presented receipt matches the authoritative record the engine holds,
    AND the receipt's signature is a valid HMAC under the engine's
    per-instance secret (checked last, so a single-field alteration still
    reports its field-specific code, as A1 froze):

    - kind: a settlement receipt (not a query view or any other record);
    - request_id / request_digest: bound to the stored request's digest;
    - approval_digest: recomputed from the stored approval — itself
      checked for a valid signature over its own fields — by the same
      derivation issue_release used when the release was created;
    - effect.object: the stored request's object;
    - effect.prestate_digest: the digest of that object replayed through
      the store history up to (not including) the gated entry;
    - effect.poststate_digest: the gated entry's recorded poststate;
    - seq: the gated entry's index in the store history;
    - signature: HMAC under the engine's instance secret over every other
      field of the receipt. In v0.1/v0.2 the only signature material was
      a published key, so a signature alone authenticated nothing and
      rejection rested entirely on the comparisons above. In v0.3 a
      field-perfect receipt re-signed with the published key fails here.

    v0.1 compared only the request digest, the approval signature, and
    the poststate digest; v0.2 compared them all; v0.3 keeps every v0.2
    comparison and adds the signature check.
    """
    if record.get("kind") != "settlement_receipt":
        return False, "not_a_settlement_receipt"
    rid = record.get("request_id")
    if rid not in engine.requests:
        return False, "unknown_request"
    request = engine.requests[rid]
    if record.get("request_digest") != digest_of(request):
        return False, "request_digest_mismatch"
    approval = engine._approval_for(rid)
    if approval is None:
        return False, "no_approval_on_record"
    if approval["signature"] != engine._engine_sign(
        {k: approval[k] for k in ("request_digest", "decision", "approver")}
    ):
        return False, "approval_signature_invalid"
    expected_approval_digest = digest_of(
        {k: approval[k] for k in ("request_digest", "decision", "approver", "signature")}
    )
    if record.get("approval_digest") != expected_approval_digest:
        return False, "approval_digest_mismatch"
    history = engine.store_history
    gated_index = None
    for i, h in enumerate(history):
        if h["request_id"] == rid and h["via"] == "gate":
            gated_index = i
            break
    if gated_index is None:
        return False, "no_matching_gated_effect"
    entry = history[gated_index]
    effect = record.get("effect", {})
    if effect.get("object") != request["object"]:
        return False, "effect_object_mismatch"
    replayed = copy.deepcopy(engine.initial_state)
    for h in history[:gated_index]:
        replayed[h["object"]] = h["value"]
    if effect.get("prestate_digest") != digest_of(replayed.get(request["object"])):
        return False, "prestate_digest_mismatch"
    if effect.get("poststate_digest") != entry["poststate_digest"]:
        return False, "no_matching_gated_effect"
    if record.get("seq") != gated_index:
        return False, "seq_mismatch"
    presented_sig = record.get("signature")
    expected_sig = engine._engine_sign(
        {k: v for k, v in record.items() if k != "signature"}
    )
    if not isinstance(presented_sig, str) or not hmac.compare_digest(expected_sig, presented_sig):
        return False, "receipt_signature_invalid"
    return True, "verified"
