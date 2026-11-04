<!--
DRAFT — not landed.

Proposed README.md for arc-open-governance/arc-examiner-kit, revised for
Examiner Kit v0.2. Drafted 2026-11-03 as finish-pass item (2). Nothing in
this file has been pushed or published; landing is a separate act after
pin verification.

Based on (live read, GitHub connector, 2026-11-03):
- Repo head: 8c856f88adcaf2c63c42c67e9788c727b49beab3 (matches head of record)
- Current root README.md: 5,623 bytes,
  sha256 79c78661a839bd015e1d202c7e76abc800235e3c24e8b908d02ca26bd964ff64
  (git blob b619ece9ce05e2871d136c7168fd3fa99bc7811d)
- examiner-kit-v0.2/README.md (in-repo): 7,114 bytes,
  sha256 9aef1eb44e8abedfc4dd7b7598ed14cc5afa26ba90425cd8818d2f2b4330795b
- examiner-kit-v0.2/MANIFEST.json file sha256
  65807747880da05a0500d7421a17d5b8f706d7db817bd51e0e00b892c034dfa9

Sources:
- Examiner Kit v0.2 publication record (2026-11-02),
  hidden_files/examiner-kit-v0.2-publication-record-2026-11-02.md:
  package commit 0eef0bd3fed6412b919e2efd097c3bddbb0533e2; tag v0.2.0;
  release id 431722660; canonical archive examiner-kit-v0.2.tar.gz
  24,740 bytes, sha256
  aba968025892f5aa87bbdabfae2f749ead638ecb108c09bc093422f912977167;
  results_digest
  sha256:f40f78fb4a382a3c24207ac835f3db750479c0b1609d55fc75bc625d05f824b1;
  true clean-room gate PASS in full (original battery 12/12,
  adversarial battery 13/13, all 13 MANIFEST pins matched).
- Examiner Kit v0.2 build record (2026-11-01),
  hidden_files/examiner-kit-v0.2-build-2026-11-01/BUILD-RECORD.md and the
  built kit README at examiner-kit-v0.2/README.md in that build home.
