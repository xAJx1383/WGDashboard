# External Integrations

**Analysis Date:** 2025-05-14

## APIs & External Services

**Authentication:**
- OIDC (OpenID Connect) - Support for external identity providers for both Admin and Client users.
  - Implementation: `src/modules/DashboardOIDC.py`
  - Config: `wg-dashboard-oidc-providers.json`

**Notifications:**
- Email (SMTP) - Used for sending alerts and password reset tokens.
  - Implementation: `src/modules/Email.py`
  - Client: `EmailSender`
- Webhooks - Support for outgoing HTTP callbacks on certain events.
  - Implementation: `src/modules/DashboardWebHooks.py`

## Data Storage

**Databases:**
- SQLite (Default) - Used for local storage of peer tracking and client info.
  - Client: SQLAlchemy
- PostgreSQL / MySQL (Optional) - Can be configured in `wg-dashboard.ini`.
  - Connection: Configured via `[Database]` section in `wg-dashboard.ini`.
  - Client: `psycopg2` (PostgreSQL), `mysqlclient` (MySQL).

**File Storage:**
- Local filesystem - Stores WireGuard configuration files (`.conf`) and dashboard settings.
- Default paths: `/etc/wireguard`, `/etc/amnezia/amneziawg`, and `./db` for SQLite.

**Caching:**
- None detected (uses in-memory Python dictionaries for some state, but no external cache like Redis).

## Authentication & Identity

**Auth Provider:**
- Custom + OIDC - Username/password with optional TOTP (via `pyotp`).
- Implementation: `src/modules/DashboardConfig.py` (for Admin), `src/modules/DashboardClients.py` (for Clients).

## Monitoring & Observability

**Error Tracking:**
- None detected.

**Logs:**
- File-based logging via Python `logging` module.
- Implementation: `src/modules/DashboardLogger.py` and `src/modules/Log.py`.

## CI/CD & Deployment

**Hosting:**
- Self-hosted on Linux servers.
- Containerized via Docker (`ghcr.io/wgdashboard/wgdashboard`).

**CI Pipeline:**
- GitHub Actions - Used for building Docker images and running CodeQL scans.
- Config: `.github/workflows/docker.yml`, `.github/workflows/codeql-analyze.yaml`.

## Environment Configuration

**Required env vars:**
- `CONFIGURATION_PATH`: Path to the directory containing configuration and database files.

**Secrets location:**
- `wg-dashboard.ini`: Stores hashed passwords and other configuration.
- `wg-dashboard-oidc-providers.json`: Stores OIDC client secrets.

## Webhooks & Callbacks

**Incoming:**
- None detected.

**Outgoing:**
- User-configurable webhooks for events like peer connection/disconnection (to be verified).
- Implementation: `src/modules/DashboardWebHooks.py`.

---

*Integration audit: 2025-05-14*
