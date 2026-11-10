"""Canonical serialization and digests for the ARC Examiner Kit.

Deterministic by construction: JSON with sorted keys and fixed separators,
UTF-8, no ambient timestamps or randomness anywhere in the kit. The same
inputs produce the same digests on any machine.
"""

import hashlib
import json


def canonical(obj) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_of(obj) -> str:
    """Digest of any JSON-able value, as 'sha256:<hex>'."""
    return "sha256:" + sha256_hex(canonical(obj))


def request_id_for(request: dict) -> str:
    return "req-" + sha256_hex(canonical(request))[:16]
