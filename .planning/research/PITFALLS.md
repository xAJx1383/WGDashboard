# Domain Pitfalls: WireGuard Dashboards

**Domain:** VPN Management
**Researched:** 2025-05-21

## Critical Pitfalls

### Pitfall 1: Session Interruption on Update
**What goes wrong:** Using `wg-quick down` and `wg-quick up` to apply peer changes.
**Why it happens:** Easiest way to ensure the `.conf` file and the kernel interface are in sync.
**Consequences:** Every user on the VPN is disconnected for several seconds.
**Prevention:** Use `wg set` for live updates and `wg-quick save` to sync to disk.

### Pitfall 2: Routing Table Race Conditions
**What goes wrong:** `wg-quick` automatically picking an "unused" routing table (e.g., 51820).
**Why it happens:** Multiple interfaces starting in parallel might both pick the same table ID.
**Consequences:** Interface fails to start or traffic is routed incorrectly.
**Prevention:** Explicitly assign unique `Table` IDs in the configuration for each interface.

## Moderate Pitfalls

### Pitfall 3: Floating Point Precision Loss
**What goes wrong:** Storing cumulative usage in Gigabytes as floats.
**Why it happens:** Easier for display, but leads to rounding errors over time.
**Prevention:** Always store raw bytes as BigIntegers in the database; convert to human-readable units only at the UI layer.

### Pitfall 4: MTU Mismatches
**What goes wrong:** Defaulting to 1500 MTU on the WireGuard interface.
**Why it happens:** Standard Ethernet MTU.
**Consequences:** Connection works for some sites but "hangs" on others due to packet fragmentation.
**Prevention:** Default to `1420` for WireGuard to allow room for the 80-byte encapsulation header.

## Minor Pitfalls

### Pitfall 5: System Clock Jumps
**What goes wrong:** Handshakes fail if the server's clock is set backward (e.g., via NTP).
**Prevention:** Use a monotonic clock for internal timing where possible, though WireGuard's protocol itself is sensitive to system time for replay protection.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Usage Tracking | Data loss on reboot | Flush in-memory "deltas" to DB on SIGTERM. |
| Peer Usage Panel | Source IP Spoofing | Ensure the panel is only reachable on the internal VPN interface (binding to VPN IP). |
| Stability | Shell Injection | Use `subprocess.run(list_of_args)` instead of shell=True when calling `wg`. |

## Sources

- [WireGuard-UI Issue Tracker](https://github.com/ngoduyduyet/wireguard-ui/issues)
- [Linux Kernel Networking documentation](https://www.kernel.org/doc/Documentation/networking/wireguard.txt)
