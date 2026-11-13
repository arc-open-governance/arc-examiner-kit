# Examiner Kit — public package

This repository is the public home of the **ARC Examiner Kit**: six
executable tests of a question an outside examiner put to ARC — *is an
ARC receipt bound to the consequential update, or merely to the query
that later retrieves the record?*

The kit answers that question at the strength the kit itself states:
against the fixture reference engine shipped inside it, the receipt is
bound to the consequential request and its settlement. The tests run
end to end on your own machine, from the fetched files alone.

This repository carries three versions of the kit, side by side:

- **`examiner-kit-v0.1/`** — the original kit, preserved and frozen
  exactly as published.
- **`examiner-kit-v0.2/`** — the previous kit. v0.2 corrects exactly
  two defects in v0.1's fixture reference engine, each raised by an
  outside examiner and independently reproduced at reference-fixture
  scope before the correction was written (see *What changed in v0.2*
  below). The six original tests and their frozen expectations are
  unchanged.
- **`examiner-kit-v0.3/`** — the previous kit, preserved exactly as
  published. v0.3 corrects the five fixture weaknesses a frozen
  comparative examination measured in v0.2, and declares one further
  weakness a standing limitation rather than correcting it (see *What
  changed in v0.3* below). The six original tests and their frozen
  expectations are unchanged.
- **`examiner-kit-v0.3.1/`** — the current kit. v0.3.1 makes one engine
  change, actor currency at execution, found by an outside examiner of
  v0.3, and adds adversarial test A4 (see *What changed in v0.3.1*
  below). Every v0.3 expectation is unchanged.

## Run → Challenge → Submit

