# Domain Research: WGDashboard Enhancement

This document summarizes the research findings for the WGDashboard enhancement project, focusing on peer usage tracking, restricted client panels, and system stability.

## 1. Stable Peer Usage Tracking

### Current Limitations
- Current implementation uses `wg show <interface> transfer` which returns data in bytes, but WGDashboard converts these to Gigabyte floats before storage, leading to precision loss.
- Usage tracking depends on periodic polling which may miss data if the interface is reset between polls.

### Recommendations
- **Switch to `wg show dump`**: This command provides a comprehensive tab-separated output for all peers, including handshake timestamps and raw byte counts. It is significantly more efficient than calling `show` multiple times.
- **High-Precision Persistence**: Store all traffic data as raw bytes (BigInteger) in the database. Only convert to human-readable units (MB, GB, TB) in the frontend.
- **The Delta Pattern**:
    1. Store `last_known_counter` and `cumulative_total` in the DB.
    2. On each poll:
       - If `current_counter < last_known_counter` (reset detected), add `current_counter` to `cumulative_total`.
       - Else, add `(current_counter - last_known_counter)` to `cumulative_total`.
    3. Update `last_known_counter` to `current_counter`.

## 2. Restricted Usage Panel

### Approach: VPN IP Identification
The most secure and seamless way to serve a usage panel to peers is by identifying them through their VPN source IP.

### Implementation Best Practices
- **Middleware-based Authentication**: Use a Flask `before_request` hook to capture `request.remote_addr`.
- **Peer Lookup**: Match the captured IP against the `AllowedIPs` list in the peer database.
- **Port Isolation**: Serve the usage panel on a dedicated port (e.g., 51821) and bind the Flask listener specifically to the server's VPN interface IP (e.g., `10.0.0.1`).
- **Firewall Restriction**: Use `iptables` or `ufw` to ensure that the panel port is only accessible from the WireGuard interface (`wg0`).
- **Read-Only Scope**: The panel should be a distinct Flask Blueprint with only `GET` routes, ensuring clients cannot modify any configuration.

## 3. Stability & Best Practices

### Mitigating Race Conditions
- **Avoid `wg-quick` for Updates**: Using `wg-quick down/up` to apply changes drops all active sessions. 
- **Use `wg set`**: For adding/removing peers or updating keys live, use `wg set <interface> peer <pubkey> ...`.
- **Sync with `wg-quick save`**: After using `wg set`, call `wg-quick save <interface>` to persist the changes to the `.conf` file.
- **Explicit Routing Tables**: Avoid the `Table = auto` race condition by explicitly assigning a unique `Table` ID to each interface in the dashboard configuration.

### System Performance
- **Background Task Locking**: Ensure that only one background thread is attempting to communicate with the WireGuard binary at a time using a threading lock (already partially implemented in WGDashboard).
- **Graceful Shutdown**: Implement a signal handler to flush any in-memory usage deltas to the database when the Flask app stops.

## 4. Technology Stack Recommendations
- **Backend**: Flask 3.0+
- **Database**: SQLite with SQLAlchemy 2.0 (BigInteger for bytes)
- **Monitoring**: `psutil` for interface IO, `subprocess` for `wg` CLI.
- **IP Logic**: Python `ipaddress` module.

---
For more detailed breakdowns, see:
- [SUMMARY.md](./SUMMARY.md)
- [STACK.md](./STACK.md)
- [FEATURES.md](./FEATURES.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [PITFALLS.md](./PITFALLS.md)
