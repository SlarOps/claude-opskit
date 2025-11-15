#!/usr/bin/env python3
"""
Query Datadog dashboard and execute all widget queries.

This script fetches a Datadog dashboard and executes all widget queries,
providing a comprehensive view of the metrics that engineers have already
curated and analyzed.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import urllib.request
import urllib.parse
import urllib.error


class DatadogDashboardQuery:
    """Query Datadog dashboard and execute widget queries."""

    def __init__(self, api_key: str, app_key: str, site: str = 'datadoghq.eu'):
        """Initialize Datadog API client.

        Args:
            api_key: Datadog API key
            app_key: Datadog application key
            site: Datadog site (default: datadoghq.eu, can be datadoghq.com)
        """
        self.api_key = api_key
        self.app_key = app_key
        self.base_url = f"https://api.{site}"

    def _make_request(self, endpoint: str, method: str = 'GET') -> Dict:
        """Make a request to Datadog API.

        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)

        Returns:
            Dict with API response
        """
        url = f"{self.base_url}{endpoint}"
        req = urllib.request.Request(url, method=method)
        req.add_header('DD-API-KEY', self.api_key)
        req.add_header('DD-APPLICATION-KEY', self.app_key)
        req.add_header('Content-Type', 'application/json')

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise Exception(f"Datadog API error: {e.code} - {error_body}")

    def list_dashboards(self) -> List[Dict]:
        """List all dashboards in the account.

        Returns:
            List of dashboard summaries
        """
        result = self._make_request('/api/v1/dashboard')
        return result.get('dashboards', [])

    def get_dashboard(self, dashboard_id: str) -> Dict:
        """Get dashboard definition by ID.

        Args:
            dashboard_id: Dashboard ID

        Returns:
            Dict with dashboard definition
        """
        return self._make_request(f'/api/v1/dashboard/{dashboard_id}')

    def search_dashboard(self, query: str) -> List[Dict]:
        """Search for dashboards by name.

        Args:
            query: Search query (dashboard name)

        Returns:
            List of matching dashboards
        """
        dashboards = self.list_dashboards()
        query_lower = query.lower()
        return [
            d for d in dashboards
            if query_lower in d.get('title', '').lower()
        ]

    def extract_widget_queries(self, dashboard: Dict) -> List[Dict]:
        """Extract all queries from dashboard widgets.

        Args:
            dashboard: Dashboard definition

        Returns:
            List of widget query information
        """
        widgets = []
        widget_list = dashboard.get('widgets', [])

        for idx, widget in enumerate(widget_list):
            widget_info = {
                'index': idx,
                'id': widget.get('id'),
                'definition': widget.get('definition', {}),
                'queries': []
            }

            definition = widget.get('definition', {})
            widget_type = definition.get('type', 'unknown')
            widget_info['type'] = widget_type
            widget_info['title'] = definition.get('title', f'Widget {idx}')

            # Extract queries based on widget type
            if widget_type == 'timeseries':
                requests = definition.get('requests', [])
                for req in requests:
                    if 'q' in req:
                        widget_info['queries'].append(req['q'])
                    if 'queries' in req:
                        for q in req['queries']:
                            if 'query' in q:
                                widget_info['queries'].append(q['query'])

            elif widget_type == 'query_value':
                requests = definition.get('requests', [])
                for req in requests:
                    if 'q' in req:
                        widget_info['queries'].append(req['q'])
                    if 'queries' in req:
                        for q in req['queries']:
                            if 'query' in q:
                                widget_info['queries'].append(q['query'])

            elif widget_type == 'toplist':
                requests = definition.get('requests', [])
                for req in requests:
                    if 'q' in req:
                        widget_info['queries'].append(req['q'])
                    if 'queries' in req:
                        for q in req['queries']:
                            if 'query' in q:
                                widget_info['queries'].append(q['query'])

            elif widget_type == 'heatmap':
                requests = definition.get('requests', [])
                for req in requests:
                    if 'q' in req:
                        widget_info['queries'].append(req['q'])

            # Add more widget types as needed

            if widget_info['queries']:
                widgets.append(widget_info)

        return widgets

    def analyze_series(self, series: List[Dict]) -> Dict:
        """Analyze series data and return statistics instead of raw data.

        Args:
            series: List of series data from Datadog

        Returns:
            Dict with analyzed statistics
        """
        analysis = {
            'series_count': len(series),
            'series_data': []
        }

        for s in series:
            pointlist = s.get('pointlist', [])
            if not pointlist:
                continue

            # Extract values (ignore None/null values)
            values = [p[1] for p in pointlist if p[1] is not None]

            if not values:
                continue

            series_info = {
                'metric': s.get('metric', 'unknown'),
                'scope': s.get('scope', ''),
                'tag_set': s.get('tag_set', []),
                'display_name': s.get('display_name', ''),
                'statistics': {
                    'min': round(min(values), 2),
                    'max': round(max(values), 2),
                    'avg': round(sum(values) / len(values), 2),
                    'latest': round(values[-1], 2),
                    'first': round(values[0], 2),
                    'data_points': len(values)
                }
            }

            # Detect anomalies (simple threshold-based)
            avg_val = series_info['statistics']['avg']
            latest_val = series_info['statistics']['latest']

            # Check if latest value is significantly different from average
            if avg_val > 0:
                change_pct = ((latest_val - avg_val) / avg_val) * 100
                if abs(change_pct) > 20:  # More than 20% change
                    series_info['anomaly'] = {
                        'detected': True,
                        'change_percent': round(change_pct, 2),
                        'severity': 'HIGH' if abs(change_pct) > 50 else 'MEDIUM'
                    }

            analysis['series_data'].append(series_info)

        return analysis

    def execute_query(self, query: str, from_ts: int, to_ts: int) -> Dict:
        """Execute a metric query.

        Args:
            query: Metric query string
            from_ts: Start timestamp (Unix seconds)
            to_ts: End timestamp (Unix seconds)

        Returns:
            Dict with query results
        """
        url = f"{self.base_url}/api/v1/query"
        params = {
            'query': query,
            'from': from_ts,
            'to': to_ts
        }

        url_with_params = f"{url}?{urllib.parse.urlencode(params)}"

        req = urllib.request.Request(url_with_params)
        req.add_header('DD-API-KEY', self.api_key)
        req.add_header('DD-APPLICATION-KEY', self.app_key)

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise Exception(f"Datadog API error: {e.code} - {error_body}")

    def query_dashboard_widgets(
        self,
        dashboard_id: str,
        from_time: datetime,
        to_time: datetime,
        analyze: bool = True
    ) -> Dict:
        """Query all widgets in a dashboard.

        Args:
            dashboard_id: Dashboard ID
            from_time: Start time for queries
            to_time: End time for queries
            analyze: If True, analyze series data instead of returning raw data (default: True)

        Returns:
            Dict with dashboard and widget query results
        """
        print(f"Fetching dashboard: {dashboard_id}")
        dashboard = self.get_dashboard(dashboard_id)

        dashboard_title = dashboard.get('title', 'Unknown')
        dashboard_desc = dashboard.get('description', '')

        print(f"Dashboard: {dashboard_title}")
        if dashboard_desc:
            print(f"Description: {dashboard_desc}")
        print()

        # Extract widgets and queries
        widgets = self.extract_widget_queries(dashboard)
        print(f"Found {len(widgets)} widgets with queries")
        print()

        # Execute queries
        from_ts = int(from_time.timestamp())
        to_ts = int(to_time.timestamp())

        results = {
            'metadata': {
                'dashboard_id': dashboard_id,
                'dashboard_title': dashboard_title,
                'dashboard_description': dashboard_desc,
                'time_range': {
                    'from': from_time.isoformat(),
                    'to': to_time.isoformat(),
                    'from_ts': from_ts,
                    'to_ts': to_ts
                },
                'total_widgets': len(widgets)
            },
            'widgets': []
        }

        total_queries = sum(len(w['queries']) for w in widgets)
        successful_queries = 0
        failed_queries = 0

        for widget in widgets:
            widget_result = {
                'index': widget['index'],
                'id': widget['id'],
                'type': widget['type'],
                'title': widget['title'],
                'queries': []
            }

            print(f"Widget {widget['index']}: {widget['title']} ({widget['type']})")

            for query in widget['queries']:
                print(f"  Query: {query}")

                try:
                    result = self.execute_query(query, from_ts, to_ts)

                    if result.get('series'):
                        # Analyze or save raw data based on mode
                        if analyze:
                            analysis = self.analyze_series(result['series'])
                            widget_result['queries'].append({
                                'query': query,
                                'status': 'success',
                                'analysis': analysis
                            })
                            print(f"    ✓ Success ({analysis['series_count']} series analyzed)")
                        else:
                            widget_result['queries'].append({
                                'query': query,
                                'status': 'success',
                                'series': result['series']
                            })
                            print(f"    ✓ Success ({len(result['series'])} series)")
                        successful_queries += 1
                    else:
                        widget_result['queries'].append({
                            'query': query,
                            'status': 'no_data'
                        })
                        print(f"    ✗ No data")

                except Exception as e:
                    widget_result['queries'].append({
                        'query': query,
                        'status': 'error',
                        'error': str(e)
                    })
                    print(f"    ✗ Error: {str(e)}")
                    failed_queries += 1

            results['widgets'].append(widget_result)
            print()

        # Print summary
        print(f"{'='*60}")
        print(f"Query Summary:")
        print(f"  Total widgets: {len(widgets)}")
        print(f"  Total queries: {total_queries}")
        print(f"  Successful: {successful_queries}")
        print(f"  Failed: {failed_queries}")
        print(f"{'='*60}\n")

        results['metadata']['query_summary'] = {
            'total_queries': total_queries,
            'successful': successful_queries,
            'failed': failed_queries
        }

        return results


def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string in various formats."""
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%dT%H:%M',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    # Try parsing relative time (e.g., "30m ago", "2h ago", "1h ago")
    if 'ago' in dt_str:
        parts = dt_str.replace('ago', '').strip().split()
        if len(parts) >= 1:
            # Handle "1h ago" format
            time_str = parts[0]
            # Extract number and unit
            import re
            match = re.match(r'(\d+)([a-z]+)', time_str)
            if match:
                amount = int(match.group(1))
                unit = match.group(2)

                if unit in ['m', 'min', 'minute', 'minutes']:
                    return datetime.now() - timedelta(minutes=amount)
                elif unit in ['h', 'hr', 'hour', 'hours']:
                    return datetime.now() - timedelta(hours=amount)
                elif unit in ['d', 'day', 'days']:
                    return datetime.now() - timedelta(days=amount)

    raise ValueError(f"Unable to parse datetime: {dt_str}")


