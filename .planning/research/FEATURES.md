# Feature Landscape

**Domain:** WireGuard Management
**Researched:** 2025-05-21

## Table Stakes

Features users expect in a WireGuard dashboard.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Cumulative Usage Tracking | WG counters reset on interface restart; users need "all-time" stats. | Medium | Requires "Delta Pattern" logic. |
| Configuration Export | QR codes and .conf files for clients. | Low | Already partially implemented. |
| Interface Management | Start/Stop interfaces. | Low | Uses `wg-quick`. |

## Differentiators

Features that set WGDashboard apart.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| IP-Restricted Usage Panel | Peers can see their own stats by visiting the gateway IP. No login needed. | Medium | Uses `request.remote_addr` for auth. |
| Atomic Peer Updates | Add/Remove peers without dropping the entire interface. | Medium | Uses `wg set` + `wg-quick save`. |
| Usage History Graphs | Visualizing traffic over time (last 24h, week, etc.). | High | Requires time-series data storage. |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Public Stats Page | Privacy risk; reveals VPN usage patterns to anyone. | IP-restricted panel. |
| Client-Side Configuration Editing | Clients should not be able to change their assigned IPs or keys. | Admin-only configuration. |

## Feature Dependencies

```
Usage Persistence Logic → Peer Usage Panel
IP Validation Middleware → Peer Usage Panel
```

## MVP Recommendation

Prioritize:
1. **High-Precision Usage Tracking**: Update existing logic to use `wg show dump` and byte-level precision.
2. **Zero-Login Usage Panel**: Create a dedicated port/endpoint restricted to VPN IPs.

Defer:
- Usage History Graphs: High complexity, requires significant DB growth.

## Sources

- [WireGuard community feature requests](https://github.com/ngoduyduyet/wireguard-ui/issues)
- [VPN provider best practices](https://mullvad.net/en/help/wireguard-handshake-and-usage-data/)
