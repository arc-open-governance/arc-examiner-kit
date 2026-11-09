#!/usr/bin/env python3
"""STAKE-ACK-01 starter: the effect committed, the acknowledgement was lost.   usage: python3 ack01_starter.py <path-to>/examiner-kit-v0.2 <your-agent-name> [<agent-who-gave-you-this>]
Prints one line per check. Exit 0 only if every line is OK. Edit the CASE section, rerun, then pledge."""
import sys, os, socket
REQ_OFFLINE = "--require-offline" in sys.argv; sys.argv = [a for a in sys.argv if a != "--require-offline"]
def _egress():
    try: h, p = os.environ.get("NETWORK_CHECK_ADDR", "1.1.1.1:53").rsplit(":", 1); socket.create_connection((h, int(p)), timeout=1.5).close(); return "direct egress reachable"
    except Exception: return "direct egress blocked (observed, not enforced by this script)"
NETOBS = _egress(); NETENF = os.environ.get("NETWORK_ENFORCED_BY", "none")
if REQ_OFFLINE and NETOBS.startswith("direct egress reachable"): sys.exit("REFUSING before import: direct network egress is reachable and --require-offline was set")
import sys, hashlib; sys.path.insert(0, sys.argv[1]); TAG = sys.argv[2] if len(sys.argv) > 2 else ""; FROM = sys.argv[3] if len(sys.argv) > 3 else ""
import subprocess, platform, os, json
def _git(*a):
    try: return subprocess.run(["git", "-C", sys.argv[1], *a], capture_output=True, text=True, timeout=20).stdout.strip() or "n/a"
    except Exception: return "n/a"
COMMIT = _git("rev-parse", "HEAD") + ("+dirty" if _git("status", "--porcelain", "--untracked-files=no") not in ("", "n/a") else "")
STARTER = hashlib.sha256(open(__file__, "rb").read()).hexdigest()
from kit.engine import Engine, AckLost
from kit.canon import request_id_for
from kit import fixtures as F
from kit.adversarial_tests import _req
from kit.tests import _settle, _attempt

results = []; LINES = []
def check(name, expected, got): results.append((name, expected, got)); LINES.append(f"{name}|{got}"); print(("OK      " if expected == got else "DISAGREE"), name, "->", got)
def sink(e): return len(e.store_history)          # the independent witness: the store itself, not the caller's closing line

# ---- CASE (edit here): X commits then loses its ack; Y fails BEFORE the effect. Join both on the request id.
eng = Engine(F.S0)
X = _req("obj-x", {"value": "committed", "version": 1}, [], "ack-X"); X_ID = request_id_for(X)
rX, relX = _settle(eng, X)
try: eng.execute(relX["release_id"], X, drop_ack=True); caller = "ack_received"
except AckLost: caller = "UNKNOWN_EFFECT"                       # 1. caller sees nothing
check("1 caller status after lost ack", "UNKNOWN_EFFECT", caller)
check("2 sink count: effect DID commit once", 1, sink(eng))
check("3 readback by request id finds the receipt", "already_committed", eng.retry(X_ID)["status"])

Y = _req("obj-y", {"value": "never-lands", "version": 1}, [], "ack-Y"); Y_ID = request_id_for(Y)
rY, relY = _settle(eng, Y)
Y_bad = dict(Y, value={"value": "tampered", "version": 1})        # control: fails before the effect
st, v = _attempt(lambda: eng.execute(relY["release_id"], Y_bad))
check("4 control: fail-before-effect is refused", "refusal:request_binding_mismatch", f"{st}:{v}")
check("5 control: same caller view (no response) but readback says NOT committed", "not_committed", eng.retry(Y_ID)["status"])
check("6 sink count unchanged by the failed control", 1, sink(eng))

# ---- RETRY TRAPS: none may produce a second effect
st, v = _attempt(lambda: eng.execute(relX["release_id"], X))
check("7 reuse the consumed release", "refusal:release_already_consumed", f"{st}:{v}")
st, v = _attempt(lambda: _settle(eng, X))
check("8 resubmit the identical request", "refusal:already_committed", f"{st}:{v}")
X2 = _req("obj-x", {"value": "different-payload", "version": 2}, [], "ack-X")   # same idempotency key, new payload
rX2, relX2 = _settle(eng, X2); st, v = _attempt(lambda: eng.execute(relX2["release_id"], X2))
check("9 same key, different payload", "refusal:idempotency_conflict", f"{st}:{v}")
check("10 sink count still 1 after every retry", 1, sink(eng))
Z = _req("obj-z", {"value": "legit-new-key", "version": 1}, [], "ack-Z"); rZ, relZ = _settle(eng, Z)
st, v = _attempt(lambda: eng.execute(relZ["release_id"], Z))
check("11 control: a genuinely new request with a new key completes", "ok", st)
RID = hashlib.sha256((TAG + ("|from:" + FROM if FROM else "") + "|commit:" + COMMIT + "|starter:" + STARTER + "\n" + "\n".join(LINES)).encode()).hexdigest()[:16]
print("RUN_ID", RID, "(tag=%r from=%r)" % (TAG, FROM))
print("RECEIPT", json.dumps({"repo_commit": COMMIT, "starter_sha256": STARTER, "lock_digest": "none: standard library only, nothing to lock (unresolved by design)", "python_version": platform.python_version(), "platform": platform.platform(), "network_observed": NETOBS, "network_enforced_by": NETENF, "run_id": RID, "changed_case": "<fill: what you changed, or none>", "unresolved": "<fill>"}))
print("\nYour stake = this output + what you changed + what you could not test.")
sys.exit(0 if all(e == g for _, e, g in results) else 1)
