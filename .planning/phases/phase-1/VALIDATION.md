# Phase 1 Validation Architecture

This document defines the verification strategy for Phase 1: Stabilization & Robust Tracking.

## Test Framework
- **Framework:** `pytest`
- **Location:** `src/tests/`
- **Config:** Default `pytest` behavior.

## Requirement Verification Map

| ID | Requirement | Verification Method | Command |
|----|-------------|---------------------|---------|
| STAB-01 | Atomic Updates | Integration (Grep) | `grep -E "wg\", \"set" src/modules/WireguardConfiguration.py` |
| STAB-02 | Persistence | Integration (Grep) | `grep -E "wg-quick\", \"save" src/modules/WireguardConfiguration.py` |
| STAB-03 | Thread-Safety | Unit Test (Concurrency) | `pytest src/tests/test_stab_track.py::test_cli_locking` |
| STAB-04 | Graceful Shutdown | Unit Test (Atexit) | `pytest src/tests/test_stab_track.py::test_graceful_shutdown` |
| TRACK-01 | Batch Collection | Integration (Grep) | `grep "show\", self.Name, \"dump" src/modules/WireguardConfiguration.py` |
| TRACK-02 | Raw Byte Storage | Unit Test (Database) | `pytest src/tests/test_stab_track.py::test_biginteger_storage` |
| TRACK-03 | Delta Pattern | Unit Test (Logic) | `pytest src/tests/test_delta_pattern.py` |
| TRACK-04 | Separate Totals | Unit Test (Logic) | `pytest src/tests/test_stab_track.py::test_separate_totals` |

## Automated Test Suites

### 1. Delta Pattern (`src/tests/test_delta_pattern.py`)
Verifies the core mathematical logic for tracking bytes across resets.
**Command:** `pytest src/tests/test_delta_pattern.py`

### 2. Stabilization & Tracking Integration (`src/tests/test_stab_track.py`)
Verifies database interaction, thread locking, and command wrapping.
**Command:** `pytest src/tests/test_stab_track.py`

## Manual Verification (Fallbacks)
If automated tests fail due to missing WireGuard installation in the CI/build environment:
1. Verify code patterns via `grep`.
2. Check database schema manually using `sqlite3`:
   ```bash
   sqlite3 wgdashboard.db ".schema <config_name>"
   ```
   Verify `total_sent`, `total_receive` are `INTEGER`.
