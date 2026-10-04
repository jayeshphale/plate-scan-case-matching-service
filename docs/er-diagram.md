# Database Entity-Relationship (ER) Diagram & Schema Specification

## 1. Mermaid Entity-Relationship Diagram

```mermaid
erDiagram
    TENANT ||--o{ USER : employs
    TENANT ||--o{ CAMERA : operates
    TENANT ||--o{ CASE : owns_active_or_closed
    TENANT |o--o{ CASE : discovered_pending
    USER ||--o{ CASE : assigned_agent
    CAMERA ||--o{ SCAN : transmits

    TENANT {
        string id PK "UUID"
        string name UK "Agency Name"
        datetime created_at
        datetime updated_at
    }

    USER {
        string id PK "UUID"
        string tenant_id FK "FK to tenants.id ON DELETE CASCADE"
        string username UK "Unique Username"
        string email UK "Unique Email"
        string password_hash "Bcrypt hash"
        string role "staff | admin"
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    CAMERA {
        string id PK "UUID"
        string camera_id UK "External Hardware ID (e.g. cam_1001)"
        string tenant_id FK "FK to tenants.id ON DELETE CASCADE"
        string name "Descriptive Camera Name"
        string truck_identifier "Truck fleet plate/ID"
        boolean is_active
        datetime created_at
    }

    CASE {
        string id PK "UUID"
        string vin "Vehicle Identification Number (Indexed)"
        string origin_tenant_id FK "Nullable: Identifying Tenant"
        string tenant_id FK "Nullable: Assigned Tenant (NULL when pending)"
        string assigned_user_id FK "Nullable: Assigned Agent (NULL when pending)"
        string status "pending_claim | active | closed (Indexed)"
        datetime created_at
        datetime updated_at
        datetime claimed_at "Nullable: Timestamp of claim"
        datetime closed_at "Nullable: Timestamp of close"
    }

    SCAN {
        string id PK "UUID"
        string camera_id "External Camera Identifier (Indexed)"
        string plate "License Plate Text (Indexed)"
        string vin "Vehicle Identification Number (Indexed)"
        float latitude "GPS Latitude"
        float longitude "GPS Longitude"
        datetime scanned_at "Sighting Timestamp (Indexed)"
        string image_url "Capture Image Storage URL"
        datetime created_at
    }
```

---

## 2. Key PostgreSQL Constraints & Performance Indexes

### Partial Unique Index on Active Cases
Ensures an agency cannot accidentally create or claim duplicate active cases for the exact same VIN:
```sql
CREATE UNIQUE INDEX uq_tenant_active_vin ON cases (tenant_id, vin) WHERE status = 'active';
```

### Composite Ingestion Index
Optimizes Flow A lookup (`tenant_id` + `vin` + `status='active'`) during scan webhooks:
```sql
CREATE INDEX ix_case_tenant_vin_status ON cases (tenant_id, vin, status);
```

### Chronological Location Trail Index
Accelerates retrieval of the vehicle's sighting history ordered by time:
```sql
CREATE INDEX ix_scans_vin_scanned_at ON scans (vin, scanned_at);
```
