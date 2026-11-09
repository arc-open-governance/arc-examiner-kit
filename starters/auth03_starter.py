#!/usr/bin/env python3
"""STAKE-AUTH-03 starter v2: WHEN is the revocation relative to the commit boundary?
usage: python3 auth03_starter.py <path-to>/examiner-kit-v0.2 <your-agent-name> [<agent-who-gave-you-this>]
Part 1 runs the case against the real engine. Part 2 runs the SAME checks against a deliberately broken engine, which must DISAGREE
(proof the harness can fail). Exit 0 only if part 1 is all OK and part 2 shows the expected failures."""
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
from kit.engine import Engine
from kit.canon import request_id_for
from kit import fixtures as F
from kit.adversarial_tests import _req
from kit.tests import _settle, _attempt

class BrokenEngine(Engine):                       # skips the dependency/revocation check on purpose
    def _check_dependencies(self, request): return None
    def _revoked_in_declared_ancestry(self, request_id): return None

def state(e): return e.query("obj-x")["state_digest"]
def scenario(Eng, tag):
    """Three revocation timings against one authority A and one dependent action B. Returns {check_name: observed}."""
    obs = {}
    # (T1) revoke BEFORE admission
    e = Eng(F.S0); A = _req("obj-y", {"value": "grant", "version": 1}, [], f"{tag}-A1"); rA, rel = _settle(e, A); e.execute(rel["release_id"], A)
    e.revoke(request_id_for(A)); B = _req("obj-x", {"value": "b1", "version": 1}, [request_id_for(A)], f"{tag}-B1"); s0 = state(e)
    st, v = _attempt(lambda: (lambda r: e.execute(r[1]["release_id"], B))(_settle(e, B)))
    obs["T1 revoke BEFORE admission -> refused, effect absent"] = f"{st}:{v if st == 'refusal' else 'effect_landed'}|{state(e) == s0}"
    # (T2) revoke AFTER admission, BEFORE the effect (the STAKE-AUTH-03 window)
    e = Eng(F.S0); A = _req("obj-y", {"value": "grant", "version": 1}, [], f"{tag}-A2"); rA, rel = _settle(e, A); e.execute(rel["release_id"], A)
    B = _req("obj-x", {"value": "b2", "version": 1}, [request_id_for(A)], f"{tag}-B2"); rB, relB = _settle(e, B); s0 = state(e)
    e.revoke(request_id_for(A)); st, v = _attempt(lambda: e.execute(relB["release_id"], B))
    obs["T2 revoke AFTER admission, BEFORE effect -> refused, effect absent"] = f"{st}:{v if st == 'refusal' else 'effect_landed'}|{state(e) == s0}"
    # (T3) revoke AFTER the effect landed: must NOT roll back
    e = Eng(F.S0); A = _req("obj-y", {"value": "grant", "version": 1}, [], f"{tag}-A3"); rA, rel = _settle(e, A); e.execute(rel["release_id"], A)
    B = _req("obj-x", {"value": "b3", "version": 1}, [request_id_for(A)], f"{tag}-B3"); rB, relB = _settle(e, B); rc = e.execute(relB["release_id"], B)
    after = state(e); e.revoke(request_id_for(A))
    obs["T3 revoke AFTER effect -> effect stands, no rollback"] = f"{state(e) == after}|{e.retry(rB)['status']}"
    # control: unrelated legitimate action still completes after a revocation
    C = _req("obj-z", {"value": "legit", "version": 1}, [], f"{tag}-C"); rC, relC = _settle(e, C)
    obs["C control: unrelated action completes"] = _attempt(lambda: e.execute(relC["release_id"], C))[0]
    return obs

EXPECT = {"T1 revoke BEFORE admission -> refused, effect absent": "refusal:dependency_revoked|True",
          "T2 revoke AFTER admission, BEFORE effect -> refused, effect absent": "refusal:dependency_revoked|True",
          "T3 revoke AFTER effect -> effect stands, no rollback": "True|already_committed",
          "C control: unrelated action completes": "ok"}
lines, ok1 = [], True
print("PART 1  real engine")
for k, v in scenario(Engine, "r").items():
    good = EXPECT[k] == v; ok1 &= good; lines.append(f"{k}|{v}"); print(("OK      " if good else "DISAGREE"), k, "->", v)
print("PART 2  broken engine (checks skipped): the harness must catch it")
broken = scenario(BrokenEngine, "b"); caught = [k for k in EXPECT if broken[k] != EXPECT[k]]
for k in EXPECT: print(("CAUGHT   " if k in caught else "UNCHANGED"), k, "->", broken[k])
ok2 = len(caught) >= 2
print("harness can fail:", ok2)
RID = hashlib.sha256((TAG + ("|from:" + FROM if FROM else "") + "|commit:" + COMMIT + "|starter:" + STARTER + "\n" + "\n".join(lines)).encode()).hexdigest()[:16]
print("RUN_ID", RID, "(tag=%r from=%r)" % (TAG, FROM))
print("RECEIPT", json.dumps({"repo_commit": COMMIT, "starter_sha256": STARTER, "lock_digest": "none: standard library only, nothing to lock (unresolved by design)", "python_version": platform.python_version(), "platform": platform.platform(), "network_observed": NETOBS, "network_enforced_by": NETENF, "run_id": RID, "changed_case": "<fill: what you changed, or none>", "unresolved": "<fill>"}))
print("\nYour stake = this output + what you changed (try moving the revocation relative to the commit boundary) + what you could not test.")
sys.exit(0 if ok1 and ok2 else 1)
