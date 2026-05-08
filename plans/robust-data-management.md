# Architecture Cleanup & Robust Data Management

## Background & Motivation
This fifth round of improvements focuses on architectural cleanup, disk space management, and hardening the data usage calculations:
1. **Redundant Data Transmission:** `Peer.toJson()` currently exports the entire internal state of the object, including the parent configuration, leading to massive and redundant API responses.
2. **Disk Exhaustion Risk:** Configuration backups and job logs are created indefinitely with no rotation or cleanup mechanism.
3. **Redundant Logic:** IP and CIDR validation is duplicated across multiple files.
4. **Usage Calculation Edge Case:** The current traffic counter reset logic is "all or nothing"—if one counter resets, both are added to the cumulative total and zeroed. This can lead to minor data inaccuracies if only one counter reset.

## Phased Implementation Plan

### Phase 1: Refactor `Peer.toJson`
**File:** `src/modules/Peer.py`
*   Replace `return self.__dict__` with a curated dictionary of only the fields the frontend needs. Exclude the `self.configuration` object to avoid circular references and redundant data in the JSON payload.

### Phase 2: Implement Backup Rotation
**File:** `src/modules/WireguardConfiguration.py`
*   In `backupConfigurationFile`, after creating a new backup, add logic to check the number of existing backups for that configuration. If it exceeds a limit (e.g., 100), delete the oldest ones.

### Phase 3: Implement Log Rotation
**File:** `src/modules/PeerJobLogger.py`
*   Add a `cleanupLogs` method that deletes logs older than X days or limits the total number of logs. Call this periodically or within the `log` method.

### Phase 4: Robust Independent Traffic Reset
**File:** `src/modules/WireguardConfiguration.py`
*   Refactor `getPeersTransfer` to handle `total_sent` and `total_receive` counter resets independently. If only one resets, only that one should be added to the cumulative total.

### Phase 5: Centralize Validation Logic
**File:** `src/modules/Utilities.py`, `src/dashboard.py`, `src/modules/WireguardConfiguration.py`
*   Ensure all IP/CIDR validation uses functions from `Utilities.py` instead of inline `ipaddress.ip_network` calls.

## Verification
*   Verify that `Peer.toJson()` output is much smaller and no longer contains the `configuration` object.
*   Verify that only a maximum number of backups are kept on disk.
*   Verify that data usage is still calculated correctly and that independent counter resets (rare but possible in some WG implementations) are handled.
