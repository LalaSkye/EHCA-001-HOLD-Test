#!/usr/bin/env python3
"""EHCA-001 v0.6 — scoped HOLD with once-only nonce and controllable concurrent race.
Specimen-scoped. Decision driven by current standing, scope match, and executor mode.
v0.1–v0.5 left unchanged.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

FIXTURE_VERSION = "EHCA-001-v0.6"
LINEARISATION = "check-standing-then-mutate"
FROZEN_TIMESTAMP = "2026-10-27T12:00:00Z"


def _body_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _scope_digest(action: str, object_id: str) -> str:
    return hashlib.sha256(f"{action}|{object_id}".encode()).hexdigest()


@dataclass
class Receipt:
    fixture: str
    version: str
    actor: str
    scoped_authority: str
    action: str
    object_id: str
    hold_id: Optional[str]
    hold_issued_at: Optional[str]
    hold_scope: Optional[str]
    hold_nonce: Optional[str]
    hold_consumed: bool
    hold_provenance: str
    enforcement_boundary: str
    current_standing_checked: bool
    scope_matched: bool
    executor_mode: str
    intervening_hold: bool
    atomic: bool
    concurrent_race: bool
    race_winner: str
    outcome: str
    final_state: str
    bypass_or_failure: str
    human_action_observed: str
    technical_enforcement_observed: str
    consequence_observed: str
    causal_attribution: str
    uncertainty: str
    linearisation_point: str
    timestamp: str
    body_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("body_hash")
        d["body_hash"] = _body_hash(d)
        return d


class Simulator:
    def __init__(self):
        self.state = "IDLE"
        self.committed = False
        self.hold_active = False
        self.hold_id: Optional[str] = None
        self.hold_time: Optional[str] = None
        self.hold_scope: Optional[str] = None
        self.hold_nonce: Optional[str] = None
        self.hold_consumed = False
        self._lock = threading.Lock()
        self._hold_ready = threading.Event()
        self._check_started = threading.Event()

    def issue_hold(self, hold_id: str, actor: str, issued_at: str, action: str, object_id: str, nonce: str) -> bool:
        if hold_id and actor and nonce:
            with self._lock:
                if self.hold_consumed:
                    return False
                self.hold_active = True
                self.hold_id = hold_id
                self.hold_time = issued_at
                self.hold_scope = _scope_digest(action, object_id)
                self.hold_nonce = nonce
            return True
        return False

    def attempt_commit(
        self,
        action: str,
        object_id: str,
        actor: str,
        executor_mode: str,
        intervening_hold: bool = False,
        atomic: bool = True,
        concurrent_race: bool = False,
        race_winner: str = "none",
    ) -> Receipt:
        scope = _scope_digest(action, object_id)
        if self.committed:
            outcome = "ALREADY_COMMITTED"
            final_state = "COMMITTED_HISTORICAL"
            enforcement = "LATE"
            bypass = "NONE"
            checked = False
            scope_matched = False
            causal = "UNRESOLVED"
            uncertainty = "REMEDY_FOR_HUMAN_ASSESSMENT"
        elif executor_mode == "enforce":
            checked = True
            with self._lock:
                observed_hold = self.hold_active and not self.hold_consumed
                observed_scope = self.hold_scope
            scope_matched = observed_hold and observed_scope == scope
            if concurrent_race and race_winner == "hold":
                # Fixture controls the interleave: HOLD arrives and is observed
                self.issue_hold("HOLD-CONCURRENT", actor, FROZEN_TIMESTAMP, action, object_id, "nonce-race")
                with self._lock:
                    observed_hold = self.hold_active and not self.hold_consumed
                    observed_scope = self.hold_scope
                scope_matched = observed_hold and observed_scope == scope
            elif concurrent_race and race_winner == "commit":
                # Fixture controls the interleave: check completes before HOLD
                pass
            if not atomic and intervening_hold and not concurrent_race:
                self.issue_hold("HOLD-RACE", actor, FROZEN_TIMESTAMP, action, object_id, "nonce-seq")
            if scope_matched:
                outcome = "REFUSED"
                final_state = "UNCHANGED"
                enforcement = "ENFORCED"
                bypass = "NONE"
                causal = "ESTABLISHED"
                uncertainty = "NONE"
                self.state = "REFUSED"
                with self._lock:
                    self.hold_consumed = True
            elif not atomic and intervening_hold and self.hold_active and self.hold_scope == scope and not concurrent_race:
                outcome = "COMMITTED"
                final_state = "MUTATED"
                enforcement = "RACE_LOST"
                bypass = "NON_ATOMIC_WINDOW"
                causal = "PARTIAL"
                uncertainty = "CHECK_THEN_MUTATE_NOT_ATOMIC"
                self.committed = True
                self.state = "COMMITTED"
            else:
                outcome = "COMMITTED"
                final_state = "MUTATED"
                if concurrent_race and race_winner == "commit":
                    enforcement = "CONCURRENT_RACE_COMMIT_WON"
                    bypass = "CONCURRENT_WINDOW"
                    causal = "PARTIAL"
                    uncertainty = "HOLD_ARRIVED_AFTER_CHECK"
                else:
                    enforcement = "NO_HOLD_PRESENT" if not observed_hold else "SCOPE_MISMATCH"
                    bypass = "NONE" if not observed_hold else "HOLD_SCOPE_MISMATCH"
                    causal = "ESTABLISHED"
                    uncertainty = "NONE"
                self.committed = True
                self.state = "COMMITTED"
        elif executor_mode == "skip":
            checked = False
            scope_matched = False
            outcome = "COMMITTED"
            final_state = "MUTATED"
            enforcement = "ACKNOWLEDGED_NOT_ENFORCED"
            bypass = "ENFORCEMENT_PATH_FAILURE"
            causal = "PARTIAL"
            uncertainty = "TECHNICAL_FAILURE_IDENTIFIED"
            self.committed = True
            self.state = "COMMITTED"
        elif executor_mode == "bypass":
            checked = False
            scope_matched = False
            outcome = "COMMITTED"
            final_state = "MUTATED"
            enforcement = "NOT_CHECKED"
            bypass = "ALTERNATIVE_PATH_BYPASS"
            causal = "PARTIAL"
            uncertainty = "DESIGN_DEFICIENCY_PRESERVED"
            self.committed = True
            self.state = "COMMITTED"
        else:
            raise ValueError(f"unknown executor_mode: {executor_mode}")

        human_action = "HOLD_ISSUED" if self.hold_active else "NONE"
        if executor_mode == "bypass" and self.hold_active:
            human_action = "HOLD_ISSUED_BUT_PATH_BYPASSED"
        if intervening_hold and not atomic:
            human_action = "INTERVENING_HOLD_IN_RACE_WINDOW"
        if concurrent_race:
            human_action = f"CONCURRENT_RACE_{race_winner.upper()}"

        return Receipt(
            fixture="ehca-001-simulator",
            version=FIXTURE_VERSION,
            actor=actor,
            scoped_authority="fixture-scoped",
            action=action,
            object_id=object_id,
            hold_id=self.hold_id,
            hold_issued_at=self.hold_time,
            hold_scope=self.hold_scope,
            hold_nonce=self.hold_nonce,
            hold_consumed=self.hold_consumed,
            hold_provenance="fixture-authenticated" if self.hold_active else "none",
            enforcement_boundary="simulated-commit-boundary",
            current_standing_checked=checked,
            scope_matched=scope_matched,
            executor_mode=executor_mode,
            intervening_hold=intervening_hold,
            atomic=atomic,
            concurrent_race=concurrent_race,
            race_winner=race_winner,
            outcome=outcome,
            final_state=final_state,
            bypass_or_failure=bypass,
            human_action_observed=human_action,
            technical_enforcement_observed=enforcement,
            consequence_observed=final_state,
            causal_attribution=causal,
            uncertainty=uncertainty,
            linearisation_point=LINEARISATION,
            timestamp=FROZEN_TIMESTAMP,
        )


def run_scenarios() -> Dict[str, Any]:
    action = "TRANSFER"
    object_id = "TX-001"
    actor = "officer-1"
    hold_id = "HOLD-2026-10-27-001"
    issued_at = FROZEN_TIMESTAMP

    results: Dict[str, Any] = {}

    s = Simulator()
    s.issue_hold(hold_id, actor, issued_at, action, object_id, "nonce-1")
    results["hold_active_enforce"] = s.attempt_commit(action, object_id, actor, "enforce").to_dict()

    s = Simulator()
    results["hold_inactive_enforce"] = s.attempt_commit(action, object_id, actor, "enforce").to_dict()

    s = Simulator()
    s.issue_hold(hold_id, actor, issued_at, action, object_id, "nonce-2")
    results["hold_active_skip"] = s.attempt_commit(action, object_id, actor, "skip").to_dict()

    s = Simulator()
    s.issue_hold(hold_id, actor, issued_at, action, object_id, "nonce-3")
    results["hold_active_bypass"] = s.attempt_commit(action, object_id, actor, "bypass").to_dict()

    s = Simulator()
    s.attempt_commit(action, object_id, actor, "enforce")
    s.issue_hold(hold_id, actor, issued_at, action, object_id, "nonce-4")
    results["late_hold"] = s.attempt_commit(action, object_id, actor, "enforce").to_dict()

    s = Simulator()
    results["non_atomic_race"] = s.attempt_commit(
        action, object_id, actor, "enforce", intervening_hold=True, atomic=False
    ).to_dict()

    s = Simulator()
    s.issue_hold(hold_id, actor, issued_at, action, "TX-OTHER", "nonce-5")
    results["scope_mismatch"] = s.attempt_commit(action, object_id, actor, "enforce").to_dict()

    # Concurrent race: fixture forces HOLD to win
    s = Simulator()
    results["concurrent_hold_wins"] = s.attempt_commit(
        action, object_id, actor, "enforce", concurrent_race=True, race_winner="hold"
    ).to_dict()

    # Concurrent race: fixture forces commit to win
    s = Simulator()
    results["concurrent_commit_wins"] = s.attempt_commit(
        action, object_id, actor, "enforce", concurrent_race=True, race_winner="commit"
    ).to_dict()

    # Once-only: issue, consume via enforce, attempt re-issue of same nonce fails
    s = Simulator()
    s.issue_hold(hold_id, actor, issued_at, action, object_id, "nonce-once")
    s.attempt_commit(action, object_id, actor, "enforce")
    reissued = s.issue_hold(hold_id, actor, issued_at, action, object_id, "nonce-once")
    results["nonce_replay_blocked"] = {
        "reissue_succeeded": reissued,
        "hold_consumed": s.hold_consumed,
    }

    return results


if __name__ == "__main__":
    receipts = run_scenarios()
    with open("receipts.json", "w") as f:
        json.dump(receipts, f, indent=2)
    for name, r in receipts.items():
        if isinstance(r, dict) and "outcome" in r:
            print(f"{name}: {r['outcome']} / {r['technical_enforcement_observed']}")
        else:
            print(f"{name}: {r}")
    print("receipts.json written")
