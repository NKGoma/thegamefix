"""Seeded randomness: every sub-seed derives from the run seed plus a scope, never global state."""

import hashlib
import json
import random


def derive_seed(*scope: object) -> int:
    """Stable 31-bit seed from a JSON-serialisable scope, e.g. (run_seed, task_id, retry)."""
    canonical = json.dumps(list(scope), sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(canonical.encode()).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF


def rng_for(*scope: object) -> random.Random:
    return random.Random(derive_seed(*scope))
