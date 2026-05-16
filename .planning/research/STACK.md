# Technology Stack

**Project:** WGDashboard Enhancement
**Researched:** 2025-05-21

## Recommended Stack

### Core Framework
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.10+ | Backend Runtime | Standard for existing project. |
| Flask | 3.0+ | Web Framework | Lightweight and flexible for system management. |

### Database
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLite | 3.x | Usage Data & Config | Low overhead, single-file persistence. |
| SQLAlchemy | 2.0+ | ORM | Efficient database abstraction and migrations. |

### Infrastructure / CLI
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| WireGuard-tools | Latest | Interface Mgmt | The official `wg` and `wg-quick` utilities. |
| Gunicorn | 21+ | WSGI Server | Production-ready server for Flask. |

### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psutil | 5.9+ | Resource Monitoring | Used for checking interface status and IO. |
| ipaddress | Native | IP Validation | Verifying VPN IPs and subnets. |
| pyroute2 | (Optional) | Netlink API | If shell-parsing of `wg` becomes a bottleneck. |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Tracking | `wg show dump` | Netlink API | Netlink is more complex to implement and maintain than parsing tab-separated text. |
| Persistence | SQLite | Redis | Redis is volatile; SQLite ensures data survives reboots without extra setup. |
| Client Panel | IP-based Auth | JWT/Login | IP-based is seamless for connected VPN clients and "read-only" by nature. |

## Installation

```bash
# Ensure WireGuard tools are installed
sudo apt install wireguard-tools

# Python dependencies
pip install flask sqlalchemy psutil
```

## Sources

- [WireGuard Official Website](https://www.wireguard.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Delta Pattern community posts](https://stackoverflow.com/questions/59169429/how-to-track-wireguard-traffic-usage-per-peer)
