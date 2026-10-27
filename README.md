# EHCA-001 v0.6 — Local Candidate Prototype
# Scoped HOLD with once-only nonce and controllable concurrent race.
# Specimen-scoped only. No production claims. No legal attribution.
# v0.1–v0.5 left unchanged.

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
cd artifacts/04-labs/ehca-001-v0.6
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
- Does not modify any existing repository or claim boundary

## Status
CANDIDATE / LOCAL / NOT ADMITTED / NOT A PUBLIC OBJECT
