"""Frozen fixtures for Examiner Kit v0.1.

Every input is fixed in this file. `fixtures/fixture-manifest.json` pins the
digest of the initial state and of every request, so a runner can confirm it
is exercising exactly the frozen inputs. No clocks, no randomness, no
environment reads.
"""

import copy

from .canon import request_id_for

# Frozen initial state S0.
S0 = {
    "obj-x": {"value": "alpha", "version": 0},
    "obj-y": {"value": "seed", "version": 0},
    "obj-z": {"value": "empty", "version": 0},
}

ACTOR = "examiner-fixture"
APPROVER = "fixture-authority"


def _req(obj, value, depends_on, idem):
    return {
        "actor": ACTOR,
        "action": "set",
        "object": obj,
        "value": value,
        "depends_on": list(depends_on),
        "idempotency_key": idem,
    }


# Test 1 / Test 2 share a target shape (separate engines per test).
REQ_T1 = _req("obj-x", {"value": "beta", "version": 1}, [], "exam-t1-001")
REQ_T2 = _req("obj-x", {"value": "beta", "version": 1}, [], "exam-t2-001")
# Test 2's mutation: the exact approved request with its target changed X->Y.
REQ_T2_MUTATED = _req("obj-y", {"value": "beta", "version": 1}, [], "exam-t2-001")

# Test 3's authorized mutation.
REQ_T3 = _req("obj-x", {"value": "gamma", "version": 2}, [], "exam-t3-001")

# Test 4: one request, and a second request reusing its idempotency key with
# a different payload (the negative control).
REQ_T4 = _req("obj-x", {"value": "delta", "version": 3}, [], "exam-t4-001")
REQ_T4_CONFLICT = _req("obj-x", {"value": "delta-prime", "version": 3}, [], "exam-t4-001")

# Test 5 chain: A (base) -> D (derived, declares A). D2 is a post-revocation
# reliance attempt on A. U is unrelated. SNEAK copies A's output value but
# declares no dependence on A (the undeclared-dependence limit case).
REQ_T5_A = _req("obj-y", {"value": "base-1", "version": 1}, [], "exam-t5-a")
_A_ID = request_id_for(REQ_T5_A)
REQ_T5_D = _req("obj-z", {"value": "derived-1", "version": 1}, [_A_ID], "exam-t5-d")
REQ_T5_D2 = _req("obj-z", {"value": "derived-2", "version": 2}, [_A_ID], "exam-t5-d2")
REQ_T5_U = _req("obj-x", {"value": "unrelated", "version": 9}, [], "exam-t5-u")
REQ_T5_SNEAK = _req("obj-z", {"value": "base-1", "version": 1}, [], "exam-t5-sneak")

# Test 6's gated write.
REQ_T6 = _req("obj-x", {"value": "gated", "version": 1}, [], "exam-t6-001")
BYPASS_VALUE = {"value": "bypassed", "version": 66}


def all_requests():
    return {
        "REQ_T1": copy.deepcopy(REQ_T1),
        "REQ_T2": copy.deepcopy(REQ_T2),
        "REQ_T2_MUTATED": copy.deepcopy(REQ_T2_MUTATED),
        "REQ_T3": copy.deepcopy(REQ_T3),
        "REQ_T4": copy.deepcopy(REQ_T4),
        "REQ_T4_CONFLICT": copy.deepcopy(REQ_T4_CONFLICT),
        "REQ_T5_A": copy.deepcopy(REQ_T5_A),
        "REQ_T5_D": copy.deepcopy(REQ_T5_D),
        "REQ_T5_D2": copy.deepcopy(REQ_T5_D2),
        "REQ_T5_U": copy.deepcopy(REQ_T5_U),
        "REQ_T5_SNEAK": copy.deepcopy(REQ_T5_SNEAK),
        "REQ_T6": copy.deepcopy(REQ_T6),
    }
