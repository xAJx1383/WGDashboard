# Refactor Engine Creation to use CreateEngine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize SQLAlchemy engine creation across the project by using the `CreateEngine` wrapper from `ConnectionString.py`, which includes SQLite-specific optimizations like WAL mode.

**Architecture:** Replace direct calls to `db.create_engine` or `sqlalchemy.create_engine` with `CreateEngine(ConnectionString(...))`.

**Tech Stack:** Python, SQLAlchemy

---

### Task 1: Update DashboardClients.py

**Files:**
- Modify: `src/modules/DashboardClients.py`

- [ ] **Step 1: Update imports and engine creation**

Modify `src/modules/DashboardClients.py` to import `CreateEngine` and use it.

```python
from .ConnectionString import ConnectionString, CreateEngine
...
self.engine = CreateEngine(ConnectionString("wgdashboard"))
```

### Task 2: Update DashboardClientsPeerAssignment.py

**Files:**
- Modify: `src/modules/DashboardClientsPeerAssignment.py`

- [ ] **Step 1: Update imports and engine creation**

Modify `src/modules/DashboardClientsPeerAssignment.py` to import `CreateEngine` and use it.

```python
from .ConnectionString import ConnectionString, CreateEngine
...
self.engine = CreateEngine(ConnectionString("wgdashboard"))
```

### Task 3: Update DashboardClientsTOTP.py

**Files:**
- Modify: `src/modules/DashboardClientsTOTP.py`

- [ ] **Step 1: Update imports and engine creation**

Modify `src/modules/DashboardClientsTOTP.py` to import `CreateEngine` and use it.

```python
from .ConnectionString import ConnectionString, CreateEngine
...
self.engine = CreateEngine(ConnectionString("wgdashboard"))
```

### Task 4: Update DashboardLogger.py

**Files:**
- Modify: `src/modules/DashboardLogger.py`

- [ ] **Step 1: Update imports and engine creation**

Modify `src/modules/DashboardLogger.py` to import `CreateEngine` and use it.

```python
from .ConnectionString import ConnectionString, CreateEngine
...
self.engine = CreateEngine(ConnectionString("wgdashboard_log"))
```

### Task 5: Update DashboardWebHooks.py

**Files:**
- Modify: `src/modules/DashboardWebHooks.py`

- [ ] **Step 1: Update imports and engine creation**

Modify `src/modules/DashboardWebHooks.py` to import `CreateEngine` and use it. Replace both occurrences.

```python
from .ConnectionString import ConnectionString, CreateEngine
...
self.engine = CreateEngine(ConnectionString("wgdashboard")) # L44
...
self.engine = CreateEngine(ConnectionString("wgdashboard")) # L205
```

### Task 6: Update NewConfigurationTemplates.py

**Files:**
- Modify: `src/modules/NewConfigurationTemplates.py`

- [ ] **Step 1: Update imports and engine creation**

Modify `src/modules/NewConfigurationTemplates.py` to import `CreateEngine` and use it.

```python
from .ConnectionString import ConnectionString, CreateEngine
...
self.engine = CreateEngine(ConnectionString("wgdashboard"))
```

### Task 7: Update PeerJobLogger.py

**Files:**
- Modify: `src/modules/PeerJobLogger.py`

- [ ] **Step 1: Update imports and engine creation**

Modify `src/modules/PeerJobLogger.py` to import `CreateEngine` and use it.

```python
from .ConnectionString import ConnectionString, CreateEngine
...
self.engine = CreateEngine(ConnectionString("wgdashboard_log"))
```

### Task 8: Update PeerJobs.py

**Files:**
- Modify: `src/modules/PeerJobs.py`

- [ ] **Step 1: Update imports and engine creation**

Modify `src/modules/PeerJobs.py` to import `CreateEngine` and use it.

```python
from .ConnectionString import ConnectionString, CreateEngine
...
self.engine = CreateEngine(ConnectionString('wgdashboard_job'))
```

### Task 9: Update PeerShareLinks.py

**Files:**
- Modify: `src/modules/PeerShareLinks.py`

- [ ] **Step 1: Update imports and engine creation**

Modify `src/modules/PeerShareLinks.py` to import `CreateEngine` and use it.

```python
from .ConnectionString import ConnectionString, CreateEngine
...
self.engine = CreateEngine(ConnectionString("wgdashboard"))
```

---

## Verification Plan

### Automated Tests
Since these are mostly architectural changes to how the database engine is initialized, we should verify that the application can still start and interact with the database.

1. Run the existing tests: `src/test.sh` (if applicable)
2. Manually verify one or two modules by ensuring they don't throw errors on initialization.

### Manual Verification
1. Start the dashboard and check the logs for any SQLAlchemy-related errors.
2. Verify that SQLite databases are indeed using WAL mode (optional, but good for confirmation).
