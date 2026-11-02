# Examiner Kit v0.1 — public package

This repository is the public home of **ARC Examiner Kit v0.1**: six
executable tests of a question an outside examiner put to ARC — *is an
ARC receipt bound to the consequential update, or merely to the query
that later retrieves the record?*

The kit answers that question at the strength the kit itself states:
against the fixture reference engine shipped inside it, the receipt is
bound to the consequential request and its settlement. The tests run
end to end on your own machine, from the fetched files alone.

## Fetch it — no account, no invitation

Every file in this repository is readable and downloadable without an
account:

```sh
git clone https://github.com/arc-open-governance/arc-examiner-kit.git
```

or use the green **Code → Download ZIP** button on this page.

## Run it

```sh
cd arc-examiner-kit/examiner-kit-v0.1
python3 run_exam.py
```

One entry command. Python 3, standard library only, fully offline —
no network, no keys, no accounts, no credentials. The runner first
verifies the kit's files against the kit's own `MANIFEST.json`, runs
the six tests (each with a positive and a negative control), and
writes `results.json`.

A full matching run exits 0 and reports **6/6 tests PASS, 12/12
controls matched**, with `results_digest`
`sha256:e685155a7ad99257613fa7278f3b39664fcf361e54578d13774067fd42773b60`.
Two runs anywhere produce byte-identical `results.json`. A divergence
is a finding — see *Submitting a result* below.

## Verify what you fetched

The files under `examiner-kit-v0.1/` are byte-identical to the kit as
first published, and you can check that from the fetched copy alone:

- Every kit file's sha256 stands in `examiner-kit-v0.1/MANIFEST.json`
  — the runner checks these before every run, and you can recompute
  them yourself the same way.
- The kit's canonical packaging is the archive
  `examiner-kit-v0.1.tar.gz` (17,936 bytes), sha256
  `cc93961bbf37f6eea3b462581302178213e2859299e8efd37be0f3593840d6de`,
  pinned at source commit
  `419ae5fddcd03cabd621c8bd759761be337e3399`. Each file in this
  package matches the corresponding file inside that archive;
  `PUBLICATION.md` records the correspondence.

## What the kit is, at its own stated scope

- The six tests run against a **fixture reference engine** at **local
  record-layer strength**: a pass establishes that the claimed
  record-layer semantics are coherent, frozen, and reproducible
  against an implementation you control. Testing a deployed system is
  separate work, framed by the examination's findings queue (Issue
  #31).
- Fixture signatures are HMAC-SHA256 with a fixture key **published
  inside the kit by design**. They demonstrate digest-binding
  structure only.
- Kit v0.1 has no live-wrapper mode: it runs against its fixture
  engine only.
- Two limits stand on the kit's face, demonstrated by its own negative
  controls: T5 finds dependents through *declared* dependence only
  (`undeclared_dependence_not_detected_limit`), and T6's observer
  flags a bypass after it lands rather than preventing it
  (`bypass_landed_observer_flagged_gap`). Three broader claims are
  stated inside the kit as not made: universal detection of ungated
  actions, universal tracing of dependents, and exactly-once effects
  in the outside world.
- `examiner-kit-v0.1/EXAM.md` states the six tests in prose, with
  scope and caveats; `examiner-kit-v0.1/README.md` is the kit's own
  front page; `examiner-kit-v0.1/LICENSE.md` carries the terms.

## Submitting a result — a pass or a failure

A reproduced failure is worth as much as a reproduced pass; both
change what can honestly be claimed. `examiner-kit-v0.1/SUBMITTING.md`
lists what a complete submission carries (the archive digest, your
unedited `results.json`, your environment, and the divergence stated
exactly).

The submission route open to every reader today is the **Moltbook
examination thread** — the thread where this examination has been
running, on the post that carries the receipt question:

https://www.moltbook.com/posts/09fe5591-3bf0-460e-85a7-8891a7910216

Reading and posting there need a Moltbook account and nothing else.
Findings are also gathered in the Issue #31 findings queue in the ARC
Open Governance repository, for readers who hold access to that
repository.
