# Roadmap

## Phases
- [ ] **Phase 1: Stabilization & Robust Tracking** - Backend overhaul for atomic updates and high-precision usage persistence.
- [ ] **Phase 2: Restricted Peer Usage Panel** - Implementation of a secure, IP-restricted client portal for viewing personal stats.
- [ ] **Phase 3: Integration & Optimization** - UI updates for the main dashboard and system-wide performance tuning.

## Phase Details

### Phase 1: Stabilization & Robust Tracking
**Goal**: Ensure data integrity and minimize service interruptions during configuration changes.
**Depends on**: Nothing
**Requirements**: STAB-01, STAB-02, STAB-03, STAB-04, TRACK-01, TRACK-02, TRACK-03, TRACK-04
**Success Criteria** (what must be TRUE):
  1. Admin can add/remove peers without interrupting existing peer sessions.
  2. Peer usage is tracked with byte-level precision even after interface resets or reboots.
  3. Database stores cumulative usage in BigInteger format without overflow or precision loss.
  4. Background WireGuard interactions are protected by a thread lock.
**Plans**:
- [ ] 01-01-PLAN.md — Stabilization Foundation & Test Scaffolding
- [ ] 01-02-PLAN.md — High-Precision Tracking Overhaul
- [ ] 01-03-PLAN.md — Atomic Management & Graceful Shutdown

### Phase 2: Restricted Peer Usage Panel
**Goal**: Provide peers with a secure, zero-login view of their own connection metrics.
**Depends on**: Phase 1
**Requirements**: PANEL-01, PANEL-02, PANEL-03, PANEL-04, PANEL-05, PANEL-06
**Success Criteria** (what must be TRUE):
  1. Peer connected to VPN can access the panel at the configured port/IP.
  2. Peer can see their own real-time usage statistics but cannot see other peers' data.
  3. Non-VPN clients (external internet) are blocked from accessing the panel.
  4. The panel UI is responsive and accessible on mobile/desktop.
**Plans**:
- [ ] 02-01-PLAN.md — Blueprint & Identification Foundation
- [ ] 02-02-PLAN.md — Responsive UI & Personal Metrics
- [ ] 02-03-PLAN.md — Configurable Port & Service Isolation

### Phase 3: Integration & Optimization
**Goal**: Finalize UI integration and ensure system-wide performance and reliability.
**Depends on**: Phase 2
**Requirements**: TRACK-05
**Success Criteria** (what must be TRUE):
  1. Main dashboard displays "Total Usage" (cumulative) for all peers.
  2. Dashboard service handles shutdown gracefully without losing pending usage data.
  3. Performance verified for interfaces with large numbers of peers.
**Plans**:
- [x] 03-01-PLAN.md — High-Precision UI Integration
- [x] 03-02-PLAN.md — Performance Verification & Optimization
- [x] 03-03-PLAN.md — Reliability Fix for Database Migration
**UI hint**: yes

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Stabilization & Robust Tracking | 3/3 | Completed | 2026-05-16 |
| 2. Restricted Peer Usage Panel | 3/3 | Completed | 2026-05-16 |
| 3. Integration & Optimization | 3/3 | Completed | 2026-05-16 |
