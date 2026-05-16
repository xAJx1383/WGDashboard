# Phase 1: Stabilization & Robust Tracking - Research

**Researched:** 2025-05-16
**Domain:** Backend Overhaul / WireGuard Interface Management
**Confidence:** HIGH

## Summary

This research focuses on transitioning the WGDashboard backend from high-level, session-dropping `wg-quick` restarts to atomic, low-level `wg` CLI interactions. The goal is to achieve high-precision traffic tracking and thread-safe interface management. 

Key findings indicate that the current implementation converts raw bytes to GB (`float`) prematurely, causing precision loss. The "Delta Pattern" is partially implemented but uses floating-point math and doesn't explicitly handle all reset scenarios (e.g., interface deletion/recreation). 

**Primary recommendation:** Shift all traffic tracking to raw bytes using `BigInteger` (64-bit), implement a global thread lock for all WireGuard CLI interactions, and unify the schema/logic update to avoid broken intermediate states.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Atomic Peer Updates | API / Backend | — | Uses `wg set` to modify live interface state without restarts. |
| Traffic Collection | API / Backend | — | Uses `wg show dump` for batch retrieval of peer metrics. |
| Persistence (Conf) | API / Backend | — | Uses `wg-quick save` to sync live state back to `.conf` files. |
| Persistence (Stats) | Database | — | Stores cumulative and session totals in SQLite/PostgreSQL/MySQL. |
| Concurrency Control | API / Backend | — | Ensures serialized access to the `wg` CLI to prevent race conditions. |
| Data Integrity | Database | — | Uses `BigInteger` to store byte-perfect traffic metrics. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| WireGuard-tools | Latest | CLI Interaction | Official toolset (`wg`, `wg-quick`) for interface management. [VERIFIED: wg man pages] |
| SQLAlchemy | 2.0+ | Persistence | Database-agnostic ORM; supports `BigInteger` for raw byte storage. [VERIFIED: SQLAlchemy Docs] |
| psutil | Latest | System Monitoring | Used for real-time interface throughput monitoring. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| threading | Built-in | Concurrency | Used for background tracking threads and CLI locking. |
| atexit | Built-in | Cleanup | Used for graceful shutdown data flushing. |

## Architecture Patterns

### Recommended Project Structure
```
src/
├── modules/
│   ├── WireguardConfiguration.py  # Interface-level logic & CLI wrapping
│   ├── Peer.py                    # Peer-level state & traffic calculations
│   └── DashboardConfig.py         # Global settings & Database initialization
├── tests/
│   ├── test_delta_pattern.py      # Unit tests for tracking logic
│   └── test_stab_track.py         # Integration tests for Phase 1
└── dashboard.py                   # Flask App & Background Threads
```

### Pattern 1: Global CLI Lock
To prevent race conditions where multiple threads (e.g., background tracking vs. user peer creation) call the WireGuard CLI simultaneously, a global lock must be used.

**Example:**
```python
import threading
import subprocess

_wg_cli_lock = threading.Lock()

def run_wg_command(cmd):
    with _wg_cli_lock:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=10)
```

### Pattern 2: Delta Pattern for Raw Bytes
The Delta Pattern ensures that even if the WireGuard interface restarts or the counter wraps around, cumulative totals remain accurate.

**Logic:**
1. Fetch `current_counter` from `wg show dump`.
2. `delta = current_counter - last_known_counter`.
3. If `delta < 0` (reset/wrap): `delta = current_counter`.
4. `cumulative_total += delta`.
5. `last_known_counter = current_counter`.

[VERIFIED: WireGuard mailing list / Monitoring best practices]

### Pattern 3: Atomic Schema & Logic Migration
To avoid broken intermediate states (e.g., storing GB floats in a BigInteger byte column), the migration must:
1. Update tracking logic to work with raw bytes.
2. Update database schema to `BigInteger`.
3. Convert existing data: `new_total = old_total_gb * (1024**3)`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI Race Conditions | Custom retry logic | `threading.Lock` | Simple, reliable serialization of system calls. |
| Byte Formatting | Manual division | `Utilities.py` or Frontend filters | Keep backend data raw for precision; format only for display. |
| Configuration Parsing | Manual Regex | `configparser` | WireGuard `.conf` is mostly INI-compatible. |

## Common Pitfalls

### Pitfall 1: Precision Loss
**What goes wrong:** Storing `1,073,741,824 bytes` as `1.0` GB. Adding `512 bytes` results in `1.0` GB again due to floating point limits.
**Prevention:** Use `BigInteger` (8-byte integer) in the database and `int` in Python.

### Pitfall 2: `wg-quick` Locking
**What goes wrong:** `wg-quick` can occasionally fail if called while the interface is undergoing other state changes.
**Prevention:** Explicitly lock all `wg` and `wg-quick` calls at the application level.

