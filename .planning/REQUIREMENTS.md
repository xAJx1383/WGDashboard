# Requirements

## v1: Core Enhancements

### Stability (STAB)
- **STAB-01**: Implement atomic configuration updates using `wg set` instead of full interface restarts (`wg-quick down/up`).
- **STAB-02**: Persist live configuration changes to disk using `wg-quick save <interface>` after atomic updates.
- **STAB-03**: Implement thread-safe locking for all WireGuard CLI interactions to prevent race conditions.
- **STAB-04**: Implement graceful shutdown handlers to flush in-memory usage deltas to the database before the service exits.

### Usage Tracking (TRACK)
- **TRACK-01**: Use `wg show <interface> dump` for high-performance, batch collection of peer data.
- **TRACK-02**: Store traffic metrics (Upload, Download, Total) as raw bytes using `BigInteger` (or equivalent) in the database to prevent precision loss.
- **TRACK-03**: Implement the "Delta Pattern" for usage tracking:
    - If `current_counter < last_known_counter` (reset detected), add `current_counter` to `cumulative_total`.
    - Else, add `(current_counter - last_known_counter)` to `cumulative_total`.
- **TRACK-04**: Track separate cumulative totals for upload, download, and combined usage.
- **TRACK-05**: Expose high-precision cumulative usage data in the main dashboard UI.

### Restricted Peer Panel (PANEL)
- **PANEL-01**: Create a dedicated Flask Blueprint for the peer usage panel, isolated from administrative routes.
- **PANEL-02**: Identify peers automatically via source VPN IP (`request.remote_addr`) and match against `AllowedIPs`.
- **PANEL-03**: Enforce read-only access for all routes within the peer panel blueprint.
- **PANEL-04**: Restrict peer data visibility: a connected client must ONLY see their own metrics.
- **PANEL-05**: Support configurable binding interface and port for the peer panel service.
- **PANEL-06**: Provide a simple, responsive web interface for peers to view their usage stats.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STAB-01 | Phase 1 | Completed |
| STAB-02 | Phase 1 | Completed |
| STAB-03 | Phase 1 | Completed |
| STAB-04 | Phase 1 | Completed |
| TRACK-01 | Phase 1 | Completed |
| TRACK-02 | Phase 1 | Completed |
| TRACK-03 | Phase 1 | Completed |
| TRACK-04 | Phase 1 | Completed |
| PANEL-01 | Phase 2 | Completed |
| PANEL-02 | Phase 2 | Completed |
| PANEL-03 | Phase 2 | Completed |
| PANEL-04 | Phase 2 | Completed |
| PANEL-05 | Phase 2 | Completed |
| PANEL-06 | Phase 2 | Completed |
| TRACK-05 | Phase 3 | Completed |
