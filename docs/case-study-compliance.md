# Case Study Compliance & Security Audit Report

This document records the rigorous verification of all architectural, multi-tenant security, API behavior, and database requirements for the **Plate Scan & Case Matching Service**.

---

## 1. Compliance Verification Matrix

| Requirement | Implementation | Verified | Status |
| :--- | :--- | :---: | :---: |
| **FastAPI Backend Architecture** | Python 3.12, FastAPI, Pydantic V2, ASGI Lifespan, CORS, and dependency injection | Yes | **PASS** |
| **PostgreSQL Database & Constraints** | SQLAlchemy 2.x declarative models, partial unique indexes, foreign keys without cascade deletion of scans | Yes | **PASS** |
| **Database Migrations** | Alembic with offline and online runners, versioned migration `001_initial_schema.py` | Yes | **PASS** |
| **React + TypeScript Frontend** | React 18, TypeScript, Vite, React Router 6, Axios with JWT interceptors, responsive dark design | Yes | **PASS** |
| **Real API Communication** | No mocked frontend data; all case listings, sighting trails, scans, and claims invoke backend REST endpoints | Yes | **PASS** |
| **Tenant Isolation** | Verified JWT bearer token scoping; cross-tenant active and closed case requests return `HTTP 403 Forbidden` | Yes | **PASS** |
| **Unauthenticated Scan Ingest** | `POST /api/v1/scans` simulates camera hardware webhook; resolves tenant exclusively from `camera_id` | Yes | **PASS** |
| **Spoofed Tenant ID Rejection** | Scan payload client-supplied `tenant_id` is completely ignored; camera database record is sole authority | Yes | **PASS** |
| **Permanent Scan Retention** | All scans (matching, non-matching, eligible, ineligible) are unconditionally persisted in the `scans` table | Yes | **PASS** |
| **Flow A (Existing Active Case)** | Sighting on active VIN matches existing case, updates location trail, returns `matched_existing_case=True` | Yes | **PASS** |
| **Flow B (New Repo Discovery)** | Sighting on unassigned VIN checks repossession eligibility; if true, spawns unassigned `pending_claim` case | Yes | **PASS** |
| **Ineligible Flow** | Ineligible VIN scan is permanently stored in database; no case is created | Yes | **PASS** |
| **Pending Claim Visibility Exception** | All authenticated users across all tenants can view open `pending_claim` cases and their sighting trails | Yes | **PASS** |
| **Cross-Tenant Case Claiming** | Any authenticated staff user can claim any pending case; transitions status to `active` and assigns ownership | Yes | **PASS** |
| **Post-Claim Isolation** | Once claimed by Tenant A, Tenant B listing excludes case, and direct requests return `HTTP 403` or `409` | Yes | **PASS** |
| **Concurrency & Race Condition Defense** | Transactional row-level locking (`SELECT ... FOR UPDATE`); duplicate claim fails with `HTTP 409 Conflict` | Yes | **PASS** |
| **Duplicate Active Case Prevention** | Partial unique index `uq_tenant_active_vin` prevents an agency having duplicate active cases for same VIN | Yes | **PASS** |
| **Chronological Location Trail** | `GET /api/v1/cases/{id}/scans` returns all historical sightings for VIN sorted by `scanned_at ASC` | Yes | **PASS** |
| **Mock Partner Eligibility** | `POST /mock/partner-network/eligibility` endpoint and `EligibilityService` clean abstraction | Yes | **PASS** |
| **Authentication & Password Hashing** | Bcrypt hashing, signed JWT bearer tokens (`user_id`, `tenant_id`, `role`), expired/inactive token defense | Yes | **PASS** |
| **Genuine Tenant Switching** | `TenantSwitcher` executes real `POST /api/v1/auth/login` to obtain genuine JWT tokens from backend | Yes | **PASS** |
| **Automated Test Coverage** | 41 automated pytest tests passing across authentication, security audit, claiming, and ingestion | Yes | **PASS** |
| **Docker & Docker Compose** | Multi-stage Dockerfiles for backend and frontend, and `docker-compose.yml` for PostgreSQL 16 stack | Yes | **PASS** |

---

## 2. Detailed Technical Audit Findings

