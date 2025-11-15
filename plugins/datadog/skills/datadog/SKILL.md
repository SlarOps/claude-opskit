---
name: datadog-incident-metrics
description: This skill should be used when investigating incidents or troubleshooting performance issues by querying Datadog metrics. It enables retrieval and analysis of CPU, memory, error rate, and RPS metrics for affected components, and generates actionable incident reports.
---

# Datadog Incident Metrics

## Purpose

Query and analyze Datadog metrics during incident response. Gather performance data, detect anomalies, and generate incident analysis reports with actionable recommendations.

## When to Use

Invoke this skill when:
- Investigating active incidents or alerts
- Checking Datadog metrics for specific services/components
- Troubleshooting performance issues (high CPU, memory leaks, error spikes, traffic surges)
- Generating incident reports with metrics data
- Analyzing time-series data around incident time windows
- User mentions Datadog, metrics, monitoring, or observability in incident context

## How to Use

### Primary Workflow: Dashboard-First Approach (Recommended)

Prefer dashboard queries over individual metrics because:
- Engineers have pre-optimized queries with aggregations and formulas
- Related metrics are grouped for better context
- Analyze mode saves ~95% tokens by returning statistics instead of raw timeseries

**Step 1: Find dashboard**
```bash
# List all dashboards
python3 scripts/query_dashboard.py --list

# Search by name
python3 scripts/query_dashboard.py --search "production"
```

**Step 2: Query dashboard (analyze mode - default)**
```bash
python3 scripts/query_dashboard.py \
  --dashboard-id "abc-123-def" \
  --from-time "1h ago" \
  --to-time "now" \
  --output /tmp/dashboard_results.json
```

Analyze mode returns:
- Statistics: min, max, avg, latest, first
- Anomaly detection (>20% deviation)
- Series metadata (metric name, scope, tags)
- ~95% smaller output than raw mode

**Step 3 (Optional): Query with raw timeseries**
```bash
# Only use --raw for full timeseries data (20x more tokens)
python3 scripts/query_dashboard.py \
  --dashboard-id "abc-123-def" \
  --raw \
  --output /tmp/dashboard_raw.json
```

### Alternative Workflow: Individual Metrics

Use when no relevant dashboard exists or when querying specific components.

**Step 1: Query metrics**
```bash
python3 scripts/query_datadog.py \
  --components "api-gateway,database" \
  --incident-time "now" \
  --metrics "cpu,memory,error_rate,rps" \
  --tag-type "service" \
  --output /tmp/metrics.json
```

Key parameters:
- `--components`: Service/component names (required)
- `--tag-type`: Tag type for filtering (default: "service", also: host, instance, container_name)
- `--incident-time`: Timestamp or relative time ("30m ago", "now")
- `--before`/`--after`: Time window in minutes (default: 30)

Consult `references/common_metrics.md` for supported metrics.

**Step 2: Analyze metrics** (if analyze_metrics.py exists)
```bash
python3 scripts/analyze_metrics.py /tmp/metrics.json \
  --output incident_report.md
```

Generates markdown report with:
- Anomaly detection (CRITICAL/HIGH/MEDIUM severity)
- Statistics (min, max, avg, median, stdev)
- Actionable recommendations

## Usage Guidelines

### Decision Making

**Prefer dashboard queries when:**
- User mentions a dashboard name
- Investigating general issues or service health
- Token efficiency matters (analyze mode saves ~95%)

**Use individual metrics when:**
- No relevant dashboard exists
- Querying specific component + metric
- Quick spot-check needed

**Tag type selection:**
- `host`: User mentions "host", "node", "server", "ubuntu"
- `service`: User mentions "service", "application", "app" (default)
- `container_name`: User mentions "container", "docker"
- `instance`: User mentions "instance", "EC2", "VM"

**Time windows:**
- Short (15 min): Real-time monitoring, quick checks
- Standard (30 min): Active incident investigation (default)
- Extended (60+ min): Post-incident analysis, trends

### Response Pattern

When presenting results:
1. Read JSON output from scripts
2. Highlight anomalies with severity levels
3. Present key statistics clearly
4. Provide actionable recommendations

Consult `references/examples.md` for detailed example interactions and decision trees

## Best Practices

- Ask for component names if not provided
- Use relative time formats ("30m ago", "1h ago") when timestamp not specified
- Default to all metrics (cpu,memory,error_rate,rps) for comprehensive view
- Consult `references/common_metrics.md` when user asks about specific metrics
- Remind user to set DD_API_KEY, DD_APP_KEY, and DD_SITE env vars if authentication errors occur

## Setup

Require environment variables:
```bash
export DD_API_KEY="your_api_key"
export DD_APP_KEY="your_app_key"
export DD_SITE="datadoghq.com"  # Optional, default: datadoghq.eu
```

Obtain keys from Datadog: Organization Settings > API Keys / Application Keys

## Troubleshooting

**Authentication failed:**
- Verify DD_API_KEY and DD_APP_KEY are set correctly

**No data found:**
- Check component name matches Datadog tags
- Verify tag-type is correct (service, host, container_name, instance)
- Consult `references/common_metrics.md` for naming conventions

**Rate limit exceeded:**
- Wait 60 seconds before retrying
- Reduce number of components or time window

## Bundled Resources

**scripts/**
- `query_dashboard.py` - Query dashboard widgets with analyze mode
- `query_datadog.py` - Query individual metrics
- `analyze_metrics.py` - Generate incident reports (if exists)

**references/**
- `common_metrics.md` - Comprehensive metrics documentation by category
- `examples.md` - Detailed usage examples and decision trees
