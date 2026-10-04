# System Architecture & Flow Specifications

## 1. Flow Diagrams

### Flow A: Inbound Scan Matches Existing Active Case
```mermaid
sequenceDiagram
    autonumber
    actor Truck as Truck LPR Camera
    participant Ingest as FastAPI /api/v1/scans
    participant DB as PostgreSQL Database
    actor Agent as Agency Staff Dashboard

    Truck->>Ingest: POST /api/v1/scans (cam_1001, VIN, lat, lng, image)
    Ingest->>DB: Resolve Camera & Tenant (cam_1001 -> Tenant A)
    Ingest->>DB: INSERT INTO scans (...) (Always stored)
    Ingest->>DB: SELECT FROM cases WHERE tenant_id=A AND vin=VIN AND status='active'
    DB-->>Ingest: Active Case Found (case_id)
    Ingest-->>Truck: 201 Created (matched_existing_case=True, case_id)
    Agent->>DB: GET /api/v1/cases/{id}/scans (JWT Bearer)
    DB-->>Agent: Chronological Location Trail (including new sighting)
```

---

### Flow B: Inbound Scan Creates New Repossession Opportunity
```mermaid
sequenceDiagram
    autonumber
    actor Truck as Truck LPR Camera
    participant Ingest as FastAPI /api/v1/scans
    participant DB as PostgreSQL Database
    participant Partner as Mock Eligibility Service
    actor AnyAgent as Any Authenticated Staff (Agency A or B)

    Truck->>Ingest: POST /api/v1/scans (cam_2050, new_vin, lat, lng, image)
    Ingest->>DB: Resolve Camera & Tenant (cam_2050 -> Tenant B)
    Ingest->>DB: INSERT INTO scans (...) (Always stored)
    Ingest->>DB: Check active case for Tenant B + new_vin (Not Found)
    Ingest->>Partner: POST /mock/partner-network/eligibility (new_vin)
    Partner-->>Ingest: { "still_eligible_for_repo": true }
    Ingest->>DB: INSERT INTO cases (vin, status='pending_claim', origin_tenant=B, tenant_id=NULL)
    Ingest-->>Truck: 201 Created (created_new_case=True, status='pending_claim')
    AnyAgent->>DB: GET /api/v1/cases?status=pending_claim
    DB-->>AnyAgent: Sighted vehicle appears in global pending claims pool
```

---

### Cross-Tenant Claiming & Race Condition Defense
```mermaid
sequenceDiagram
    autonumber
    actor AgentA as Staff User (Tenant A)
    actor AgentB as Staff User (Tenant B)
    participant API as FastAPI /api/v1/cases/{id}/claim
    participant DB as PostgreSQL (Row Lock)

    AgentA->>API: POST /cases/{id}/claim (User A JWT)
    AgentB->>API: POST /cases/{id}/claim (User B JWT)
    Note over API,DB: Concurrent Claim Requests Arrive Simultaneously
    API->>DB: [Tx 1] SELECT * FROM cases WHERE id=:id FOR UPDATE
    DB-->>API: [Tx 1] Lock Acquired (status='pending_claim')
    API->>DB: [Tx 2] SELECT * FROM cases WHERE id=:id FOR UPDATE (Blocked)
    API->>DB: [Tx 1] UPDATE cases SET status='active', tenant_id=Tenant_A, user=User_A
    API->>DB: [Tx 1] COMMIT
    API-->>AgentA: 200 OK (Case Claimed Successfully)
    DB-->>API: [Tx 2] Lock Released to Tx 2
    Note over API: Tx 2 checks status == 'pending_claim' (Now FALSE, is 'active')
    API->>DB: [Tx 2] ROLLBACK
    API-->>AgentB: 409 Conflict ("Case has already been claimed")
```