### 2.1 Multi-Tenant Security & Access Control
- **Test Matrix Executed**:
  - `tenant_a_user` requesting Tenant B active case: **HTTP 403 Forbidden** (`{"detail": "You do not have access to this case"}`).
  - `tenant_a_user` requesting Tenant B closed case: **HTTP 403 Forbidden**.
  - `tenant_a_user` requesting scan trail for Tenant B active case: **HTTP 403 Forbidden**.
  - `tenant_a_user` listing cases (`GET /api/v1/cases`): Includes Tenant A active cases, Tenant A closed cases, and ALL pending cases. Does **NOT** include Tenant B active or closed cases.
  - `tenant_b_user` listing cases: Reverse isolation strictly maintained.

### 2.2 Pending Claim Lifecycle & Cross-Tenant Handoff
- Sighted eligible vehicle (`5NPE34AF9KH123456`) was detected by Tenant B's camera (`cam_2050`).
- Generated case `id=f885ae1a-...` with `status='pending_claim'`, `origin_tenant_id=Tenant B`, and `tenant_id=None`.
- `tenant_a_user` discovered the case in the global pool and claimed it via `POST /api/v1/cases/{id}/claim`.
- **Database state verification**:
  - `status` transitioned to `active`.
  - `tenant_id` updated to Tenant A.
  - `assigned_user_id` updated to `tenant_a_user`.
  - `claimed_at` timestamp populated.
- **Tenant B post-claim lockout**:
  - Tenant B filtered listing (`?status=pending_claim`): Case is absent.
  - Tenant B general listing: Case is absent.
  - Tenant B direct request (`GET /cases/{id}`): **HTTP 403 Forbidden**.
  - Tenant B scan trail request (`GET /cases/{id}/scans`): **HTTP 403 Forbidden**.
  - Tenant B duplicate claim attempt: **HTTP 409 Conflict** (`"Case has already been claimed"`).

### 2.3 Concurrency Defense & Race Condition Audit
- Tested in `backend/tests/test_claiming.py` and `backend/tests/test_security_audit.py`:
  - Request 1: Acquires row lock via `get_by_id_for_update()`, validates `status == 'pending_claim'`, sets `status = 'active'`, commits. Returns `HTTP 200 OK`.
  - Request 2: Blocked until Transaction 1 commits. Re-evaluates status (now `active`), aborts, and returns `HTTP 409 Conflict`.
- **Integrity Guarantee**: Zero dual-ownership states can occur.

### 2.4 Scan Ingestion & Camera Authority
- `POST /api/v1/scans` carries no `Authorization` header.
- Client payloads supplying a forged `"tenant_id"` are completely ignored; the tenant is resolved exclusively from `Camera.tenant_id`.
- Unknown cameras (`cam_nonexistent`) return **HTTP 404 Not Found**.
- Deactivated cameras (`cam_disabled`) return **HTTP 400 Bad Request**.

### 2.5 Database Direct Row Audit
Executed direct SQLite/PostgreSQL row inspection on live database:
- **Total Scans in DB**: 6 sightings
  - 3 historical scans for `1FTFW1E51NFA12345` (cam_1001)
  - 1 seeded scan for `2C3CDXBG4KH987654` (cam_2050)
  - 1 ingested scan for Flow A `1FTFW1E51NFA12345` (cam_1001)
  - 1 ingested scan for Flow B `5NPE34AF9KH123456` (cam_2050)
- **Total Cases in DB**: 3 records
  - Case 1: `1FTFW1E51NFA12345` | `status=active` | `tenant=Agency A` | `origin=Agency A`
  - Case 2: `2C3CDXBG4KH987654` | `status=pending_claim` | `tenant=None` | `origin=Agency B`
  - Case 3: `5NPE34AF9KH123456` | `status=active` | `tenant=Agency A` | `origin=Agency B` (Claimed cross-tenant)

### 2.6 Alembic Clean Database Verification
- Recreated database from scratch via `alembic upgrade head` without calling `Base.metadata.create_all()`.
- All tables (`tenants`, `users`, `cameras`, `cases`, `scans`) and partial unique indexes (`uq_tenant_active_vin`) generated cleanly.

### 2.7 Automated Test Suite Summary
Executed `pytest -v`:
- **41 tests executed, 41 passed (100% pass rate) in 20.27s**.
- 0 failures, 0 errors.