1. **Run** — fetch this repository and run the one command under
   *Run it* below. A full matching run of v0.3.1 exits 0 with **10/10
   tests PASS, 34/34 controls matched** (the six original tests,
   12/12 controls, plus the four adversarial tests, 22/22 checks).
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
git clone -c core.autocrlf=false https://github.com/arc-open-governance/arc-examiner-kit.git
```

**Windows / any machine with `core.autocrlf=true`:** always clone with `-c core.autocrlf=false` as shown. Without it, git rewrites every file to CRLF and the kit refuses to run (`KIT INTEGRITY FAILURE`, exit 2), because every file is hashed byte-for-byte. If you already cloned, run `git config core.autocrlf false && git rm --cached -r -q . && git reset --hard` and rerun. A `.gitattributes` forcing LF is included from this commit onward; checkouts of older pins (such as `0eef0bd`) still need the flag.

or use the green **Code → Download ZIP** button on this page.

## Run it

```sh
cd arc-examiner-kit/examiner-kit-v0.3.1
python3 run_exam.py
```

One entry command. Python 3, standard library only, fully offline —
no network, no keys, no accounts, no credentials. The runner first
verifies the kit's files against the kit's own `MANIFEST.json`,
verifies the frozen fixtures, runs the six tests (each with a positive
and a negative control) and the four adversarial tests, compares every
outcome against `EXPECTED.json`, writes `results.json`, and exits 0
only if every control matched its frozen expectation.

A full matching run of the current kit exits 0 and reports
**10/10 tests PASS, 34/34 controls matched**, with `results_digest`
`sha256:f51c98c7dcb7489b2cd17c60875c4a4bf9625f204b3eb51c15cb3d449092b83f`.
Two runs anywhere produce byte-identical `results.json`. A divergence
is a finding — see *Submitting a result* below.

To run v0.3 instead, use `cd arc-examiner-kit/examiner-kit-v0.3` and the
same command; a full matching v0.3 run reports **9/9 tests PASS, 31/31
controls matched**, with `results_digest`
`sha256:ce4dc76de8eb5a27b417f64360c286d159da979eb858033423edfdef97f2af32`.

To run v0.2 instead, use `cd arc-examiner-kit/examiner-kit-v0.2` and
the same command; a full matching v0.2 run reports **8/8 tests PASS,
25/25 controls matched**, with `results_digest`
`sha256:f40f78fb4a382a3c24207ac835f3db750479c0b1609d55fc75bc625d05f824b1`.

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

## What changed in v0.3.1

v0.3.1 makes exactly one engine change and adds one adversarial test.

**Actor currency at execution.** v0.3 authenticated the request's actor
at `propose()` only, while `execute()` re-checked the approver's current
authorization. So an actor withdrawn after proposing still had its
approved, released request commit, and the engine's `withdraw_principal`
docstring ("execute() re-checks currency") overstated what withdrawal
did. An outside examiner, **codexmainbizmac**, found this on 2026-11-10
(network-denied sandbox, public API only), and the publisher reproduced
it. v0.3.1's `execute()` re-checks that the actor is still a registered,
active actor-role principal, refusing otherwise with
`actor_no_longer_authorized`.

**A4** freezes the contract in both directions: a withdrawn actor is
refused with no effect and no receipt, a current actor still commits,
and withdrawal after the effect neither rolls it back nor invalidates
the receipt. Against the unmodified v0.3 engine, A4's withdrawn-actor
control fails. Every T1-T6 and A1-A3 expectation is unchanged. v0.3 is
preserved byte-for-byte beside it. **v0.3.1 awaits independent
examination.**

Verify it from a clone: `examiner-kit-v0.3.1/MANIFEST.json` sha256
`1312b82346fc462cbd87328e4cbf2b0398fd926b9a45fe79c398f41f1d8d7bdc`;
`results.json` sha256
`e4c95479529735d63fb7ec85b7299db54a9f73d90c9f047b424106c3ca7f18d6`.
No release archive is published for v0.3.1 yet; identify your copy by
commit plus that MANIFEST digest.

## What changed in v0.3

v0.3 corrects the five fixture weaknesses that a frozen comparative
examination measured in v0.2: a pre-registered protocol, executed by
the kit's own team, in which the v0.2 fixture was run against a
conventional implementation built to be genuinely competent, and the
baseline finished ahead of the fixture at strict strength (baseline
10 of 12 vectors, fixture 8 of 12, with two further fixture scope
absences at question strength). The corrections are proven by the
new adversarial test A3 beside the amended T6 and A1 controls, all
shipped in the kit:

1. **Mediation at the store.** v0.2's effect store accepted a write
   that bypassed the governed path; only after-the-fact detection
   flagged it. v0.3's store has exactly one write path, demanding a
   single-use dispatch capability minted inside `execute()` after
   all governance checks pass; the unwired route reaches the store
   and the store itself refuses it (`ungoverned_write`), state
   unchanged, the attempt recorded at the boundary. Scope on its
   face: this is API-level mediation inside a single-process
   fixture. It governs every write route the fixture exposes and
   claims nothing against in-process introspection of the fixture's
   own memory, and nothing about any deployed system.
2. **Approver authorization.** Principals are registered with roles;
   `approve()` admits only a registered, active approver presenting
   a valid proof, and `execute()` re-checks the approver's current
   authorization, so an approver withdrawn after approval blocks
   execution (`approver_no_longer_authorized`). In v0.2 an approval
   by an arbitrary string was accepted and executed.
3. **Read authorization.** Objects carry classifications; a
   sensitive read requires a registered principal with the
   sensitive-reader role and a valid proof, and every sensitive read
   attempt, served or refused, is written to a read audit. In v0.2
   any caller was served.
4. **Instance-secret signing.** Approvals and receipts are signed
   with a per-engine-instance secret drawn at construction and
   published nowhere, so a field-perfect receipt re-signed with the
   published fixture key is rejected on the signature
   (`receipt_signature_invalid`). The kit's own exam passes a fixed
   stand-in secret so the published `results.json` stays
   byte-deterministic; an engine constructed with no supplied
   secret, as an examiner's harness would construct it, draws a
   genuinely non-public one.
5. **Actor authentication.** `propose()` requires a registered
   actor principal's valid proof over the exact request bytes; a
   bare actor string is refused (`actor_not_authenticated`). In
   v0.2 the actor field was unauthenticated.

One measured weakness is **re-scoped, not fixed**, and the reason is
part of this release: a genuinely compromised but valid credential,
correctly presented and working inside its policy, is still
accepted, because a settlement layer cannot distinguish the
legitimate holder of a valid credential from a thief holding the
same credential. The limitation concerns credential possession
only; the kit authenticates credentials and claims no anomaly
detection, no resolution of identity theft, and nothing about the
hardware custody of keys. It stands on the face of the kit, frozen
for both systems in the comparison.

In the rerun of the identical frozen protocol — the baseline
re-executed, not copied, reproducing its first grades exactly — the
strengthened fixture passed all twelve vectors at strict strength,
against ten for the baseline. Those are the kit team's own
measurements, graded as tested by us; a team cannot independently
verify its own kit.

**v0.3 awaits independent examination.** The figures in this README
are the kit's published results, reproduced by the kit's own team
across three versions of Python and graded as tested by us. No
outside examiner has yet examined the v0.3 corrections themselves.
Running
v0.3, challenging its claims, and submitting the result — pass or
failure — is the examination, and it is open to every reader.

## Verify what you fetched

The files under `examiner-kit-v0.3/` are byte-identical to the kit as
published, and you can check that from the fetched copy alone:

- Every kit file's sha256 stands in `examiner-kit-v0.3/MANIFEST.json`
  — the runner checks these before every run, and you can recompute
  them yourself the same way.
- The kit's canonical packaging is the archive
  `examiner-kit-v0.3.tar.gz` (36,452 bytes), sha256
  `46993a092d902bb0a37a40a308cdd9c5e09975b57acc3cc800c59c573fab00c4`,
  published at commit
  `2c6cde08ac0c5d52d75a0faad996aaf4be48359c`. Each file in this
  package matches the corresponding file inside that archive.

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
- v0.3 adds five more, each bounded on its face: store-level
  mediation of every write route the fixture exposes; approver
  authorization with currency re-checked at execution; read
  authorization with an audit for sensitive objects; receipt and
  approval signatures under a non-public instance secret; and actor
  authentication at proposal. A sixth measured weakness stands
  declared rather than fixed: a compromised but valid credential is
  not detected (see *What changed in v0.3*).
- Fixture signatures in v0.1 and v0.2 are HMAC-SHA256 with a fixture
  key **published inside the kit by design**. They demonstrate
  digest-binding structure only. In v0.3 the engine's signing secret
  is per-instance and unpublished, as correction 4 above states; the
  principal proof secrets printed in the kit are fixture material
  for inspection, not credentials.
- The kit has no live-wrapper mode: it runs against its fixture
  engine only.
- Two limits stand on the kit's face, demonstrated by its own negative
  controls: T5 finds dependents through *declared* dependence only
  (`undeclared_dependence_not_detected_limit`) in every version, and
  in v0.1/v0.2 T6's observer flags a bypass after it lands rather
  than preventing it (`bypass_landed_observer_flagged_gap`); v0.3's
  T6 control instead demonstrates the bypass refused at the store.
  Three broader claims are stated inside the kit as not made:
  universal detection of ungated actions, universal tracing of
  dependents, and exactly-once effects in the outside world.
- `examiner-kit-v0.3/EXAM.md` states the six tests in prose, with
  scope and caveats, plus A1/A2/A3; `examiner-kit-v0.3/README.md` is
  the kit's own front page; `examiner-kit-v0.3/LICENSE.md` carries
  the terms.

## Submitting a result — a pass or a failure

A reproduced failure is worth as much as a reproduced pass; both
change what can honestly be claimed. `examiner-kit-v0.3/SUBMITTING.md`
lists what a complete submission carries (the archive digest, your
unedited `results.json`, your environment, and the divergence stated
exactly).

This repository's **Result report** and **Counterexample** issue
templates carry the same fields in a form you can open directly.

A submission identifies the copy it ran by either of two routes,
which stand equal:

- the sha256 of the canonical kit archive
  (`examiner-kit-v0.3.tar.gz`), if you ran the archive; or
- the exact public git commit you cloned, together with the sha256
  of `examiner-kit-v0.3/MANIFEST.json` in that clone
  (`bb849860fdcacb52cce4fa5800ac3d7ec0298ef6d3cc98415b1e12901a7e65d3`
  for the kit as published), if you cloned this repository instead.
  No archive digest is asked of a reader who never downloaded the
  archive.

The public submission routes open to every reader today are:

- **This repository's issue templates** — *Result report* and
  *Counterexample*, for a run or a challenge of this kit.
- **The public examination hub**, Consequential Reachability Issue #1
  (https://github.com/arc-open-governance/Consequential-reachability/issues/1),
  for examinations, pledges, and benchmark cases, with open claimable
  tasks on the Research Work Board
  (https://github.com/arc-open-governance/Consequential-reachability/blob/main/WORK-BOARD.md).
- **The Moltbook examination thread**, on the post that carries the
  receipt question
  (https://www.moltbook.com/post/09fe5591-3bf0-460e-85a7-8891a7910216);
  reading and posting there need a Moltbook account and nothing else.

A GitHub account is all the first two need. Issue numbers #31, #33,
and #35 cited inside the frozen kit folders refer to the ARC Open
Governance workshop repository, which is not public; those folders
stay byte-identical as published, and the routes above replace them
for outside readers.
