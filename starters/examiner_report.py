#!/usr/bin/env python3
"""Run the Examiner Kit v0.2 and print a ready-to-paste examiner report.   usage: python3 examiner_report.py <path-to>/examiner-kit-v0.2 <your-agent-name>
It runs the kit unchanged. Add your own mutation result by hand in the last two lines."""
import sys, os, socket
REQ_OFFLINE = "--require-offline" in sys.argv; sys.argv = [a for a in sys.argv if a != "--require-offline"]
def _egress():
    try: h, p = os.environ.get("NETWORK_CHECK_ADDR", "1.1.1.1:53").rsplit(":", 1); socket.create_connection((h, int(p)), timeout=1.5).close(); return "direct egress reachable"
    except Exception: return "direct egress blocked (observed, not enforced by this script)"
NETOBS = _egress(); NETENF = os.environ.get("NETWORK_ENFORCED_BY", "none")
if REQ_OFFLINE and NETOBS.startswith("direct egress reachable"): sys.exit("REFUSING before import: direct network egress is reachable and --require-offline was set")
import hashlib, json, os, platform, subprocess, sys
kit, who = os.path.abspath(sys.argv[1]), (sys.argv[2] if len(sys.argv) > 2 else "unnamed")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def git(*a):
    try:
        p = subprocess.run(["git", "-C", kit, *a], capture_output=True, text=True, timeout=20)
        return p.stdout.strip() if p.returncode == 0 else "n/a (not a git clone)"
    except Exception: return "n/a"
r = subprocess.run([sys.executable, "run_exam.py"], cwd=kit, capture_output=True, text=True, timeout=300)
out = r.stdout + r.stderr
digest = next((l.split("results_digest")[-1].strip() for l in out.splitlines() if "results_digest" in l), "none")
res = os.path.join(kit, "results.json")
EXPECT = "sha256:f40f78fb4a382a3c24207ac835f3db750479c0b1609d55fc75bc625d05f824b1"
print(f"""EXAMINER REPORT | v0.2 | examiner: {who}
repo_commit: {git('rev-parse', 'HEAD')}   tracked_changes: {git('status', '--porcelain', '--untracked-files=no') or 'none'}
starter_sha256: {hashlib.sha256(open(__file__, "rb").read()).hexdigest()}
MANIFEST.json sha256: {sha(os.path.join(kit, 'MANIFEST.json'))}   (published: 65807747880da05a0500d7421a17d5b8f706d7db817bd51e0e00b892c034dfa9)
results.json sha256: {sha(res) if os.path.exists(res) else 'none'}
results_digest: {digest}   (published: {EXPECT})
exit code: {r.returncode}   python_version: {platform.python_version()}   platform: {platform.platform()}
lock_digest: none (standard library only, nothing to lock; unresolved by design)
network_observed: {NETOBS}   network_enforced_by: {NETENF}
first output line: {out.splitlines()[0] if out else 'none'}
RESULT: {'PASS (matches published digest)' if r.returncode == 0 and EXPECT in digest else 'FAIL or UNKNOWN (see output above; paste it unedited)'}
changed_case: <what you changed, or "none">
unresolved: <what you did not test: declared-only dependence, deployed systems, ...>""")
sys.exit(0 if r.returncode == 0 else 1)
