#!/usr/bin/env python3
"""ARC Examiner Kit v0.2 — single entry command.

    python3 run_exam.py

Run from the kit root. The runner:
  1. verifies every kit file against MANIFEST.json (sha256, exact file set);
  2. verifies the frozen fixtures against fixtures/fixture-manifest.json;
  3. runs Issue #35's six tests, each with a positive and a negative control,
     and the two v0.2 adversarial tests (A1, A2) — the regression proof for
     the corrections described in README.md, "What changed in v0.2";
  4. compares every control's observed outcome code against EXPECTED.json;
  5. writes results.json (machine-readable, deterministic) into the kit root
     and prints a summary to stdout.

Exit codes: 0 = every control matched its frozen expectation;
1 = a test/control diverged; 2 = kit integrity failure (do not trust a run
whose own files do not match the manifest — re-extract from the archive).

No network, no credentials, no private keys, no writes outside the kit root.
Python 3 standard library only.
"""

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from kit.canon import digest_of, sha256_hex  # noqa: E402
from kit import fixtures as F  # noqa: E402
from kit.tests import ALL_TESTS  # noqa: E402
from kit.adversarial_tests import ALL_ADVERSARIAL  # noqa: E402

KIT_NAME = "arc-examiner-kit"
KIT_VERSION = "0.2.0"
EXCLUDED_FROM_MANIFEST = {"MANIFEST.json", "results.json"}


def _walk_files():
    out = []
    for p in sorted(ROOT.rglob("*")):
        if p.is_file():
            rel = p.relative_to(ROOT).as_posix()
            if "__pycache__" in rel.split("/"):
                continue
            out.append(rel)
    return out


def verify_manifest():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    listed = manifest["files"]
    actual = [r for r in _walk_files() if r not in EXCLUDED_FROM_MANIFEST]
    problems = []
    if sorted(listed) != sorted(actual):
        problems.append(
            f"file set mismatch: manifest={sorted(listed)} actual={sorted(actual)}"
        )
    for rel, expected in listed.items():
        p = ROOT / rel
        if p.exists():
            got = "sha256:" + sha256_hex(p.read_bytes())
            if got != expected:
                problems.append(f"digest mismatch: {rel}")
    return manifest, problems


def verify_fixtures():
    fm = json.loads((ROOT / "fixtures" / "fixture-manifest.json").read_text(encoding="utf-8"))
    problems = []
    if digest_of(F.S0) != fm["initial_state_digest"]:
        problems.append("S0 digest mismatch")
    reqs = F.all_requests()
    for name, expected in fm["request_digests"].items():
        if digest_of(reqs[name]) != expected:
            problems.append(f"request digest mismatch: {name}")
    if digest_of(F.BYPASS_VALUE) != fm["bypass_value_digest"]:
        problems.append("bypass value digest mismatch")
    return problems


def main():
    manifest, problems = verify_manifest()
    if problems:
        print("KIT INTEGRITY FAILURE — refusing to run:", file=sys.stderr)
        for p in problems:
            print("  -", p, file=sys.stderr)
        return 2
    fproblems = verify_fixtures()
    if fproblems:
        print("FIXTURE INTEGRITY FAILURE — refusing to run:", file=sys.stderr)
        for p in fproblems:
            print("  -", p, file=sys.stderr)
        return 2

    expected = json.loads((ROOT / "EXPECTED.json").read_text(encoding="utf-8"))
    results = {
        "kit": KIT_NAME,
        "version": KIT_VERSION,
        "manifest_digest": digest_of(manifest["files"]),
        "tests": [],
    }
    all_pass = True
    for fn in ALL_TESTS:
        t = fn()
        exp = expected["tests"].get(t["test_id"], {})
        for c in t["controls"]:
            want = exp.get("controls", {}).get(c["name"])
            c["expected_frozen_in_expected_json"] = want
            if want != c["expected_code"]:
                c["pass"] = False
                c["frozen_expectation_mismatch"] = True
            if not c["pass"]:
                all_pass = False
        t["verdict"] = "PASS" if all(c["pass"] for c in t["controls"]) else "FAIL"
        results["tests"].append(t)
    results["adversarial_tests"] = []
    for fn in ALL_ADVERSARIAL:
        t = fn()
        exp = expected["adversarial_tests"].get(t["test_id"], {})
        for c in t["controls"]:
            want = exp.get("controls", {}).get(c["name"])
            c["expected_frozen_in_expected_json"] = want
            if want != c["expected_code"]:
                c["pass"] = False
                c["frozen_expectation_mismatch"] = True
            if not c["pass"]:
                all_pass = False
        t["verdict"] = "PASS" if all(c["pass"] for c in t["controls"]) else "FAIL"
        results["adversarial_tests"].append(t)
    results["summary"] = {
        "tests": len(results["tests"]),
        "tests_passed": sum(1 for t in results["tests"] if t["verdict"] == "PASS"),
        "controls": sum(len(t["controls"]) for t in results["tests"]),
        "controls_passed": sum(
            1 for t in results["tests"] for c in t["controls"] if c["pass"]
        ),
        "adversarial_tests": len(results["adversarial_tests"]),
        "adversarial_tests_passed": sum(1 for t in results["adversarial_tests"] if t["verdict"] == "PASS"),
        "adversarial_controls": sum(len(t["controls"]) for t in results["adversarial_tests"]),
        "adversarial_controls_passed": sum(
            1 for t in results["adversarial_tests"] for c in t["controls"] if c["pass"]
        ),
        "all_pass": all_pass,
    }
    results["results_digest"] = digest_of(
        {k: v for k, v in results.items() if k != "results_digest"}
    )
    (ROOT / "results.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for t in results["tests"]:
        print(f"{t['test_id']} {t['title']}: {t['verdict']}")
        for c in t["controls"]:
            mark = "ok " if c["pass"] else "FAIL"
            print(f"   [{mark}] {c['kind']:8s} {c['name']}: {c['observed_code']}")
    for t in results["adversarial_tests"]:
        print(f"{t['test_id']} {t['title']}: {t['verdict']}")
        for c in t["controls"]:
            mark = "ok " if c["pass"] else "FAIL"
            print(f"   [{mark}] {c['kind']:8s} {c['name']}: {c['observed_code']}")
    s = results["summary"]
    print(
        f"controls {s['controls_passed']}/{s['controls']} passed; "
        f"adversarial controls {s['adversarial_controls_passed']}/{s['adversarial_controls']} passed; "
        f"results_digest {results['results_digest']}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
