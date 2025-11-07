# Claude Plugins

DevOps plugins for Claude Code.

## Installation

You can register this repository as a Claude Code Plugin marketplace by running the following command in Claude Code:

```
/plugin marketplace add slarops/claude-opskit
```

Then, to install a specific plugin:

1. Select **Browse and install plugins**
2. Select **claude-plugin**
3. Select **datadog-incident-metrics**
4. Select **Install now**

Alternatively, directly install the plugin via:

```
/plugin install datadog-incident-metrics@claude-plugin
```

## Usage

After installing the plugin, you can use the skill by just mentioning it. For instance:

```
"Use the Datadog skill to analyze incident metrics from the last 7 days"
```

## Available Plugins

### datadog-incident-metrics

Query and analyze Datadog incident metrics, including MTTR, incident counts, severity distributions, and more.

**Example usage:**
- "Show me incident metrics for the last 30 days"
- "Analyze MTTR trends by severity"
- "Get incident count grouped by service"

## Repository Structure

```
claude-plugin/
├── .claude-plugin/
│   └── marketplace.json
└── datadog-incident-metrics/
    ├── SKILL.md
    ├── requirements.txt
    ├── references/
    └── scripts/
```

## Contributing

To add new plugins to this marketplace, create a new directory with:
- `SKILL.md` - Plugin documentation and capabilities
- `requirements.txt` - Python dependencies
- `scripts/` - Implementation scripts

Then update `.claude-plugin/marketplace.json` to register the new plugin.

## License

See individual plugin directories for license information.

