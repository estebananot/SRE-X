import json
import time

from agent.sre_agent import run_sre_agent, run_sre_agent_stream
from tools.data_sources import DataSourceManager


class IncidentTriage:
    def __init__(self):
        self._ds = DataSourceManager()

    def triage_alert(self, alert_id: str) -> dict:
        alerts = self._ds.get_alerts()
        alert = next((a for a in alerts if a.get("id") == alert_id), None)
        if not alert:
            return {"error": f"Alert '{alert_id}' not found. Available: {[a['id'] for a in alerts]}"}

        service = alert["service"]
        message = (
            f"I received this critical alert:\n\n"
            f"**Alert**: {alert['title']}\n"
            f"**Service**: {service}\n"
            f"**Severity**: {alert['severity']}\n"
            f"**Description**: {alert['description']}\n\n"
            f"Please analyze this incident following your structured reasoning process. "
            f"Start by gathering data about the {service} service, then diagnose the root cause "
            f"and suggest remediation steps."
        )

        start_time = time.time()
        result = run_sre_agent(message, thread_id=f"incident-{alert_id}")
        elapsed = time.time() - start_time

        ai_message = result["messages"][-1].content

        return {
            "alert_id": alert_id,
            "service": service,
            "severity": alert["severity"],
            "diagnosis": ai_message,
            "triage_time_seconds": round(elapsed, 2),
            "messages_trace": [
                {"role": msg.type if hasattr(msg, "type") else "unknown", "content": msg.content if hasattr(msg, "content") else str(msg)}
                for msg in result["messages"]
            ],
        }

    def triage_service(self, service: str) -> dict:
        context = self._ds.get_incident_context(service)
        message = (
            f"I'm investigating issues with the **{service}** service. "
            f"Please analyze its current state by gathering logs, metrics, and any active alerts. "
            f"Provide a diagnosis and recommended actions."
        )

        start_time = time.time()
        result = run_sre_agent(message, thread_id=f"service-{service}")
        elapsed = time.time() - start_time

        ai_message = result["messages"][-1].content

        return {
            "service": service,
            "diagnosis": ai_message,
            "triage_time_seconds": round(elapsed, 2),
        }

    def interactive(self, message: str, thread_id: str = "interactive") -> dict:
        start_time = time.time()
        result = run_sre_agent(message, thread_id=thread_id)
        elapsed = time.time() - start_time

        ai_message = result["messages"][-1].content

        return {
            "response": ai_message,
            "response_time_seconds": round(elapsed, 2),
        }

    def list_alerts(self) -> list[dict]:
        return self._ds.get_alerts()