### Pitfall 3: Daemon Thread Termination
**What goes wrong:** Background threads are killed mid-loop during app shutdown, losing the last 10-60s of traffic data.
**Prevention:** Use a `threading.Event` for shutdown and explicitly call a `flush()` method in `atexit` handlers.

## Code Examples

### Atomic Peer Update & Save
```python
# Based on WireguardConfiguration.py logic
def atomic_peer_update(interface, peer_id, allowed_ips):
    # Update live state
    subprocess.check_output(["wg", "set", interface, "peer", peer_id, "allowed-ips", allowed_ips])
    # Persist to .conf
    subprocess.check_output(["wg-quick", "save", interface])
```

### Raw Byte Collection (Dump)
```python
# Source: wg show <interface> dump
def get_peer_metrics(interface):
    dump = subprocess.check_output(["wg", "show", interface, "dump"]).decode().splitlines()
    peers = []
    for line in dump[1:]:  # Skip interface line
        parts = line.split('\t')
        peers.append({
            "public_key": parts[0],
            "rx_bytes": int(parts[5]),
            "tx_bytes": int(parts[6])
        })
    return peers
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Quick run command | `pytest src/tests/test_delta_pattern.py` |
| Full suite command | `pytest src/tests/` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STAB-01 | `wg set` called for updates | Integration | `grep -E "wg\", \"set" src/modules/WireguardConfiguration.py` | ✅ |
| STAB-02 | `wg-quick save` called | Integration | `grep -E "wg-quick\", \"save" src/modules/WireguardConfiguration.py` | ✅ |
| STAB-03 | CLI calls wrapped in lock | Unit | `pytest src/tests/test_stab_track.py::test_cli_locking` | ❌ Wave 0 |
| STAB-04 | Data flushed on exit | Unit | `pytest src/tests/test_stab_track.py::test_graceful_shutdown` | ❌ Wave 0 |
| TRACK-01| Uses `wg show dump` | Integration | `grep "show\", self.Name, \"dump" src/modules/WireguardConfiguration.py` | ✅ |
| TRACK-02| Data stored as BigInteger | Unit | `pytest src/tests/test_stab_track.py::test_biginteger_storage` | ❌ Wave 0 |
| TRACK-03| Delta Pattern handles reset | Unit | `pytest src/tests/test_delta_pattern.py` | ❌ Wave 0 |
| TRACK-04| Separate totals (RX/TX) | Unit | `pytest src/tests/test_stab_track.py::test_separate_totals` | ❌ Wave 0 |

### Wave 0 Gaps
- `src/tests/test_delta_pattern.py`: Must be created to verify TRACK-03.
- `src/tests/test_stab_track.py`: Must be created to verify integration of locking and storage.

## Delta Pattern Test Design (`src/tests/test_delta_pattern.py`)

The test suite should mock the database and WireGuard CLI to verify the logic in isolation.

```python
import pytest
from unittest.mock import MagicMock

def calculate_delta(current, last_known):
    if current < last_known:
        return current  # Reset detected
    return current - last_known

def test_delta_increment():
    assert calculate_delta(150, 100) == 50

def test_delta_reset():
    assert calculate_delta(50, 100) == 50

def test_delta_no_change():
    assert calculate_delta(100, 100) == 0

def test_cumulative_tracking():
    cumulative = 1000
    last_known = 500
    
    # 1. Normal increment
    current = 600
    delta = calculate_delta(current, last_known)
    cumulative += delta
    last_known = current
    assert cumulative == 1100
    
    # 2. Reset (reboot)
    current = 50
    delta = calculate_delta(current, last_known)
    cumulative += delta
    last_known = current
    assert cumulative == 1150
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `wg-quick down/up` | `wg set` + `wg-quick save` | Recommended | Zero-downtime updates. |
| `Float` (GB) Storage | `BigInteger` (Bytes) | Recommended | Byte-perfect accuracy. |
| `wg show transfer` | `wg show dump` | Performance | Batch collection of all peer data in one call. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `wg-quick save` is available on target systems | Summary | Configuration persistence will require manual `.conf` file editing. |
| A2 | SQLite `INTEGER` supports 64-bit | Pitfalls | Precision loss if restricted to 32-bit. (SQLite INTEGER is 8-byte/64-bit by default). |

## Sources

### Primary (HIGH confidence)
- WireGuard Official Docs - `wg` and `wg-quick` man pages.
- SQLAlchemy Documentation - `BigInteger` type mapping.
- WGDashboard Codebase - `WireguardConfiguration.py`, `dashboard.py`.

### Secondary (MEDIUM confidence)
- Community patterns for WireGuard API wrappers.
