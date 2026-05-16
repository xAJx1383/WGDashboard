# Research Summary: WGDashboard Enhancement

**Domain:** VPN Management / WireGuard Dashboard
**Researched:** 2025-05-21
**Overall confidence:** HIGH

## Executive Summary

The research focused on three key areas for enhancing WGDashboard: robust peer usage tracking, a restricted read-only usage panel for VPN clients, and general stability improvements for Flask-based WireGuard management. 

WGDashboard currently implements basic usage tracking using a "delta pattern" to handle WireGuard counter resets. However, precision can be improved by storing raw bytes instead of converted Gigabyte floats, and performance can be enhanced by switching to `wg show dump` for batch processing of peer data.

For the client-facing usage panel, the most secure and user-friendly approach is to identify peers automatically via their source VPN IP address. This allows for a "zero-login" experience where clients connected to the VPN can view their own stats simply by visiting a specific port/URL on the VPN gateway, while unauthorized external access is blocked by middleware and firewall rules.

Stability research highlighted critical pitfalls when using high-level tools like `wg-quick` for programmatic management, particularly regarding race conditions in routing table assignment and firewall locks. The recommendation is to shift towards granular `wg set` commands for configuration updates to avoid dropping active sessions.

## Key Findings

**Stack:** Python/Flask (Backend), SQLite/SQLAlchemy (Persistence), WireGuard-tools (`wg`, `wg-quick`).
**Architecture:** Background polling of `wg` binary with persistence in relational DB using the "Delta Pattern" for counter resets.
**Critical pitfall:** Dropping all active sessions by using `wg-quick down/up` for minor config changes instead of using atomic `wg set` updates.

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Robust Usage Tracking** - Refine the existing persistence logic to use high-precision byte counters and batch-process peer data using `wg show dump`.
   - Addresses: Precision issues, performance overhead of multiple `wg` calls.
   - Avoids: Data loss on interface reset.

2. **Peer Usage Panel** - Implement a new Flask blueprint restricted by source IP to allow peers to see their own usage without traditional login.
   - Addresses: Feature request for client self-service.
   - Avoids: Complexity of managing separate client accounts for simple usage checks.

3. **Stability & Performance Optimization** - Implement atomic configuration updates and explicit routing table management to prevent `wg-quick` race conditions.
   - Addresses: Stability issues when managing multiple interfaces.
   - Avoids: Dropping client sessions during updates.

**Phase ordering rationale:**
- Robust tracking is the foundation for the usage panel. Stability improvements should be integrated alongside or after to ensure the new features don't introduce regressions.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core technologies are already in use and well-documented. |
| Features | HIGH | Requirements for the usage panel are clear and technically feasible. |
| Architecture | HIGH | The "Delta Pattern" is the industry standard for WG usage tracking. |
| Pitfalls | MEDIUM | Most pitfalls are documented in community discussions; specific WGDashboard regressions need testing. |

## Gaps to Address

- Testing the performance of `wg show dump` with a very large number of peers (e.g., >1000).
- Verifying if `CAP_NET_ADMIN` is sufficient for the Flask process to avoid `sudo` for all operations.