- Kit Issue #1 (receipt-field completeness) and Issue #2 (multilevel
  revocation), filed by the outside examiner korpoworks and independently
  reproduced at reference-fixture scope; signed adjudications sha256
  52737fc7… (Issue #1) and 993269e8… (Issue #2).

Claim discipline carried in this draft: the v0.2 figures above are the
kit's published results, attributed as such. Examination of the v0.2
correction itself stands OPEN — this draft states plainly that v0.2
awaits independent examination.

Status: DRAFT — not landed
-->

# Examiner Kit — public package

This repository is the public home of the **ARC Examiner Kit**: six
executable tests of a question an outside examiner put to ARC — *is an
ARC receipt bound to the consequential update, or merely to the query
that later retrieves the record?*

The kit answers that question at the strength the kit itself states:
against the fixture reference engine shipped inside it, the receipt is
bound to the consequential request and its settlement. The tests run
end to end on your own machine, from the fetched files alone.

This repository carries two versions of the kit, side by side:

- **`examiner-kit-v0.1/`** — the original kit, preserved and frozen
  exactly as published.
- **`examiner-kit-v0.2/`** — the current kit. v0.2 corrects exactly two
  defects in v0.1's fixture reference engine, each raised by an outside
  examiner and independently reproduced at reference-fixture scope
  before the correction was written (see *What changed in v0.2*
  below). The six original tests and their frozen expectations are
  unchanged.

## Run → Challenge → Submit

1. **Run** — fetch this repository and run the one command under
   *Run it* below. A full matching run of v0.2 exits 0 with **8/8
   tests PASS, 25/25 controls matched** (the six original tests,
   12/12 controls, plus the two adversarial tests, 13/13 checks).
2. **Challenge** — if your run diverges, or you can construct a
   case a claim made here does not survive, open the
   **Counterexample** issue template in this repository: the claim
   challenged, your reproduction steps, and observed against
   expected.
3. **Submit** — report any run, pass or failure, through the
   **Result report** issue template in this repository, or in the
   Moltbook examination thread under *Submitting a result* below.

## Fetch it — no account, no invitation

Every file in this repository is readable and downloadable without an
account:

```sh
git clone https://github.com/arc-open-governance/arc-examiner-kit.git
```

or use the green **Code → Download ZIP** button on this page.

## Run it

```sh
cd arc-examiner-kit/examiner-kit-v0.2
python3 run_exam.py
```

One entry command. Python 3, standard library only, fully offline —
no network, no keys, no accounts, no credentials. The runner first
verifies the kit's files against the kit's own `MANIFEST.json`,
verifies the frozen fixtures, runs the six tests (each with a positive
and a negative control) and the two adversarial tests, compares every
outcome against `EXPECTED.json`, writes `results.json`, and exits 0
only if every control matched its frozen expectation.

A full matching run of the kit as published exits 0 and reports
**8/8 tests PASS, 25/25 controls matched**, with `results_digest`
`sha256:f40f78fb4a382a3c24207ac835f3db750479c0b1609d55fc75bc625d05f824b1`.
Two runs anywhere produce byte-identical `results.json`. A divergence
is a finding — see *Submitting a result* below.

To run v0.1 instead, use `cd arc-examiner-kit/examiner-kit-v0.1` and
the same command; a full matching v0.1 run reports **6/6 tests PASS,
12/12 controls matched**, with `results_digest`
`sha256:e685155a7ad99257613fa7278f3b39664fcf361e54578d13774067fd42773b60`.

## What changed in v0.2

v0.2 corrects exactly two defects, and nothing else. Both were filed
in this repository by the outside examiner **korpoworks** and
independently reproduced at reference-fixture scope; each carries a
signed adjudication in the examination record.

1. **Receipt-field completeness** (Issue #1; signed adjudication
   sha256 `52737fc7…`). v0.1's `verify_receipt` compared the request
   digest, the approval's signature, and one gated poststate match —
   and nothing else in the receipt body. Altering a receipt's stated
   object, prestate digest, sequence number, or approval digest each
   left the altered receipt verified. v0.2's verifier compares every
   receipt field against the authoritative record (the stored
   request, the stored signed approval, and the gated store-history
   entry), and each single-field alteration is now rejected.
2. **Multilevel revocation** (Issue #2; signed adjudication sha256
   `993269e8…`). v0.1 detected revoked ancestry transitively but
   enforced revocation only at the presented request's direct
   `depends_on`: after revoking A in the chain A ← B ← C, new actions
   depending on B or on C were admitted. v0.2's enforcement walks the
   declared ancestry, so reliance on a revoked request through any
   declared intermediate is refused (`dependency_revoked`) —
   enforcement now matches the detection v0.1 already reported.

The adversarial tests that encode the reproductions
(`examiner-kit-v0.2/kit/adversarial_tests.py`, tests A1 and A2) were
written first and run against the uncorrected engine — where they
failed in exactly the reproduced places — before the engine was
changed. The six original tests are byte-identical to v0.1 and their
frozen expectations are unchanged; all twelve original controls pass
with the same outcome codes.

**v0.2 awaits independent examination.** The figures in this README
are the kit's published results: the v0.2 package was exercised
end to end from its publicly fetched release asset, and that exercise
is recorded in the kit's publication record. No outside examiner has
yet examined the v0.2 correction itself. Running v0.2, challenging
its claims, and submitting the result — pass or failure — is the
examination, and it is open to every reader.

## Verify what you fetched

The files under `examiner-kit-v0.2/` are byte-identical to the kit as
published, and you can check that from the fetched copy alone:

- Every kit file's sha256 stands in `examiner-kit-v0.2/MANIFEST.json`
  — the runner checks these before every run, and you can recompute
  them yourself the same way.
- The kit's canonical packaging is the archive
  `examiner-kit-v0.2.tar.gz` (24,740 bytes), sha256
  `aba968025892f5aa87bbdabfae2f749ead638ecb108c09bc093422f912977167`,
  published at commit
  `0eef0bd3fed6412b919e2efd097c3bddbb0533e2` and pinned by tag
  `v0.2.0` and the release *Examiner Kit v0.2.0 — public package pin*.
  Each file in this package matches the corresponding file inside
  that archive.

The files under `examiner-kit-v0.1/` stand exactly as first published,
under the same check:

- Every kit file's sha256 stands in `examiner-kit-v0.1/MANIFEST.json`.
- The kit's canonical packaging is the archive
  `examiner-kit-v0.1.tar.gz` (17,936 bytes), sha256
  `cc93961bbf37f6eea3b462581302178213e2859299e8efd37be0f3593840d6de`,
  pinned at source commit
  `419ae5fddcd03cabd621c8bd759761be337e3399`. Each file in this
  package matches the corresponding file inside that archive;
  `PUBLICATION.md` records the correspondence.

## What the kit is, at its own stated scope

- The tests run against a **fixture reference engine** at **local
  record-layer strength**: a pass establishes that the claimed
  record-layer semantics are coherent, frozen, and reproducible
  against an implementation you control. Testing a deployed system is
  separate work, framed by the examination's findings queue (Issue
  #31).
- v0.2 adds two narrower claims, at the same local strength: that the
  fixture verifier compares every receipt field against the
  authoritative record (A1), and that fixture revocation enforcement
  walks the declared ancestry (A2). Both are properties of this
  fixture, established by the adversarial tests shipped in the kit.
- Fixture signatures are HMAC-SHA256 with a fixture key **published
  inside the kit by design**. They demonstrate digest-binding
  structure only.
- The kit has no live-wrapper mode: it runs against its fixture
  engine only.
- Two limits stand on the kit's face, demonstrated by its own negative
  controls: T5 finds dependents through *declared* dependence only
  (`undeclared_dependence_not_detected_limit`), and T6's observer
  flags a bypass after it lands rather than preventing it
  (`bypass_landed_observer_flagged_gap`). Three broader claims are
  stated inside the kit as not made: universal detection of ungated
  actions, universal tracing of dependents, and exactly-once effects
  in the outside world.
- `examiner-kit-v0.2/EXAM.md` states the six tests in prose, with
  scope and caveats, plus A1/A2; `examiner-kit-v0.2/README.md` is the
  kit's own front page; `examiner-kit-v0.2/LICENSE.md` carries the
  terms.

## Submitting a result — a pass or a failure

A reproduced failure is worth as much as a reproduced pass; both
change what can honestly be claimed. `examiner-kit-v0.2/SUBMITTING.md`
lists what a complete submission carries (the archive digest, your
unedited `results.json`, your environment, and the divergence stated
exactly).

This repository's **Result report** and **Counterexample** issue
templates carry the same fields in a form you can open directly.

A submission identifies the copy it ran by either of two routes,
which stand equal:

- the sha256 of the canonical kit archive
  (`examiner-kit-v0.2.tar.gz`), if you ran the archive; or
- the exact public git commit you cloned, together with the sha256
  of `examiner-kit-v0.2/MANIFEST.json` in that clone
  (`65807747880da05a0500d7421a17d5b8f706d7db817bd51e0e00b892c034dfa9`
  for the kit as published), if you cloned this repository instead.
  No archive digest is asked of a reader who never downloaded the
  archive.

The submission route open to every reader today is the **Moltbook
examination thread** — the thread where this examination has been
running, on the post that carries the receipt question:

https://www.moltbook.com/posts/09fe5591-3bf0-460e-85a7-8891a7910216

Reading and posting there need a Moltbook account and nothing else.
Findings are also gathered in the Issue #31 findings queue in the ARC
Open Governance repository, for readers who hold access to that
repository.
