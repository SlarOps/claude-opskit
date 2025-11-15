# Datadog Skill Usage Examples

This document provides detailed example interactions showing how to use the Datadog incident metrics skill effectively.

## Dashboard Queries

### Example 1: Production Dashboard Analysis

**User Query:** "Check the production dashboard, we're having issues"

**Response Approach:**
1. Search for dashboard: `python3 scripts/query_dashboard.py --search "production"`
2. Query with analyze mode: `python3 scripts/query_dashboard.py --dashboard-id "dashboard-abc-123" --from-time "1h ago"`
3. Present findings with anomalies highlighted
4. Provide actionable recommendations

**Sample Output:**
```
Dashboard queried successfully with ANALYZE mode (95% token savings):
- 15 widgets analyzed
- 28 queries executed
- 25 successful, 3 no data

Analyzed findings from widgets:

Widget: "API Response Time (p95)"
- Metric: avg:trace.web.request.duration.by.service.95p{service:api-gateway}
- Statistics: min=245ms, max=1,200ms, avg=687ms, latest=1,150ms
- ⚠️ ANOMALY DETECTED: Latest value 67% higher than average (HIGH severity)

Widget: "Database Connection Pool"
- Metric: avg:postgres.connections.used{host:db-primary}
- Statistics: min=85, max=95, avg=92, latest=95
- ⚠️ Near capacity: 95/100 connections used

Widget: "Error Rate (5xx)"
- Metric: sum:http.status_code.5xx{service:api-gateway}
- Statistics: min=0.05%, max=3.8%, avg=1.2%, latest=3.5%
- ⚠️ ANOMALY DETECTED: Latest value 192% higher than average (HIGH severity)

Recommendations:
1. Scale API gateway instances immediately (response time spike + high error rate)
2. Increase database connection pool size (at 95% capacity)
3. Investigate recent deployments causing 5xx errors
4. Check for traffic spike or inefficient query patterns
```

### Example 2: Dashboard Discovery

**User Query:** "What dashboards do we have for kubernetes?"

**Response Approach:**
1. Search: `python3 scripts/query_dashboard.py --search "kubernetes"`
2. List matching dashboards with descriptions
3. If multiple found, ask user which to query
4. If single match, proceed with query

**Sample Output:**
```
Found 3 dashboards matching "kubernetes":

1. kubernetes-cluster-overview (dashboard-k8s-001)
   Description: Cluster health, node metrics, pod status

2. kubernetes-application-performance (dashboard-k8s-002)
   Description: Application metrics running on k8s

3. kubernetes-networking (dashboard-k8s-003)
   Description: Network traffic, ingress, service mesh

Which dashboard would you like to query?
```

### Example 3: Kubernetes Homelab Check

**User Query:** "Check my K8s homelab status"

**Response Approach:**
1. Search for homelab dashboard
2. Query with analyze mode
3. Parse pod status metrics by phase
4. Highlight any stuck/pending pods
5. Provide kubectl commands for investigation

**Sample Output:**
```
Dashboard analyzed successfully (2 widgets, 2 queries):

Widget: System CPU Usage
- Metric: avg:system.cpu.user{*}
- Statistics: min=2.78%, max=4.22%, avg=3.34%, latest=3.34%
- Status: ✅ HEALTHY - Very low CPU utilization

Widget: Pod Status by Phase
- Metric: sum:kubernetes_state.pod.ready{*} by {pod_phase}
- Running pods: 12 (stable, min=12, max=12)
- Pending pods: 1 (⚠️ stuck for 1+ hour)
- Succeeded pods: 2 (normal, completed jobs)

Key Findings:
✅ 12 running pods completely stable
✅ CPU usage very low (~3.3%)
⚠️ 1 pod stuck in Pending state for entire hour

Recommendations:
1. Investigate pending pod: kubectl describe pod <pending-pod-name>
2. Check for resource quotas or image pull errors
3. Review pod events: kubectl get events --sort-by='.lastTimestamp'

Overall Cluster Health: 87% (Good with 1 issue)
```

## Individual Metrics Queries

### Example 4: Active Incident Investigation

**User Query:** "We have high CPU on api-gateway, can you check Datadog?"

**Response Approach:**
1. Query individual metrics for api-gateway
2. Use tag-type "service" (default)
3. Run analyze_metrics.py if available
4. Present anomalies with severity
5. Provide immediate and investigative recommendations

**Commands:**
```bash
python3 scripts/query_datadog.py \
  --components "api-gateway" \
  --incident-time "now" \
  --metrics "cpu,memory,error_rate,rps" \
  --output /tmp/metrics.json

python3 scripts/analyze_metrics.py /tmp/metrics.json \
  --output incident_report.md
```

