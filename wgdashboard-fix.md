# WGDashboard Enterprise-Grade Stability & Security Fixes

Comprehensive refactor to address "thread lock" issues, command/SQL injection vulnerabilities, and architectural gaps for production readiness.

## User Review Required

> [!WARNING]
> **Breaking Change: Session Persistence**: I will implement a persistent secret key. This means existing sessions might be invalidated *once* during the upgrade, but will persist across future restarts.
> **Security Hardening**: Some API interactions might become stricter (e.g., removing `origins: "*"`) which could affect custom integrations if they don't use the API key properly.
> **Performance Trade-off**: High-frequency metric gathering will be throttled to prevent CPU/Thread spikes.

## Proposed Changes

### 1. Security & Hardening (High Priority)
#### [MODIFY] [dashboard.py](file:///home/admin/Desktop/rootskytahdidkardkecrashkoneh/WGDashboard/src/dashboard.py)
- **Persistent Secret Key**: Read secret key from `wg-dashboard.ini` or environment, instead of `secrets.token_urlsafe(32)` on every boot.
- **Thread-Safe Auth**: Remove global `DashboardConfig.APIAccessed`. Use `flask.g` for request-cycle state.
- **Robust Auth Middleware**: Refactor `auth_req` to use a more secure whitelist check (prefix-based and exact match) to prevent bypasses like `/api/foo/static/bar`.
- **CORS Hardening**: Restrict `origins` to the actual app domain or specific environment variables.

#### [MODIFY] [Utilities.py](file:///home/admin/Desktop/rootskytahdidkardkecrashkoneh/WGDashboard/src/modules/Utilities.py), [Peer.py](file:///home/admin/Desktop/rootskytahdidkardkecrashkoneh/WGDashboard/src/modules/Peer.py), [WireguardConfiguration.py](file:///home/admin/Desktop/rootskytahdidkardkecrashkoneh/WGDashboard/src/modules/WireguardConfiguration.py)
- **Eliminate `shell=True`**: Refactor all `subprocess` calls to use list-based arguments to prevent command injection.
- **Input Validation**: Add stricter regex validation for configuration names, peer names, and IPs.

#### [MODIFY] [WireguardConfiguration.py](file:///home/admin/Desktop/rootskytahdidkardkecrashkoneh/WGDashboard/src/modules/WireguardConfiguration.py)
- **SQL Injection Fix**: Use bind parameters for all SQLAlchemy queries. For dynamic table names in `renameConfiguration`, implement a whitelist or strict sanitization.

---

### 2. Stability & Performance
#### [MODIFY] [SystemStatus.py](file:///home/admin/Desktop/rootskytahdidkardkecrashkoneh/WGDashboard/src/modules/SystemStatus.py)
- **Asynchronous Monitoring**: Move metric gathering to a single long-running background thread. API requests will now return the *latest cached* metrics instantly (zero overhead).

#### [MODIFY] [DashboardWebHooks.py](file:///home/admin/Desktop/rootskytahdidkardkecrashkoneh/WGDashboard/src/modules/DashboardWebHooks.py)
- **Thread Pooling**: Replace `threading.Thread(...).start()` with a shared `Concurrent.futures.ThreadPoolExecutor` with a fixed size (e.g., 4) to prevent thread leaks.

#### [MODIFY] [gunicorn.conf.py](file:///home/admin/Desktop/rootskytahdidkardkecrashkoneh/WGDashboard/src/gunicorn.conf.py)
- Increase worker/thread count based on CPU cores.

---

### 3. Enterprise Features (Optional but Recommended)
- **CSRF Protection**: Add `Flask-WTF` or equivalent for API state-changing requests.
- **Enhanced Logging**: Centralize sensitive logs and ensure they don't leak private keys.

## Verification Plan

### Automated Tests
- **Security Audit**: Run `security_scan.py` and `bandit` on the modified code.
- **Concurrency Test**: Stress test the API with 100+ concurrent requests.
- **Injection Test**: Attempt "malicious" configuration names and verify they are rejected or handled safely.

### Manual Verification
- Verify successful login/logout and session persistence across restarts.
- Verify WireGuard peer addition/deletion still works with the new `subprocess` logic.
- Check dashboard performance on the System Status page.
