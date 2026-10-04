# Interview Readiness Notes: 20 Core Architectural Questions & Answers

These answers reflect the exact implementation built for the **Plate Scan & Case Matching Service**.

---

### 1. Why FastAPI?
FastAPI provides asynchronous concurrency natively using Python's `asyncio`, high-throughput ASGI performance comparable to Go/Node.js, automatic OpenAPI/Swagger documentation generation, and strict runtime payload validation via Pydantic V2. For high-frequency ingest endpoints like camera webhooks coupled with authenticated dashboard APIs, it provides optimal developer speed and low runtime overhead.

### 2. Why PostgreSQL?
PostgreSQL provides industrial-grade ACID guarantees, row-level locking (`SELECT ... FOR UPDATE`) essential for resolving case claiming race conditions, rich indexing capabilities (B-tree, compound indexes, partial unique indexes like `UNIQUE (tenant_id, vin) WHERE status = 'active'`), and time-series table partitioning for massive scan histories.

### 3. How does multi-tenancy work in this codebase?
Multi-tenancy uses a shared-database, shared-schema pattern with tenant-scoped logical isolation. Every user and camera belongs to exactly one `tenant_id`. Authenticated requests never trust client-provided tenant parameters; the user's `tenant_id` is extracted directly from the verified cryptographic JWT bearer token and enforced at the repository and service layers.

### 4. How do you prevent cross-tenant data leakage?
All query methods in `CaseRepository` inject tenant isolation filters by default:
```python
base_condition = or_(
    Case.tenant_id == current_tenant_id,
    Case.status == "pending_claim",
)
```
When accessing individual case records or scan trails, the service explicitly checks whether `case.tenant_id == current_user.tenant_id`. If a user attempts to access an active or closed case belonging to a rival agency, the backend raises `HTTP 403 Forbidden`.

### 5. Why is the scan endpoint unauthenticated?
Truck-mounted cameras are embedded edge hardware running automated OCR/LPR firmware on high-frequency road routes. Embedding interactive user credentials or short-lived user tokens is impractical and brittle. Instead, the ingest endpoint acts as an unauthenticated HTTP webhook where identity is determined by hardware token / identifier (`camera_id`).

### 6. How is the tenant identified for a scan?
During ingestion of `POST /api/v1/scans`, the service queries the `cameras` table by `camera_id`. The camera record resolves the owning agency's `tenant_id`. If the camera ID is unknown or marked `is_active=False`, the request is rejected immediately with HTTP 404 or 400.

### 7. Why are all scans stored, even without a case match?
In the repossession industry, vehicle sightings are high-value intelligence. A vehicle spotted in a residential driveway or workplace parking lot today might not have a repo order active today, but a lender might release a repossession order tomorrow. By permanently retaining every sighting, the platform can immediately provide a complete historical location trail the moment a new case opens.

### 8. Explain the existing-case flow (Flow A).
When a camera transmits a scan, the backend resolves the camera's tenant and checks if that tenant already has an active case matching the sighted VIN (`tenant_id + vin + status='active'`). If found:
1. The scan is stored in the `scans` table.
2. The scan is matched to the existing active case.
3. The scan immediately appears in the case's chronological location trail (`GET /api/v1/cases/{id}/scans`).
4. The API returns `matched_existing_case=True`, `created_new_case=False`, and the case ID.

### 9. Explain the new-case flow (Flow B).
If the camera's tenant does not have an active case for the scanned VIN:
1. The scan is stored permanently in the database.
2. The service calls the external partner repossession eligibility check (`POST /mock/partner-network/eligibility`).
3. If eligible, a new case is generated with `status = 'pending_claim'`, `origin_tenant_id = camera.tenant_id`, and `tenant_id = None` (unassigned).
4. If ineligible, no case is opened, but the sighting remains in scan history.

### 10. Why does a new case start as `pending_claim`?
Lenders broadcast repossession eligibility across an entire territory or forwarder network. The vehicle is not yet contracted or secured by the discovering agency. Setting the initial status to `pending_claim` puts the opportunity into a claimable state.

### 11. Why can another tenant claim it?
Repossession forwarders operate dynamic marketplaces. If Agency B's truck spotted the car, but Agency A has a specialized repo tow truck stationed around the corner, allowing any qualified agency to claim the pending case maximizes recovery rates and minimizes lender losses.

