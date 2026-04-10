# SRE Copilot - AI-Powered Incident Triage Agent

An AI-powered SRE Copilot that automates incident triage and diagnosis, reducing MTTR from ~45 minutes to seconds through structured chain-of-thought reasoning.

## Architecture

```
[Slack CLI / CLI] -> [Bot Handler] -> [SRE Agent (LangGraph ReAct)] -> [OpenRouter LLM]
                                            |
                        +-------------------+-------------------+
                        |                   |                   |
                  [Simulated Data]    [Real Logs]        [Docker API]
                  (logs, metrics,     (LogPAI/           (inspect,
                   alerts)             Loghub)             restart)
```

## Key Features

- **Structured Chain-of-Thought Reasoning**: Observation -> Hypothesis -> Data Gathering -> Diagnosis -> Remediation
- **Multi-Source Data Correlation**: Logs, metrics, alerts, and real Docker container inspection
- **Real Production Logs**: HDFS, Spark, Hadoop, Zookeeper logs from Stanford's LogPAI/Loghub
- **Docker Integration**: Inspect, restart, and stop containers directly from the agent
- **Slack Integration**: Slash commands (`/alerts`, `/triage`, `/analyze`, `/incident`) and `@mention` support
- **MTTR Reduction**: From ~45min manual to ~16s automated (99.4% reduction)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install langchain langchain-openai langchain-community pydantic python-dotenv docker slack-bolt slack-sdk
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required in `.env`:
- `OPENROUTER_API_KEY` - Get one at https://openrouter.ai/keys
- `OPENROUTER_MODEL` - Default: `openai/gpt-4o-mini`
- `SLACK_BOT_TOKEN` - For Slack integration (optional)
- `SLACK_APP_TOKEN` - For Socket Mode (optional)
- `SLACK_SIGNING_SECRET` - For Slack integration (optional)

### 3. Download Open-Source Logs

```bash
python scripts/download_logs.py
```

Downloads real production logs from HDFS, Spark, Hadoop, and Zookeeper (Stanford LogPAI/Loghub).

### 4. Run the Demo

```bash
python scripts/run_demo.py
```

This runs the full end-to-end demo with MTTR comparison.

### 5. CLI Mode

```bash
python scripts/cli.py
```

Commands:
- `alerts` - List active alerts
- `triage <alert_id>` - Run full triage (e.g., `triage alert-001`)
- `analyze <service>` - Analyze a service (e.g., `analyze payment-api`)
- `chat <message>` - Free-form question
- `quit` - Exit

### 6. Slack Bot

Set up your Slack app at https://api.slack.com/apps:

1. Create a new app (From scratch)
2. Enable **Socket Mode** (Settings -> Socket Mode)
3. Add **Bot Token Scopes**: `chat:write`, `commands`, `app_mentions:read`, `channels:read`, `groups:read`, `im:read`, `mpim:read`
4. Add **Slash Commands**: `/alerts`, `/triage`, `/analyze`, `/incident`
5. Enable **Interactivity & Shortcuts** (Request URL: any placeholder)
6. Subscribe to event: `app_mentions:read`
7. Install app to workspace
8. Copy tokens to `.env`

Run:
```bash
python bot/slack_bot.py
```

### 7. Incident Simulation (requires Docker)

```bash
python scripts/simulate_incident.py setup    # Create demo containers
python scripts/simulate_incident.py memory   # Simulate OOM incident
python scripts/simulate_incident.py disk     # Simulate disk full
python scripts/simulate_incident.py crashloop # Simulate crash loop
python scripts/simulate_incident.py cleanup  # Remove demo containers
python scripts/simulate_incident.py full     # Setup + memory scenario
```

## Project Structure

```
sre-copilot/
  agent/
    prompts.py          # SRE system prompt with structured reasoning
    sre_agent.py        # LangGraph ReAct agent
    tools.py            # 9 LangChain tools (logs, metrics, alerts, Docker, open-source logs)
    triage.py           # IncidentTriage orchestrator
  bot/
    slack_bot.py        # Slack bot with Socket Mode
  config/
    settings.py         # Pydantic settings from .env
  data/
    sample_alerts.json  # 6 PagerDuty-style alerts (OOM, conn pool, upstream, disk, crash loop, db overload)
    sample_logs.json    # 22 log entries across 6 services
    sample_metrics.json # Time-series metrics for 6 services
    raw_logs/           # Real production logs from LogPAI/Loghub (downloaded separately)
  scripts/
    cli.py              # Interactive CLI
    run_demo.py         # End-to-end demo with MTTR comparison
    simulate_incident.py # Docker-based incident simulation
    download_logs.py     # Download open-source logs
    test_connection.py   # Test OpenRouter connection
  tools/
    data_sources.py     # Unified data source manager
    docker_tool.py      # Docker SDK wrapper
    log_parser.py       # Parser for HDFS, Spark, Hadoop, Zookeeper logs
  .env.example
  .gitignore
```

## Agent Reasoning Process

For every incident, the agent follows this structured chain-of-thought:

1. **[SEVERITY]** - Classify criticality and blast radius
2. **[ANALYSIS]** - Step-by-step reasoning with evidence
3. **[ROOT CAUSE]** - Confirmed diagnosis citing logs/metrics/alerts
4. **[ACTIONS]** - Prioritized remediation steps with justification
5. **[RISKS]** - Side effects and trade-offs of recommended actions

## Included Scenarios

| Alert ID | Service | Incident | Root Cause |
|----------|---------|----------|------------|
| alert-001 | payment-api | OOMKill | Memory limit 512Mi too low (92% usage) |
| alert-002 | auth-service | DB Pool Exhausted | 200/200 connections, 47 pending |
| alert-003 | frontend-web | Upstream Failures | payment-api downstream unreachable |
| alert-004 | order-processor | Disk Full | 98% disk usage (49Gi/50Gi) |
| alert-005 | inventory-service | CrashLoopBackOff | Missing ConfigMap |
| alert-006 | db-primary | Too Many Connections | 210 active > 200 max |

## Tech Stack

- **Python 3.11+** with LangChain/LangGraph (ReAct agent)
- **OpenRouter API** (GPT-4o-mini) for LLM inference
- **Slack Bolt** for Slack integration with Socket Mode
- **Docker SDK** for container inspection and remediation
- **LogPAI/Loghub** for real production log data
- **Pydantic** for settings and data validation

## License

MIT