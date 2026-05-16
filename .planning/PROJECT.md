# Project: WGDashboard Enhancements

## Context
WGDashboard is a Python/Flask-based dashboard for managing WireGuard configurations and peers. The user wants to improve stability and add specific usage-tracking features.

## Core Goals
1. **Stability:** Improve the overall robustness and stability of the dashboard.
2. **Total Usage Tracking:** Add a "Total Usage" field for each peer, summing up upload and download data.
3. **Restricted Peer Panel:** Implement a restricted, read-only usage panel that individual peers can access (e.g., via `10.7.0.0:10085`) to view their own metrics without being able to modify any settings or jobs.

## Tech Stack
- Backend: Python/Flask (Existing)
- Frontend: Vue.js 3 (Existing)
- API: Must remain compatible with existing usage.

## Constraints
- Peers must be strictly restricted to read-only access for their own data.
- The panel must be configurable (e.g., port settings).