### 12. How do you handle concurrent claims (race condition)?
We enforce transactional row-level locking via SQLAlchemy (`query.with_for_update()`). When User 1 and User 2 attempt to claim the same pending case at the exact same millisecond:
1. User 1 acquires the row lock first.
2. User 1 validates `status == 'pending_claim'`, updates status to `active`, assigns `tenant_id` and `assigned_user_id`, and commits.
3. User 2's query unblocks and reads the freshly committed row.
4. User 2's validation detects `status != 'pending_claim'` (now `active`) and immediately aborts with `HTTP 409 Conflict: "Case has already been claimed"`.

### 13. How would you scale this service?
1. Decouple ingestion from processing using message queues (Amazon SQS / Apache Kafka).
2. Deploy stateless FastAPI instances behind an Application Load Balancer with ECS auto-scaling.
3. Use read replicas for dashboard traffic and reporting.
4. Cache camera lookups and active case status in Redis.
5. Partition PostgreSQL tables by time or VIN hash.

### 14. How would you deploy this on AWS?
- **Frontend**: Amazon S3 + CloudFront CDN.
- **API & Ingestion**: Application Load Balancer + Amazon ECS on AWS Fargate.
- **Database**: Amazon RDS for PostgreSQL in Multi-AZ private subnets.
- **Secrets & Config**: AWS Secrets Manager and Systems Manager Parameter Store.
- **Telemetry**: Amazon CloudWatch Logs and Metrics with alarm triggers.

### 15. What would you improve in a production system?
1. Real authentication provider (e.g., AWS Cognito, Okta, or Auth0) with MFA and RBAC.
2. S3 bucket integration with pre-signed URLs for high-resolution camera photo storage.
3. Webhook signature verification (HMAC SHA-256) or mTLS for camera authentication.
4. Real-time push notifications via WebSockets or AWS SNS when a camera hits an active case hotlist.
5. Interactive GIS map integration (Leaflet/Mapbox) for the location trail.

### 16. How would you handle millions of scans per day?
1. Ingest via an API Gateway / ALB directly buffer-backed by Amazon Kinesis Data Streams or SQS.
2. Ingest endpoint returns `HTTP 202 Accepted` immediately without database locking.
3. Background workers bulk-insert batches of 500-1000 scans via PostgreSQL `COPY` or `INSERT ... ON CONFLICT DO NOTHING`.
4. Hotlist matching operates against a Redis in-memory cache of active VINs.

### 17. Would you introduce SQS?
Yes. Placing an Amazon SQS FIFO or standard queue between camera webhooks and backend workers decouples camera network latency from database write pressure, protects the database from traffic spikes, and provides automatic retry dead-letter queues (DLQ) if downstream lender partner networks experience downtime.

### 18. Where would Redis be useful?
1. **Camera Registry Cache**: Cache active camera metadata (`cam_1001 -> tenant_id, is_active`) to eliminate camera database queries on every scan.
2. **Active VIN Hotlist**: Store all active case VINs in a Redis Set (`SISMEMBER active_vins {vin}`) for sub-millisecond Flow A detection.
3. **Rate Limiting**: Prevent malfunctioning cameras from flooding the ingest API.
4. **Distributed Locks**: Alternative or complement to database row locking for distributed coordination.

### 19. How would you secure camera webhooks in production?
1. **Mutual TLS (mTLS)**: Install X.509 client certificates on truck camera hardware modules validated at the ALB/API Gateway.
2. **HMAC Signature Verification**: Compute `X-Signature: HMAC-SHA256(payload, secret_key)` on the camera and verify it in middleware.
3. **IP Allowlisting / VPC Peering**: Route cellular network data from camera cellular carriers through dedicated APNs or private AWS Direct Connect channels.

### 20. How would you monitor this system?
1. **Application Performance Monitoring (APM)**: OpenTelemetry / AWS X-Ray for distributed tracing across webhook ingest, database queries, and external partner calls.
2. **Key Operational Metrics**:
   - Ingestion rate (scans/sec)
   - Flow A match rate vs Flow B new-case rate
   - Claim conflict rate (409s)
   - Partner network eligibility latency and error rate
3. **Structured CloudWatch Logging**: Centralized JSON logs with correlation IDs (`scan_id`, `request_id`, `tenant_id`) and alerting on error spikes.
