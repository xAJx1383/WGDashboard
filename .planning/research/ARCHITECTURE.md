# Architecture Patterns

**Domain:** WireGuard Management
**Researched:** 2025-05-21

## Recommended Architecture

WGDashboard should follow a **Hybrid Polling Architecture**. 
- **Admin Backend**: Periodically polls `wg show dump` to update the persistent SQLite database.
- **Client Frontend (Usage Panel)**: Fetches the *last known* usage from the database rather than triggering a fresh `wg` call, ensuring high responsiveness.

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| Background Worker | Polling `wg` binary, calculating deltas, updating SQLite. | OS Shell, Database |
| API Layer (Admin) | Managing interfaces, peers, and global settings. | OS Shell, Database |
| Usage Panel Layer | Serving read-only data to peers based on VPN IP. | Database, Peer Registry |

### Data Flow (Usage Tracking)

1. `Background Worker` runs `wg show <if> dump`.
2. Parsed output is compared with `last_seen_bytes` in SQLite.
3. If `current < last_seen`, a reset is detected; `current` is added to `total`.
4. If `current >= last_seen`, `delta = current - last_seen` is added to `total`.
5. `last_seen_bytes` is updated to `current`.

## Patterns to Follow

### Pattern 1: VPN IP Identification (Middleware)
**What:** Automatically identify the WireGuard peer by their source IP.
**When:** Request comes from a WireGuard interface.
**Example:**
```python
@app.before_request
def identify_peer():
    client_ip = request.remote_addr
    peer = db.query(Peer).filter(Peer.allowed_ips.contains(client_ip)).first()
    if peer:
        g.current_peer = peer
    else:
        abort(403)
```

### Pattern 2: Atomic Peer Management
**What:** Use `wg set` to add/remove peers without restarting the interface.
**When:** Admin modifies peer list.
**Instead of:** `wg-quick down && wg-quick up`

## Anti-Patterns to Avoid

### Anti-Pattern 1: The "Flush-and-Fill" Refresh
**What:** Dropping the entire interface and restarting it to apply a small change.
**Why bad:** Drops all active VPN sessions, causing connectivity blips.
**Instead:** Use `wg set` for live updates and `wg-quick save` to persist to the `.conf` file.

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| Polling Overhead | Negligible | Shell parsing becomes slow | Must use Netlink API |
| Database Size | Tiny | Usage history grows fast | Partitioning / Time-series DB |
| CPU Usage | Low | High due to `wg show` calls | Dedicated monitoring service |

## Sources

- [WireGuard Netlink API documentation](https://www.wireguard.com/xplatform/)
- [Flask Blueprint documentation](https://flask.palletsprojects.com/en/3.0.x/blueprints/)
