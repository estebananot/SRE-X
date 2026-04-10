# SRE Copilot - AI-Powered Incident Triage Agent

An AI-powered SRE Copilot that automates incident triage and diagnosis, reducing MTTR from ~45 minutes to seconds through structured chain-of-thought reasoning.

## Architecture

```
[Slack / CLI] -> [Bot Handler] -> [SRE Agent (LangGraph ReAct)] -> [OpenRouter LLM]
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

### Option A: Docker (Recommended)

```bash
# 1. Clone the repo
git clone https://github.com/estebananot/SRE-X.git
cd SRE-X

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys (at minimum OPENROUTER_API_KEY)

# 3. Build and run the demo
docker compose run sre-copilot python scripts/run_demo.py

# 4. Or launch the Slack bot
docker compose up sre-copilot
```

The Docker image includes all dependencies and downloads the open-source log datasets automatically during build. The Docker socket is mounted so the agent can inspect and manage containers on the host.

### Option B: Local Installation

```bash
# 1. Clone the repo
git clone https://github.com/estebananot/SRE-X.git
cd SRE-X

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Download open-source logs (HDFS, Spark, Hadoop, Zookeeper)
python scripts/download_logs.py

# 5. Run the demo
python scripts/run_demo.py
```

### Environment Variables

Required in `.env`:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | API key from https://openrouter.ai/keys | Yes |
| `OPENROUTER_MODEL` | Model to use (default: `openai/gpt-4o-mini`) | No |
| `SLACK_BOT_TOKEN` | Slack bot token (`xoxb-...`) | For Slack bot |
| `SLACK_APP_TOKEN` | Slack app-level token (`xapp-...`) | For Slack bot |
| `SLACK_SIGNING_SECRET` | Slack signing secret | For Slack bot |

## Usage

### CLI Mode

```bash
python scripts/cli.py
```

Commands:
- `alerts` - List active alerts
- `triage <alert_id>` - Run full triage (e.g., `triage alert-001`)
- `analyze <service>` - Analyze a service (e.g., `analyze payment-api`)
- `chat <message>` - Free-form question
- `quit` - Exit

### Docker CLI

```bash
docker compose run sre-copilot-cli
```

### Slack Bot

Set up your Slack app at https://api.slack.com/apps:

1. Create a new app (From scratch)
2. Enable **Socket Mode** (Settings -> Socket Mode)
3. Add **Bot Token Scopes**: `chat:write`, `commands`, `app_mentions:read`, `channels:read`, `groups:read`, `im:read`, `mpim:read`
4. Add **Slash Commands**: `/alerts`, `/triage`, `/analyze`, `/incident`
5. Enable **Interactivity & Shortcuts** (Request URL: any placeholder)
6. Subscribe to event: `app_mentions:read`
7. Install app to workspace
8. Copy tokens to `.env`

Run with Docker:
```bash
docker compose up sre-copilot
```

Or locally:
```bash
python bot/slack_bot.py
```

### Incident Simulation (requires Docker)

```bash
python scripts/simulate_incident.py setup     # Create demo containers
python scripts/simulate_incident.py memory    # Simulate OOM incident
python scripts/simulate_incident.py disk      # Simulate disk full
python scripts/simulate_incident.py crashloop # Simulate crash loop
python scripts/simulate_incident.py cleanup   # Remove demo containers
python scripts/simulate_incident.py full      # Setup + memory scenario
```

## Project Structure

```
sre-copilot/
  agent/
    prompts.py          # SRE system prompt with structured reasoning
    sre_agent.py         # LangGraph ReAct agent
    tools.py             # 9 LangChain tools (logs, metrics, alerts, Docker, open-source logs)
    triage.py            # IncidentTriage orchestrator
  bot/
    slack_bot.py         # Slack bot with Socket Mode
  config/
    settings.py          # Pydantic settings from .env
  data/
    sample_alerts.json   # 6 PagerDuty-style alerts
    sample_logs.json     # 22 log entries across 6 services
    sample_metrics.json  # Time-series metrics for 6 services
    raw_logs/            # Real production logs from LogPAI/Loghub
  scripts/
    cli.py               # Interactive CLI
    run_demo.py           # End-to-end demo with MTTR comparison
    simulate_incident.py  # Docker-based incident simulation
    download_logs.py      # Download open-source logs
    test_connection.py    # Test OpenRouter connection
  tools/
    data_sources.py       # Unified data source manager
    docker_tool.py         # Docker SDK wrapper
    log_parser.py          # Parser for HDFS, Spark, Hadoop, Zookeeper logs
  Dockerfile              # Multi-stage Docker build
  docker-compose.yml      # Docker Compose for one-command deployment
  requirements.txt        # Python dependencies
  .env.example            # Environment template
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

- **Python 3.12+** with LangChain/LangGraph (ReAct agent)
- **OpenRouter API** (GPT-4o-mini) for LLM inference
- **Slack Bolt** for Slack integration with Socket Mode
- **Docker SDK** for container inspection and remediation
- **LogPAI/Loghub** for real production log data
- **Pydantic** for settings and data validation

## License

MIT