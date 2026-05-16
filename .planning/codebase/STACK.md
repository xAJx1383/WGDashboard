# Technology Stack

**Analysis Date:** 2025-05-14

## Languages

**Primary:**
- Python 3.x - Backend API and core logic. Used in `src/*.py` and `src/modules/*.py`.
- JavaScript (ES2022) - Frontend logic. Used in `src/static/app/` and `src/static/client/`.

**Secondary:**
- Vue.js (SFC) - Frontend components. Used in `src/static/app/src/**/*.vue`.
- Shell (Bash) - Setup and management scripts. Used in `src/wgd.sh`, `src/test.sh`, `docker/entrypoint.sh`.

## Runtime

**Environment:**
- Python 3.x
- Node.js (for frontend build)

**Package Manager:**
- pip - Backend dependencies (`src/requirements.txt`).
- npm - Frontend dependencies (`src/static/app/package.json`, `src/static/client/package.json`).
- Lockfile: `package-lock.json` present in frontend directories.

## Frameworks

**Core:**
- Flask 3.1.2 - Backend web framework.
- Vue 3 - Frontend UI framework.
- Vite - Frontend build tool and dev server.

**Testing:**
- Not explicitly detected in `requirements.txt` (no `pytest` or `unittest` config found, though `src/test.sh` exists).

**Build/Dev:**
- Vite 7.x (Admin) / 6.x (Client) - Frontend bundling.
- Gunicorn 25.0.3 - WSGI HTTP Server for production.

## Key Dependencies

**Critical:**
- WireGuard / AmneziaWireGuard - The underlying VPN technology managed by the dashboard.
- SQLAlchemy 2.0.46 - ORM for database interactions.
- Flask-CORS 6.0.2 - Cross-Origin Resource Sharing support.

**Infrastructure:**
- psutil 7.2.2 - System and process utilities for monitoring.
- icmplib 3.0.4 - Python library for ICMP (ping/traceroute).
- tcconfig 0.30.1 - Traffic control tool (used for speed limiting).

## Configuration

**Environment:**
- Configured via `wg-dashboard.ini` (INI format) and environment variables (e.g., `CONFIGURATION_PATH`).
- Key configs: Server port, database type, WireGuard config paths.

**Build:**
- `vite.config.js` in `src/static/app/` and `src/static/client/`.

## Platform Requirements

**Development:**
- Linux (for WireGuard support), Python 3, Node.js.

**Production:**
- Linux with WireGuard/AmneziaWireGuard installed.
- Docker support (optional but recommended).

---

*Stack analysis: 2025-05-14*
