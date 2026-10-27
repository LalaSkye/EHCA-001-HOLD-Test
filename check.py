#!/usr/bin/env python3
"""Acceptance check for EHCA-001 v0.6.
Scoped HOLD, once-only nonce, controllable concurrent race, body hash.
"""

import hashlib
import json
import subprocess
import sys


def _body_hash(payload: dict) -> str:
    body = {k: v for k, v in payload.items() if k != "body_hash"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


EXPECTED = {
    "hold_active_enforce": {
        "outcome": "REFUSED",
        "technical_enforcement_observed": "ENFORCED",
        "scope_matched": True,
        "hold_consumed": True,
    },
    "hold_inactive_enforce": {
        "outcome": "COMMITTED",
        "technical_enforcement_observed": "NO_HOLD_PRESENT",
    },
    "hold_active_skip": {
        "outcome": "COMMITTED",
        "technical_enforcement_observed": "ACKNOWLEDGED_NOT_ENFORCED",
    },
    "hold_active_bypass": {
        "outcome": "COMMITTED",
        "bypass_or_failure": "ALTERNATIVE_PATH_BYPASS",
    },
    "late_hold": {
        "outcome": "ALREADY_COMMITTED",
        "technical_enforcement_observed": "LATE",
    },
    "non_atomic_race": {
        "outcome": "COMMITTED",
        "technical_enforcement_observed": "RACE_LOST",
    },
    "scope_mismatch": {
        "outcome": "COMMITTED",
        "technical_enforcement_observed": "SCOPE_MISMATCH",
    },
    "concurrent_hold_wins": {
        "outcome": "REFUSED",
        "technical_enforcement_observed": "ENFORCED",
        "concurrent_race": True,
        "race_winner": "hold",
    },
    "concurrent_commit_wins": {
        "outcome": "COMMITTED",
        "technical_enforcement_observed": "CONCURRENT_RACE_COMMIT_WON",
        "concurrent_race": True,
        "race_winner": "commit",
    },
}


def main() -> int:
    result = subprocess.run([sys.executable, "simulator.py"], capture_output=True, text=True)
    if result.returncode != 0:
        print("FAIL: simulator exited non-zero")
        print(result.stderr)
        return 1
    with open("receipts.json") as f:
        receipts = json.load(f)
    for name, exp in EXPECTED.items():
        got = receipts[name]
        for k, v in exp.items():
            if got.get(k) != v:
                print(f"FAIL {name} field {k}: expected {v} got {got.get(k)}")
                return 1
        if "body_hash" in got and _body_hash(got) != got.get("body_hash"):
            print(f"FAIL {name}: body_hash mismatch")
            return 1
        print(f"PASS {name}")
    a = receipts["hold_active_enforce"]["outcome"]
    b = receipts["hold_inactive_enforce"]["outcome"]
    if a == b:
        print("FAIL negative control: enforce mode identical regardless of HOLD")
        return 1
    print("PASS negative control: HOLD state changes outcome under enforce mode")
    nr = receipts["nonce_replay_blocked"]
    if nr.get("reissue_succeeded") is not False or nr.get("hold_consumed") is not True:
        print(f"FAIL nonce replay: {nr}")
        return 1
    print("PASS nonce once-only: reissue blocked after consumption")
    result2 = subprocess.run([sys.executable, "simulator.py"], capture_output=True, text=True)
    if result2.returncode != 0:
        print("FAIL: second run non-zero")
        return 1
    with open("receipts.json") as f:
        receipts2 = json.load(f)
    if receipts != receipts2:
        print("FAIL: receipts not byte-stable")
        return 1
    print("PASS receipts byte-stable")
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