**Sample Output:**
```
Analysis complete. Here are the findings:

CRITICAL Issues:
- api-gateway: CPU usage spiked to 92.4% (avg: 85.2%)
- RPS increased to 2,450 req/s (2.5x normal baseline)

Recommendations:
1. Immediate: Scale api-gateway instances to handle load
2. Investigate: Check for traffic spike or inefficient code path
```

### Example 5: Post-Incident Report

**User Query:** "Generate a report for the incident at 2PM yesterday affecting auth-service and database"

**Response Approach:**
1. Parse specific incident time
2. Query multiple components
3. Use appropriate time window (e.g., --before 30 --after 30)
4. Generate markdown report
5. Summarize key findings

**Commands:**
```bash
python3 scripts/query_datadog.py \
  --components "auth-service,database" \
  --incident-time "2025-01-07 14:00:00" \
  --before 30 \
  --after 30 \
  --output /tmp/incident_metrics.json

python3 scripts/analyze_metrics.py /tmp/incident_metrics.json \
  --output incident_analysis_report.md
```

**Sample Output:**
```
Report generated. Key findings:

HIGH Issues:
- auth-service: Error rate increased to 3.2% (baseline: 0.1%)
- database: Query latency increased 5x during incident window

The detailed report has been saved to incident_analysis_report.md.
```

### Example 6: Host Metrics Check

**User Query:** "Check CPU on ubuntu host"

**Response Approach:**
1. Identify host query (use --tag-type "host")
2. Query system metrics
3. Present CPU breakdown (user, system, idle)
4. Determine health status

**Commands:**
```bash
python3 scripts/query_datadog.py \
  --components "ubuntu" \
  --incident-time "now" \
  --metrics "cpu,memory" \
  --tag-type "host" \
  --before 30 \
  --after 0 \
  --output /tmp/ubuntu_metrics.json
```

**Sample Output:**
```
Analysis complete:

✓ CPU Status: Normal
- User CPU: 3.5% (avg: 3.3%)
- System CPU: 2.1% (avg: 1.8%)
- Idle CPU: 94.3% (avg: 94.8%)

The ubuntu host is running healthy with low CPU utilization.
```

## Reference Queries

### Example 7: Metrics Documentation

**User Query:** "What metrics can I query from Datadog?"

**Response Approach:**
1. Reference `references/common_metrics.md`
2. List metric categories (CPU, Memory, Error Rate, RPS, Network, Disk, Database)
3. Provide examples for each category

**Sample Output:**
```
Available metrics by category:

CPU Metrics:
- system.cpu.user: User CPU usage
- system.cpu.system: System CPU usage
- container.cpu.usage: Container CPU
- kubernetes.cpu.usage.total: K8s CPU usage

Memory Metrics:
- system.mem.used: Used memory
- system.mem.pct_usable: Memory % available
- container.memory.usage: Container memory
- kubernetes.memory.usage: K8s memory usage

Error Rate Metrics:
- trace.*.errors: APM error traces
- http.status_code.5xx: 5xx errors
- error.count: General error count

RPS Metrics:
- trace.*.hits: APM request traces
- http.requests: HTTP requests
- requests.count: General request count

For complete documentation, see references/common_metrics.md
```

## Decision Trees

### When to Use Dashboard vs Individual Metrics

**Use Dashboard Workflow when:**
- User mentions a specific dashboard name
- Investigating general "production issues" or "service health"
- User asks "what dashboards do we have?"
- Want comprehensive view of related metrics
- Token efficiency is important

**Use Individual Metrics when:**
- No relevant dashboard exists
- User asks for specific metric (e.g., "check CPU on service X")
- Quick spot-check needed
- Specific component + metric combination requested
- Generating post-incident reports for specific time windows

### Tag Type Selection

**host** - Use when user mentions:
- "host", "node", "server", "ubuntu", "linux server"
- Physical or virtual machine names
- Infrastructure components

**service** (default) - Use when user mentions:
- "service", "application", "app", "microservice"
- Application component names (api-gateway, auth-service)
- Business logic services

**container_name** - Use when user mentions:
- "container", "docker container"
- Container-specific identifiers

**instance** - Use when user mentions:
- "instance", "EC2 instance", "VM instance"
- Cloud instance identifiers

### Time Window Guidelines

**Short window (15 min before, 0 after):**
- Real-time monitoring
- Quick health checks
- Current status queries

**Standard window (30 min before, 30 after):**
- Active incident investigation
- Detailed analysis around incident time
- Default for most queries

**Extended window (60+ min before/after):**
- Post-incident analysis
- Trend analysis
- Comparative analysis across longer periods
