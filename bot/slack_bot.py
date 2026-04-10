import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("sre-copilot")

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from slack_bolt.app import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from agent.triage import IncidentTriage
from config.settings import settings


def format_severity_emoji(severity: str) -> str:
    mapping = {"critical": "red_circle", "warning": "large_yellow_circle", "info": "large_blue_circle"}
    return mapping.get(severity, "white_circle")


def format_status_emoji(status: str) -> str:
    mapping = {"critical": "red_circle", "degraded": "large_yellow_circle", "down": "red_circle", "stable": "large_green_circle"}
    return mapping.get(status, "white_circle")


triage = IncidentTriage()

app = App(token=settings.slack_bot_token, signing_secret=settings.slack_signing_secret)


@app.middleware
def log_all_requests(logger, body, next):
    logger.info(f"Incoming request: {body.get('type', 'unknown')} / {body.get('event', {}).get('type', 'no-event')}")
    next()


@app.command("/alerts")
def handle_alerts(ack, say, command):
    ack()
    logger.info(f"Received /alerts command from {command.get('user_name', 'unknown')}")
    alerts = triage.list_alerts()

    if not alerts:
        say(text="No active alerts. All systems operational.")
        return

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Active Alerts"},
        },
        {"type": "divider"},
    ]

    for a in alerts:
        severity = a["severity"].upper()
        marker = "[CRITICAL]" if a["severity"] == "critical" else "[WARNING]"
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{marker}* `{a['id']}` *{a['service']}* - {a['title']}",
            },
        })
        blocks.append({
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": f"_{a['description'][:200]}_"},
            ],
        })

    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": "Use `/triage <alert_id>` to analyze an alert. Example: `/triage alert-001`"},
        ],
    })

    say(text=f"Active Alerts ({len(alerts)})", blocks=blocks)


@app.command("/triage")
def handle_triage(ack, say, command):
    ack()
    alert_id = command["text"].strip()
    logger.info(f"Received /triage command with alert_id={alert_id}")

    if not alert_id:
        say(text="Usage: `/triage <alert_id>` - Example: `/triage alert-001`")
        return

    say(text=f"Running triage for `{alert_id}`... This may take a few seconds.")

    try:
        result = triage.triage_alert(alert_id)
        if "error" in result:
            say(text=f"Error: {result['error']}")
            return

        severity = result.get("severity", "unknown")
        marker = "[CRITICAL]" if severity == "critical" else "[WARNING]"

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"Incident Triage: {alert_id}"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Service:* {result['service']}"},
                    {"type": "mrkdwn", "text": f"*Severity:* {marker} {severity}"},
                    {"type": "mrkdwn", "text": f"*Triage Time:* {result['triage_time_seconds']}s"},
                ],
            },
            {"type": "divider"},
        ]

        diagnosis_text = result["diagnosis"]
        max_len = 2900
        if len(diagnosis_text) > max_len:
            diagnosis_text = diagnosis_text[:max_len] + "\n... _(truncated)_"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": diagnosis_text},
        })

        say(text=f"Triage complete for {alert_id}", blocks=blocks)

    except Exception as e:
        say(text=f"Error during triage: {e}")


@app.command("/analyze")
def handle_analyze(ack, say, command):
    ack()
    service = command["text"].strip()
    logger.info(f"Received /analyze command with service={service}")

    if not service:
        say(text="Usage: `/analyze <service>` - Example: `/analyze payment-api`")
        return

    say(text=f"Analyzing `{service}`... This may take a few seconds.")

    try:
        result = triage.triage_service(service)
        if "error" in result:
            say(text=f"Error: {result['error']}")
            return

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"Service Analysis: {service}"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Analysis Time:* {result['triage_time_seconds']}s"},
                ],
            },
            {"type": "divider"},
        ]

        diagnosis_text = result["diagnosis"]
        max_len = 2900
        if len(diagnosis_text) > max_len:
            diagnosis_text = diagnosis_text[:max_len] + "\n... _(truncated)_"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": diagnosis_text},
        })

        say(text=f"Analysis complete for {service}", blocks=blocks)

    except Exception as e:
        say(text=f"Error during analysis: {e}")


@app.command("/incident")
def handle_incident(ack, say, command):
    ack()
    message = command["text"].strip()
    logger.info(f"Received /incident command with message={message[:50]}")

    if not message:
        say(text="Usage: `/incident <description>` - Example: `/incident payment-api is returning 502 errors`")
        return

    say(text=f"Processing incident report...")

    try:
        result = triage.interactive(message, thread_id=f"incident-{command['channel_name']}")
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "SRE Copilot Analysis"},
            },
            {"type": "divider"},
        ]

        diagnosis_text = result["response"]
        max_len = 2900
        if len(diagnosis_text) > max_len:
            diagnosis_text = diagnosis_text[:max_len] + "\n... _(truncated)_"

        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": diagnosis_text},
        })

        say(text="SRE Copilot response", blocks=blocks)

    except Exception as e:
        say(text=f"Error: {e}")


@app.event("app_mention")
def handle_mention(event, say):
    text = event.get("text", "")
    logger.info(f"Received app_mention event: {text[:100]}")
    mention_text = text.split(">", 1)[-1].strip() if ">" in text else text.strip()

    if not mention_text:
        say(text="I'm the SRE Copilot! Use commands like:\n- `/alerts` - List active alerts\n- `/triage <alert_id>` - Analyze an alert\n- `/analyze <service>` - Analyze a service\n- `/incident <description>` - Report an incident")
        return

    try:
        result = triage.interactive(mention_text, thread_id=f"mention-{event.get('channel', 'default')}")

        diagnosis_text = result["response"]
        max_len = 2900
        if len(diagnosis_text) > max_len:
            diagnosis_text = diagnosis_text[:max_len] + "\n... _(truncated)_"

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "SRE Copilot"},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": diagnosis_text},
            },
        ]

        say(text="SRE Copilot response", blocks=blocks)

    except Exception as e:
        say(text=f"Error: {e}")


if __name__ == "__main__":
    print("Starting SRE Copilot Slack Bot (Socket Mode)...")
    print(f"Bot token: {settings.slack_bot_token[:15]}...")
    print(f"App token: {settings.slack_app_token[:15]}...")

    handler = SocketModeHandler(app, settings.slack_app_token)
    handler.start()