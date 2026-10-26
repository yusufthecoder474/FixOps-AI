# FixOps AI Runbook Dataset

22 authored educational scenarios. No real customer incident records or confirmed fixes. JSON is the application source of truth.

## RB-001 — HTTP 500 application error

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Requests fail with an internal server error after a release.

1. Inspect application error logs around the failed request and correlate request IDs.
2. Compare the first error timestamp with deployment and configuration changes.
3. Inspect the failing dependency and exception type; do not assume every 500 has the same cause.

**Evidence:** Redacted stack trace, affected endpoint, deployment time and error rate

**Escalation:** Application owner if errors persist or affect critical requests

Background: [MDN HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)

## RB-002 — High CPU usage

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** CPU stays near saturation and requests slow down.

1. Compare CPU usage, request rate and latency over the same interval.
2. Identify the process or container consuming CPU using existing monitoring.
3. Inspect throttling, hot code paths and recent workload changes before proposing capacity changes.

**Evidence:** CPU time series, throttling metrics and workload change timeline

**Escalation:** Service owner when saturation affects availability

Background: [Kubernetes application troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-application/)

## RB-003 — Database query timeout

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** SQL requests exceed their deadline.

1. Separate connection acquisition time from query execution time using traces.
2. Inspect database activity for long-running queries and wait events.
3. Compare slow query fingerprints and database resource metrics against the incident window.

**Evidence:** Query fingerprint, duration, wait event and redacted trace

**Escalation:** Database owner when timeouts persist

