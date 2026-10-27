# EHCA-001 — The HOLD Test

Fixture-scoped demonstrator of the difference between a human issuing a HOLD and a downstream execution path enforcing it.

## Research attribution

Abraham Chachamovits, “The Human Was Held Accountable. What Could They Actually Control?”, 27 October 2026.

https://www.linkedin.com/pulse/human-held-accountable-what-could-actually-control-chachamovits-akece

The article motivates the accountability question examined by this specimen. Abraham Chachamovits did not design, approve, or verify EHCA-001.

## Demonstrated scope

The specimen compares an enforcing execution path with paths that acknowledge or bypass HOLD.

It demonstrates fixture-scoped, state-dependent outcomes for a controlled set of executor modes. It does not establish complete execution-path coverage or production enforcement.

## Accountability boundary

Technical evidence of an acknowledged, enforced, or bypassed HOLD does not independently establish legal negligence, organisational responsibility, or human fault.

## Concurrency limitation

The race is fixture-controlled and sequentially scheduled. No free-running thread race, distributed atomicity, or real-world non-bypassability is demonstrated.

## Purpose

Same proposed action reaches different outcomes when HOLD state changes.
HOLD is bound to a specific action|object scope digest and a once-only nonce.
Consumed HOLD cannot be reissued with the same nonce.
Concurrent race outcomes are fixture-controlled for determinism.

## Executor modes

- enforce: checks standing and scope; refuses if HOLD active and scope matches; consumes nonce
- skip: acknowledges HOLD but does not honour it
- bypass: alternative path that never checks

## Scenarios

1. HOLD active + matching scope + enforce → REFUSED / UNCHANGED / consumed
2. HOLD inactive + enforce → COMMITTED / MUTATED
3. HOLD active + skip → COMMITTED / ACKNOWLEDGED_NOT_ENFORCED
4. HOLD active + bypass → COMMITTED / ALTERNATIVE_PATH_BYPASS
5. Commit first, then late HOLD → ALREADY_COMMITTED / LATE
6. Non-atomic race → COMMITTED / RACE_LOST
7. HOLD bound to different object → COMMITTED / SCOPE_MISMATCH
8. Concurrent race, HOLD wins → REFUSED / ENFORCED
9. Concurrent race, commit wins → COMMITTED / CONCURRENT_RACE_COMMIT_WON
10. Nonce reissue after consumption → blocked

## Linearisation

atomic=True: single observation of standing and scope then mutate/refuse.
atomic=False: observation, then intervening HOLD, then mutate based on earlier observation.
concurrent_race: fixture selects winner (hold or commit) for deterministic interleave.
Scope digest is SHA-256 of action|object. Nonce is once-only. No distributed atomicity claimed.

## Usage

```bash
python3 check.py
```

## Limitations

- Fixture trust model only
- Single-process simulation
- Concurrent race is fixture-controlled interleave, not free-running threads
- Body hash, scope digest, and nonce are fixture-internal
- No durable storage or external enforcement
- Coverage limited to controlled modes
- Causal labels are technical observations, not legal findings

## Licence

No licence is granted. The absence of a licence does not imply permission to reuse, modify, or redistribute. A licence decision is pending.

## Status

Specimen. Fixture-scoped. Not a production control.
