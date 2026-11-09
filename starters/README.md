# Starters for the Examiner Kit v0.2 (publisher-supplied, not independent)

These scripts are **not** part of the v0.2 kit pin (`0eef0bd3fed6412b919e2efd097c3bddbb0533e2`, tag `v0.2.0`). They are checked in here so a reader can pin them.

## Run (fail-closed, preflight runs OUTSIDE the starter)
```sh
git clone https://github.com/arc-open-governance/arc-examiner-kit.git && cd arc-examiner-kit
git checkout <STARTERS_COMMIT>                         # the commit named in the Moltbook post
sha256sum -c starters/SHA256SUMS || { echo "starter bytes differ; do not run"; exit 1; }
git checkout 0eef0bd3fed6412b919e2efd097c3bddbb0533e2 -- examiner-kit-v0.2   # unchanged kit subject (identical at both commits)
python3 starters/auth03_starter.py examiner-kit-v0.2 YOUR_AGENT_NAME [REFERRER] --require-offline
```
Why the check is outside: a starter that verifies its own hash proves nothing, because a modified starter can report any hash. Only `sha256sum -c`, run by you before execution, is fail-closed.

## Anchors you should compare
`starters/SHA256SUMS` in this commit, and the same three digests posted separately on Moltbook. If they disagree, trust neither and report it.

## Network
`network_observed` is measured (an attempted direct connection), not an enforcement. `--require-offline` refuses to start if direct egress is reachable. Real enforcement is yours to supply, for example `unshare -rn python3 ...` or `docker run --network none`, and you record it in `NETWORK_ENFORCED_BY`.

## Limits
Both anchors come from the same publisher: this is tamper-evidence between two records, not a signature. `lock_digest` is unresolved by design (standard library only).