Background: [PostgreSQL monitoring database activity](https://www.postgresql.org/docs/current/monitoring.html)

## RB-004 — Memory pressure and OOM

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Memory grows and a process is killed or restarted.

1. Compare resident memory and configured container memory limits.
2. Inspect termination reasons and events for evidence of OOM termination.
3. Review memory growth against traffic and recent releases; distinguish a sudden peak from sustained growth.

**Evidence:** Memory time series, termination reason and configured limits

**Escalation:** Service owner for profiling and capacity review

Background: [Kubernetes application troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-application/)

## RB-005 — DNS resolution failure

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** A hostname cannot be resolved although other services may work.

1. Identify the exact hostname, namespace and resolution error without collecting credentials.
2. Review resolver configuration and compare the expected service name with service discovery records.
3. Inspect DNS service health and existing DNS logs for the same failure window.

**Evidence:** Hostname category, resolver error and DNS service health

**Escalation:** Platform or DNS owner if resolution fails across workloads

Background: [Kubernetes debugging DNS resolution](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/)

## RB-006 — API latency increase

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** API response times increase without a corresponding error spike.

1. Compare p50, p95 and p99 latency with the baseline and request volume.
2. Inspect distributed traces to separate application time from dependency time.
3. Review resource saturation and recent releases for the slowest endpoint.

**Evidence:** Endpoint latency distribution and slow trace spans

**Escalation:** API owner when latency exceeds the service objective

Background: [Kubernetes application troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-application/)

## RB-007 — Service unavailable HTTP 503

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Clients receive 503 responses or no healthy backend is available.

1. Review the service endpoint list and backend readiness state.
2. Inspect workload events and health check failures during the outage.
3. Compare desired and available replicas and correlate with deployment events.

**Evidence:** Readiness status, endpoints and availability timeline

**Escalation:** On-call service owner immediately for broad outage

Background: [Kubernetes Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/)

## RB-008 — Bad gateway HTTP 502

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** A gateway reports an invalid upstream response.

1. Identify which proxy generated the 502 from existing response metadata.
2. Inspect gateway logs for upstream connection or response errors.
3. Compare upstream health, ports and protocol configuration with the expected route.

**Evidence:** Gateway error category and upstream health

**Escalation:** Gateway and upstream service owners

Background: [MDN HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)

## RB-009 — Gateway timeout HTTP 504

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** A gateway waits too long for an upstream response.

1. Review gateway timing logs to identify the slow upstream.
2. Compare upstream response duration with the configured gateway deadline.
3. Inspect dependency latency and request traces before considering timeout changes.

**Evidence:** Gateway duration, deadline and upstream trace

**Escalation:** Upstream owner for sustained slow responses

Background: [MDN HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)

## RB-010 — Disk space exhausted

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Writes fail because storage is full.

1. Inspect filesystem capacity and inode usage in existing host monitoring.
2. Identify growth in logs, temporary files and application data from storage reports.
3. Check retention policies and ownership before requesting any cleanup.

**Evidence:** Filesystem utilization, inode usage and growth trend

**Escalation:** Storage owner; do not delete files during diagnosis

Background: [Kubernetes application troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-application/)

## RB-011 — TLS certificate failure

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Clients fail TLS validation or report an expired certificate.

1. Inspect the presented certificate expiry, hostname coverage and chain using approved diagnostics.
2. Compare the client clock and trust configuration with expected settings.
3. Review certificate deployment records to identify missing or stale intermediate certificates.

**Evidence:** Expiry dates, hostname match and validation error

**Escalation:** Certificate or platform owner for renewal review

Background: [MDN Transport Layer Security](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Transport_Layer_Security)

## RB-012 — Authentication HTTP 401

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Protected requests are rejected as unauthenticated.

1. Review the response authentication challenge and redacted authentication logs.
2. Check token expiry and intended audience through approved identity tooling without pasting the token.
3. Compare the authentication configuration with the identity provider settings.

**Evidence:** Status, challenge type and redacted identity error

**Escalation:** Identity owner; never request passwords or tokens

Background: [MDN HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)

## RB-013 — Authorization HTTP 403

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** An authenticated client cannot access a resource.

1. Identify the rejected operation and resource category.
2. Compare assigned roles with the documented access policy using approved access records.
3. Review authorization audit events and recent policy changes.

**Evidence:** Denied action and policy decision without credentials

**Escalation:** Resource owner for access policy review

Background: [MDN HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)

## RB-014 — HTTP 429 rate limiting

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Requests are rejected after a traffic burst.

1. Inspect rate limit response metadata and any Retry-After value.
2. Compare request volume and client retry patterns with configured quotas.
3. Review whether retries amplify traffic and document the affected client category.

**Evidence:** Request rate, quota and response headers with secrets removed

**Escalation:** API owner for quota and retry-policy review

Background: [MDN HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)

## RB-015 — Container crash loop

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** A container repeatedly exits and restarts.

1. Inspect previous termination reason, exit code and restart count.
2. Review previous container logs and workload events around the first exit.
3. Compare entrypoint and non-secret configuration with the last working deployment.

**Evidence:** Exit code, restart timeline and redacted logs

**Escalation:** Application owner for startup failure investigation

Background: [Kubernetes application troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-application/)

## RB-016 — Container image pull failure

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** A workload cannot download its container image.

1. Inspect workload events for missing image, registry access or network errors.
2. Compare the image name and tag with the release manifest.
3. Review registry availability and credential reference configuration without reading credential values.

**Evidence:** Image reference and redacted pull error

**Escalation:** Release or registry owner

Background: [Kubernetes application troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-application/)

## RB-017 — Readiness probe failure

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Running containers are excluded from service traffic.

1. Review readiness probe events, path, port and timeout settings.
2. Inspect application startup and dependency health at the same time.
3. Compare probe settings with the application health endpoint contract.

**Evidence:** Probe failure category and readiness transition timeline

**Escalation:** Application and platform owners

Background: [Kubernetes Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/)

## RB-018 — Database connection pool exhausted

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Requests wait for a free database connection.

1. Compare active, idle and waiting pool connections with configured limits.
2. Inspect database sessions and transaction age to identify long-held connections.
3. Compare request concurrency with pool capacity and application connection lifecycle metrics.

**Evidence:** Pool wait duration, connection counts and transaction age

**Escalation:** Application and database owners

Background: [PostgreSQL monitoring database activity](https://www.postgresql.org/docs/current/monitoring.html)

## RB-019 — Database lock contention

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Transactions wait on locks or report a deadlock.

1. Inspect lock monitoring and correlate waiting sessions with database activity.
2. Identify blocking transaction age and the affected relation using approved monitoring.
3. Review transaction boundaries and concurrent workload changes without cancelling sessions.

**Evidence:** Wait chain, transaction age and query fingerprint

**Escalation:** Database owner to assess mitigation

Background: [PostgreSQL viewing locks](https://www.postgresql.org/docs/current/monitoring-locks.html)

## RB-020 — Network connection refused

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Connections to a service port are immediately refused.

1. Verify the expected destination port and service-to-container port mapping.
2. Review listener status from existing telemetry and compare backend readiness.
3. Inspect network and service events for a stopped process or incorrect route.

**Evidence:** Destination service category, port mapping and refusal timestamp

**Escalation:** Service or networking owner

Background: [Kubernetes Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/)

## RB-021 — Packet loss and intermittent connectivity

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** Requests fail intermittently with retransmissions.

1. Compare network error and retransmission metrics with the incident timeline.
2. Identify whether failures share a node, zone or destination.
3. Review interface health and recent network policy changes from existing records.

**Evidence:** Loss trend, affected path and error timestamps

**Escalation:** Network owner with affected scope

Background: [Kubernetes Debug Services](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/)

## RB-022 — Persistent volume mount failure

Authored educational runbook; not a historical incident or verbatim vendor procedure.

**Symptoms:** A workload cannot mount its required persistent storage.

1. Inspect workload and volume events for attachment or mount errors.
2. Review claim binding status, storage class and volume availability.
3. Compare access modes and node placement with the storage requirements.

**Evidence:** Claim state, volume event and node placement

**Escalation:** Storage and platform owners

Background: [Kubernetes application troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-application/)