def main():
    parser = argparse.ArgumentParser(
        description='Query Datadog dashboard and execute widget queries'
    )

    parser.add_argument(
        '--dashboard-id',
        type=str,
        help='Dashboard ID to query'
    )

    parser.add_argument(
        '--search',
        type=str,
        help='Search for dashboard by name'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List all dashboards'
    )

    parser.add_argument(
        '--from-time',
        type=str,
        default='1h ago',
        help='Start time for queries (YYYY-MM-DD HH:MM:SS, "1h ago", default: 1h ago)'
    )

    parser.add_argument(
        '--to-time',
        type=str,
        default='now',
        help='End time for queries (YYYY-MM-DD HH:MM:SS, "now", default: now)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: stdout)'
    )

    parser.add_argument(
        '--analyze',
        action='store_true',
        default=True,
        help='Analyze series data instead of returning raw timeseries (default: True, saves tokens)'
    )

    parser.add_argument(
        '--raw',
        action='store_true',
        help='Return raw timeseries data instead of analyzed summary (uses more tokens)'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        default=os.getenv('DD_API_KEY'),
        help='Datadog API key (or set DD_API_KEY env var)'
    )

    parser.add_argument(
        '--app-key',
        type=str,
        default=os.getenv('DD_APP_KEY'),
        help='Datadog application key (or set DD_APP_KEY env var)'
    )

    parser.add_argument(
        '--site',
        type=str,
        default=os.getenv('DD_SITE', 'datadoghq.eu'),
        help='Datadog site (default: datadoghq.eu)'
    )

    args = parser.parse_args()

    # Validate credentials
    if not args.api_key or not args.app_key:
        print("Error: Datadog API credentials required", file=sys.stderr)
        print("Set DD_API_KEY and DD_APP_KEY environment variables", file=sys.stderr)
        print("Or use --api-key and --app-key arguments", file=sys.stderr)
        sys.exit(1)

    client = DatadogDashboardQuery(args.api_key, args.app_key, args.site)

    # List dashboards
    if args.list:
        print("Fetching dashboards...")
        dashboards = client.list_dashboards()
        print(f"\nFound {len(dashboards)} dashboards:\n")
        for db in dashboards:
            print(f"  {db['id']}: {db.get('title', 'Untitled')}")
            if db.get('description'):
                print(f"    Description: {db['description']}")
            print()
        sys.exit(0)

    # Search dashboards
    if args.search:
        print(f"Searching for dashboards matching: {args.search}")
        dashboards = client.search_dashboard(args.search)

        if not dashboards:
            print("No dashboards found matching the query")
            sys.exit(1)

        print(f"\nFound {len(dashboards)} matching dashboard(s):\n")
        for db in dashboards:
            print(f"  {db['id']}: {db.get('title', 'Untitled')}")
            if db.get('description'):
                print(f"    Description: {db['description']}")
            print()

        if len(dashboards) == 1:
            args.dashboard_id = dashboards[0]['id']
            print(f"Using dashboard: {args.dashboard_id}\n")
        else:
            print("Multiple dashboards found. Please specify --dashboard-id")
            sys.exit(0)

    # Query dashboard
    if not args.dashboard_id:
        print("Error: --dashboard-id or --search required", file=sys.stderr)
        print("Use --list to see available dashboards", file=sys.stderr)
        sys.exit(1)

    # Parse time range
    if args.from_time.lower() == 'now':
        from_time = datetime.now()
    else:
        from_time = parse_datetime(args.from_time)

    if args.to_time.lower() == 'now':
        to_time = datetime.now()
    else:
        to_time = parse_datetime(args.to_time)

    # Determine analyze mode (analyze by default unless --raw is specified)
    analyze_mode = not args.raw

    # Query dashboard widgets
    results = client.query_dashboard_widgets(args.dashboard_id, from_time, to_time, analyze=analyze_mode)

    # Output results
    output_json = json.dumps(results, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
        print(f"✓ Results saved to: {args.output}")
    else:
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(output_json)


if __name__ == '__main__':
    main()
