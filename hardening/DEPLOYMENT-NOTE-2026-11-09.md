# Examiner conformance CI — deployment note (2026-11-09)

This branch (`hardening/examiner-conformance-ci-20261109`, from `main` @
`ae7e983f7600d7e00d313621f66b8637a599652b`) was created to deploy the pinned
conformance workflow at `.github/workflows/examiner-conformance.yml`.

**State at this note:** the branch exists; the workflow file itself is NOT yet
on it. Writing it through this seat's GitHub integration returned
`403 Resource not accessible by integration` on both the git-trees route
(`push_files`) and the Contents route (`create_or_update_file`) — the same
error class the staging surface recorded earlier the same day. Branch
creation through the same integration succeeded. The remaining act is an
installation-permissions change (or a maintainer committing the file through
another route); the file's content is final and verified.

**The workflow file is ready and tested.** Before deployment it was executed
locally in full — the identical matrix it encodes (Python 3.10 / 3.12 / 3.13 ×
examiner-kit v0.1 + v0.2, two runs per cell):

- all 6 cells exit 0, `all_pass=true`;
- results byte-identical across duplicate runs (determinism holds);
- published results digests reproduced exactly —
  v0.1 `sha256:e685155a7ad99257613fa7278f3b39664fcf361e54578d13774067fd42773b60`,
  v0.2 `sha256:f40f78fb4a382a3c24207ac835f3db750479c0b1609d55fc75bc625d05f824b1`;
- tamper test: a modified kit refuses with exit 2 and the expected
  integrity-failure lines;
- every kit file verified against its `MANIFEST.json` before running
  (25 files, 0 mismatches).

Grade: **TESTED BY US** (same-team local execution). A hosted GitHub Actions
run remains unearned — the org Actions pool was exhausted on 2026-11-09 —
and **INDEPENDENTLY VERIFIED** remains unearned by design.

Source of record for the workflow content: arc-open-governance/
arc-open-governance, `operations/examination/2026-11-09/PUBLIC_EXAMINER_CI.yml`
(PR #205), with the deployment header substituted.
