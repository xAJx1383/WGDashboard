# Architecture

**Analysis Date:** 2025-05-14

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vue.js 3)                     │
├──────────────────┬──────────────────┬───────────────────────┤
│   Admin Dashboard│   Client Portal  │    Shared Components  │
│`src/static/app/` │`src/static/client`│ `src/static/app/src/components`│
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (Flask)                         │
│         `src/dashboard.py` & `src/client.py`                 │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Core Business Logic (Python)                │
│         `src/modules/` (WG Config, Peer Management)          │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  OS / System (WireGuard, Networking, DB)                     │
│  `/etc/wireguard`, `wg` CLI, SQLite/MySQL/PG                │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Dashboard API | Main entry point, Admin routes, auth. | `src/dashboard.py` |
| Client Blueprint | Client-facing portal API and routes. | `src/client.py` |
| WG Configuration | Logic for reading/writing `.conf` files. | `src/modules/WireguardConfiguration.py` |
| Peer Management | Peer creation, updates, and tracking. | `src/modules/Peer.py` |
| Client Mgmt | User management for the client portal. | `src/modules/DashboardClients.py` |
| Config Mgmt | Dashboard-wide settings and persistence. | `src/modules/DashboardConfig.py` |
| System Status | Real-time monitoring of CPU, RAM, Network. | `src/modules/SystemStatus.py` |

## Pattern Overview

**Overall:** Layered Monolith with Single-Page Application (SPA) frontends.

**Key Characteristics:**
- Separation of Concerns: Domain logic isolated in `src/modules/`.
- Hybrid Persistence: Configuration in `.ini` and `.conf` files, metadata/tracking in SQL database.
- Background Processing: Python threads used for real-time monitoring and peer updates.

## Layers

**Frontend Layer:**
- Purpose: Provides user interface for Admins and Clients.
- Location: `src/static/app/` (Admin), `src/static/client/` (Client).
- Contains: Vue components, Pinia stores, Vite configuration.
- Depends on: Backend API via REST.

**API Layer:**
- Purpose: Handles HTTP requests, authentication, and routing.
- Location: `src/dashboard.py`, `src/client.py`.
- Contains: Flask routes, request validation, session management.
- Depends on: Core Modules.

**Domain Layer (Modules):**
- Purpose: Implements WireGuard management logic and data processing.
- Location: `src/modules/`.
- Contains: Python classes for Configurations, Peers, Clients, and Utilities.
- Depends on: SQLAlchemy, OS commands, Filesystem.

## Data Flow

### Primary Request Path (Admin UI)

1. User interacts with Admin Dashboard UI (`src/static/app/`).
2. Frontend sends AJAX request to Flask API (`src/dashboard.py`).
3. API validates session and calls relevant module (e.g., `WireguardConfiguration.SetConfig`).
4. Module updates config file and/or database via SQLAlchemy.
5. Success/Failure returned to UI via JSON response.

### Background Peer Tracking

1. `dashboard.py` starts background thread `peerInformationBackgroundThread`.
2. Thread iterates through active WireGuard configurations.
3. For each config, it executes OS commands to get peer stats.
4. Updates peer data in memory and persists historical data to the database.

**State Management:**
- Backend: Flask sessions for auth; in-memory dictionaries (e.g., `WireguardConfigurations`) for interface state.
- Frontend: Pinia stores (`src/static/app/src/stores/`) for application state.

## Key Abstractions

**WireguardConfiguration:**
- Purpose: Represents a WireGuard interface (`wg0`, `wg1`, etc.) and its associated peers.
- Examples: `src/modules/WireguardConfiguration.py`.
- Pattern: Object-Relational Mapping (ORM) and direct File I/O.

**Peer:**
- Purpose: Represents a single VPN client connected to an interface.
- Examples: `src/modules/Peer.py`.

## Entry Points

**Admin Web Server:**
- Location: `src/dashboard.py`.
- Triggers: Gunicorn/Flask execution.
- Responsibilities: Server initialization, route registration, background thread management.

**Client Blueprint:**
- Location: `src/client.py`.
- Triggers: Registration in `dashboard.py`.
- Responsibilities: Client-specific API and UI serving.

## Architectural Constraints

- **Threading:** Multi-threaded Flask app; background threads used for periodic tasks.
- **Global state:** Shared dictionaries for configuration and interface objects (e.g., `WireguardConfigurations` in `dashboard.py`).
- **Permissions:** Requires `NET_ADMIN` capability and root/sudo privileges to manage network interfaces.

## Error Handling

**Strategy:** Centralized Response Object for API, try-except blocks in modules.

**Patterns:**
- `ResponseObject` function in `dashboard.py` and `client.py` for consistent API responses.
- Logging of exceptions in modules via `DashboardLogger`.

---

*Architecture analysis: 2025-05-14*
