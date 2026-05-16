---
phase: 03-integration-optimization
plan: 03-03
subsystem: database-migration
tags: [data-integrity, migration, bugfix]
dependency_graph:
  requires: [03-02]
  provides: [reliable-migration-tracking]
  affects: [src/modules/WireguardConfiguration.py, src/modules/AmneziaWireguardConfiguration.py]
tech_stack:
  added: [wgd_migrations table]
  patterns: [migration-tracking, data-normalization]
key_files:
  modified: [src/modules/WireguardConfiguration.py, src/modules/AmneziaWireguardConfiguration.py]
decisions:
  - Implement a dedicated 'wgd_migrations' table to break the infinite migration loop in SQLite.
  - Track migration completion per configuration (e.g., float_to_bigint_v1_{dbName}) to ensure all existing tables are processed.
  - Implement a normalization routine that divides exponentially multiplied usage data (> 1 PB) by 1024**3 until it falls back into a realistic range.
  - Add a CASE check in the migration SQL to skip multiplication if the value already appears to be in bytes (>= 1,000,000 GB threshold).
metrics:
  duration: 45m
  completed_date: 2026-05-16
---

# Phase 3 Plan 03-03: Reliability Fix for Database Migration

## Summary
Fixed a critical bug in the database migration logic that caused usage data to be exponentially multiplied by 1024^3 on every application restart. This was caused by unreliable column type reflection in SQLite, which led the application to believe it always needed to run the migration from Float (GB) to BigInteger (Bytes).

## Key Changes

### 1. Reliable Migration Tracking
Introduced a `wgd_migrations` table to explicitly track applied migrations. The migration `float_to_bigint_v1_{dbName}` is now recorded once successfully completed, ensuring that the migration logic never executes twice for the same configuration.

### 2. Migration Logic Refinement
Updated the migration SQL to use a `CASE` statement. Values are only multiplied by `1024**3` if they are below a threshold (1 million GB), which helps prevent re-multiplication of data that is already in bytes.

### 3. Data Normalization
Implemented a self-healing routine that scans for corrupted usage data (values > 1 Petabyte). These values are iteratively divided by `1024**3` until they return to a realistic range, effectively reversing the effects of the multiplication bug.

## Deviations from Plan
None - plan executed exactly as written.

## Verification Results
- **Migration Loop**: Verified using a test script that `wgd_migrations` correctly blocks redundant migration runs.
- **Normalization**: Verified that values corrupted by multiple multiplications (e.g., 2^60 bytes) are successfully restored to their intended byte values (2^30 bytes).
- **Syntax**: Validated modified Python modules for syntax correctness.

## Self-Check: PASSED
- [x] Migration loop is broken; migration executes strictly once.
- [x] Corrupted exponentially-multiplied data is normalized back to correct byte sizes.
- [x] `wgd_migrations` table is created and populated.
