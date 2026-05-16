# Phase 2: Restricted Peer Usage Panel - Research

**Researched:** 2026-05-16
**Domain:** Network identification, Flask Blueprints, WireGuard Metrics
**Confidence:** HIGH

## Summary

The goal of this phase is to provide WireGuard peers with a secure, zero-login view of their connection metrics. The system will identify peers automatically based on their source VPN IP (`request.remote_addr`) and match it against the `AllowedIPs` stored in the WireGuard configuration database. This ensures that peers can only see their own metrics without requiring additional credentials.

**Primary recommendation:** Implement a dedicated Flask Blueprint that uses a custom decorator or `before_request` hook to resolve the current peer by IP address, and serve a read-only responsive HTML template with metrics.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Peer Identification | API / Backend | — | Identifying peer via IP must happen on the server for security. |
| Metrics Extraction | API / Backend | — | Reading `wg show dump` is a server-side privileged operation. |
| Read-only View | Browser / Client | Frontend Server (SSR) | SSR provides a lightweight, no-JS-required (or minimal JS) view for better compatibility. |
| Configuration | API / Backend | — | Managing binding interface/port is a backend config responsibility. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | 3.0.x | Web Framework | Existing project standard for all API and UI routes. |
| ipaddress | Built-in | IP/Subnet Matching | Python standard library for robust CIDR and IP operations. [VERIFIED: python docs] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| Bootstrap | 5.3.x | Responsive UI | Quick, mobile-friendly styling for the peer panel. |
| Jinja2 | 3.1.x | Templating | Project standard for server-side rendering. |

**Installation:**
No new packages are required; existing dependencies cover all needs.

## Architecture Patterns

### Recommended Project Structure
```
src/
├── peer_panel.py      # New Flask Blueprint for peer-specific routes
static/dist/
└── WGDashboardPeerPanel/
    └── panel.html     # Lightweight HTML template for the peer panel
```

### Pattern 1: IP-Based Peer Identification
The system must iterate through all active WireGuard configurations and their associated peers to match the requester's IP.

```python
# Logic verified against modules/Utilities.py and modules/WireguardConfiguration.py
import ipaddress

def get_peer_by_ip(remote_addr, wireguard_configs):
    user_ip = ipaddress.ip_address(remote_addr)
    for config in wireguard_configs.values():
        if not config.getStatus(): continue
        for peer in config.Peers:
            # peer.allowed_ip is a string like "10.0.0.2/32, fd00::2/128"
            networks = [n.strip() for n in peer.allowed_ip.split(',')]
            for net_str in networks:
                try:
                    if user_ip in ipaddress.ip_network(net_str, strict=False):
                        return peer
                except ValueError:
                    continue
    return None
```

### Anti-Patterns to Avoid
- **Session-based Auth in Peer Panel:** Do not use the existing `login_required` decorator; the peer panel must be zero-login.
- **Direct Database Querying for IPs:** Always use the in-memory `WireguardConfigurations` cache to ensure we match against active peers and avoid unnecessary DB load.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| IP CIDR matching | Regex or string splits | `ipaddress` module | Handles IPv4/IPv6 edge cases and subnet math correctly. |
| Responsive Layout | Custom CSS grid | Bootstrap/Tailwind | Ensures PANEL-06 (responsive interface) is met with minimal effort. |

## Common Pitfalls

### Pitfall 1: Reverse Proxy IP Masking
**What goes wrong:** `request.remote_addr` returns the IP of Nginx instead of the VPN peer.
**Why it happens:** Standard behavior for reverse proxies.
**How to avoid:** Use `werkzeug.middleware.proxy_fix.ProxyFix` if the dashboard is behind a proxy, or ensure peers connect directly to the VPN gateway IP. [CITED: Flask Docs]

### Pitfall 2: Overlapping Subnets
**What goes wrong:** One IP matches multiple peers (e.g., if `0.0.0.0/0` is misconfigured as a peer's AllowedIP).
**Why it happens:** WireGuard configuration allows broad subnets.
**How to avoid:** Always prefer the most specific match (/32 or /128) or return the first match found in active interfaces.

## Code Examples

### Peer Panel Blueprint Skeleton
```python
from flask import Blueprint, render_template, request, abort
from modules.Utilities import FormatBytes

peer_panel = Blueprint('peer_panel', __name__, template_folder='static/dist/WGDashboardPeerPanel')

@peer_panel.route('/usage')
def peer_usage():
    peer = get_peer_by_ip(request.remote_addr, WireguardConfigurations)
    if not peer:
        abort(403) # Forbidden if not a recognized VPN peer
    
    return render_template('panel.html', peer=peer, format_bytes=FormatBytes)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Shared login for all | Zero-login IP ID | This Phase | Better UX, zero credential management for peers. |
| Manual Usage Check | Auto-refreshing Dashboard | This Phase | Real-time visibility into connection quality. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `request.remote_addr` contains the VPN internal IP | Summary | Identification will fail if traffic is NATed before reaching Flask. |
| A2 | Peers want a single-page view | UI Planning | Might need multiple pages if more features are added later. |

## Open Questions

1. **How to handle Dual-Port configuration (PANEL-05)?**
   - Recommendation: If `peer_panel_port` != `app_port`, start a secondary Flask/Waitress instance in a background thread. Otherwise, register as a Blueprint on the main app.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| wg | Metrics | ✓ | 1.0.20210223 | — |
| Python | Runtime | ✓ | 3.10.x | — |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Quick run command | `pytest src/tests/test_peer_panel.py` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command |
|--------|----------|-----------|-------------------|
| PANEL-01 | Blueprint Isolation | Unit | `pytest src/tests/test_peer_panel.py::test_blueprint_isolation` |
| PANEL-02 | IP Identification | Unit | `pytest src/tests/test_peer_panel.py::test_ip_identification` |
| PANEL-04 | Data Visibility | Unit | `pytest src/tests/test_peer_panel.py::test_data_visibility` |

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V4 Access Control | yes | IP-based identification matching `AllowedIPs`. |
| V5 Input Validation | yes | Validate that `remote_addr` is a valid IP and match against sanitized CIDRs. |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| IP Spoofing | Spoofing | Rely on WireGuard kernel verification. Access should be restricted to VPN interface. |
| Data Leakage | Information Disclosure | Ensure peer index only returns data for the matched peer object. |

## Sources

### Primary (HIGH confidence)
- `src/dashboard.py` - Flask app structure
- `src/modules/WireguardConfiguration.py` - Peer data structure
- `src/modules/Utilities.py` - IP utilities
- `src/client.py` - Blueprint pattern example
