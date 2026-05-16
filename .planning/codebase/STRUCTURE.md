# Codebase Structure

**Analysis Date:** 2025-05-14

## Directory Layout

```
[project-root]/
├── .github/          # GitHub Actions and issue templates
├── docker/           # Docker build and deployment files
├── src/              # Application source code
│   ├── modules/      # Backend Python modules (Domain logic)
│   ├── static/       # Frontend source and built assets
│   │   ├── app/      # Vue.js source for Admin Dashboard
│   │   ├── client/   # Vue.js source for Client Portal
│   │   ├── dist/     # Compiled frontend assets
│   │   └── locales/  # i18n translation files (JSON)
│   ├── dashboard.py  # Main Flask entry point (Admin)
│   ├── client.py     # Flask Client Blueprint
│   └── requirements.txt # Python dependencies
├── templates/        # Configuration file templates
└── README.md         # Project overview and installation
```

## Directory Purposes

**`src/modules/`:**
- Purpose: Contains all core business logic and system interactions.
- Contains: Python classes for managing WireGuard, Users, Databases, and System Monitoring.
- Key files: `WireguardConfiguration.py`, `Peer.py`, `DashboardConfig.py`.

**`src/static/app/`:**
- Purpose: Admin Dashboard frontend source code.
- Contains: Vue 3 components, Vite config, stores.
- Key files: `src/App.vue`, `src/main.js`.

**`src/static/client/`:**
- Purpose: Client Portal frontend source code.
- Contains: Vue 3 components, Vite config, stores.
- Key files: `src/App.vue`, `src/main.js`.

**`docker/`:**
- Purpose: Deployment configuration for containerized environments.
- Contains: Dockerfile, entrypoint script, docker-compose examples.
- Key files: `Dockerfile`, `compose.yaml`.

## Key File Locations

**Entry Points:**
- `src/dashboard.py`: Main Admin API and web server.
- `src/client.py`: Client Portal API blueprint.
- `src/wgd.sh`: Shell script for managing the application life cycle.

**Configuration:**
- `src/modules/DashboardConfig.py`: Handles `wg-dashboard.ini`.
- `wg-dashboard.ini`: Created at runtime (not in repo), stores server settings.
- `src/modules/DashboardOIDC.py`: Handles OIDC provider configuration.

**Core Logic:**
- `src/modules/WireguardConfiguration.py`: interface management.
- `src/modules/Peer.py`: Peer-level operations.
- `src/modules/SystemStatus.py`: Monitoring logic.

**Testing:**
- `src/test.sh`: Script for running tests (mostly shell-based/manual checks observed).

## Naming Conventions

**Files:**
- Backend Modules: `CamelCase.py` (e.g., `WireguardConfiguration.py`).
- Backend Entry Points: `snake_case.py` (e.g., `dashboard.py`).
- Frontend Components: `camelCase.vue` (e.g., `navbar.vue`) or multi-word `camelCase.vue` (e.g., `configurationList.vue`).

**Directories:**
- Mostly `snake_case` or single word (e.g., `static`, `modules`, `clientComponents`).

## Where to Add New Code

**New Backend API Feature:**
- Route: `src/dashboard.py` (Admin) or `src/client.py` (Client).
- Logic: Create/Modify module in `src/modules/`.

**New UI Component:**
- Admin: `src/static/app/src/components/`.
- Client: `src/static/client/src/components/`.

**New Database Model:**
- Define in the relevant module in `src/modules/` using the `self.metadata` and `db.Table` pattern found in `DashboardClients.py` or `WireguardConfiguration.py`.

## Special Directories

**`src/static/dist/`:**
- Purpose: Built frontend assets served by Flask.
- Generated: Yes (via `npm run build`).
- Committed: Yes (appears to be tracked in this repo).

---

*Structure analysis: 2025-05-14*
