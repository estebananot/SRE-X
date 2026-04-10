import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from agent.triage import IncidentTriage


SEPARATOR = "=" * 70


def print_header(title: str):
    print()
    print(SEPARATOR)
    print(f"  {title}")
    print(SEPARATOR)
    print()


def print_step(step: str, text: str):
    print(f"[{step}] {text}")


def run_demo():
    triage = IncidentTriage()

    print_header("SRE COPILOT - END-TO-END DEMO")
    print("This demo shows how the SRE Copilot agent reduces MTTR")
    print("by automating incident triage and diagnosis.")
    print()
    print("Scenario: Payment API experiences OOM Kill incident")
    print("Data sources: Simulated logs, metrics, alerts + real Docker containers")

    print_header("STEP 1: WITHOUT SRE COPILOT (Manual Triage)")

    print_step("1.1", "Engineer receives alert: 'OOMKill Detected - Container Terminated'")
    print_step("1.2", "Engineer manually checks logs, metrics, dashboards...")
    print_step("1.3", "Engineer investigates multiple services to find root cause...")
    print_step("1.4", "Engineer cross-references data and forms hypothesis...")
    print_step("1.5", "Engineer writes remediation plan and gets approval...")

    manual_mttr_minutes = 45
    print(f"\n  >>> MANUAL MTTR: ~{manual_mttr_minutes} minutes (industry average for P1 incidents)")
    print("  >>> Steps: Alert received (2m) -> Data gathering (15m) -> Root cause (20m) -> Remediation (8m)")

    print_header("STEP 2: WITH SRE COPILOT (Automated Triage)")

    alerts = triage.list_alerts()
    print_step("2.1", f"Agent discovers {len(alerts)} active alerts:")
    for a in alerts:
        severity = a["severity"].upper()
        marker = "[CRITICAL]" if a["severity"] == "critical" else "[WARNING]"
        print(f"       {marker} {a['id']}: {a['service']} - {a['title']}")

    alert_id = "alert-001"
    print()
    print_step("2.2", f"Running automated triage on {alert_id}...")
    start = time.time()

    result = triage.triage_alert(alert_id)

    agent_time = time.time() - start

    print()
    print_step("2.3", f"Agent completed triage in {agent_time:.1f}s")
    print()
    print("-" * 70)
    diagnosis = result["diagnosis"]
    if len(diagnosis) > 3000:
        diagnosis = diagnosis[:3000] + "\n... [truncated]"
    print(diagnosis)
    print("-" * 70)

    print_header("STEP 3: ANALYZE REAL OPEN-SOURCE LOGS")

    print_step("3.1", "Agent analyzing real HDFS production logs from LogPAI/Loghub...")
    start2 = time.time()
    os_result = triage.interactive(
        "List the available open-source log sources, then show me WARN level logs from Zookeeper and analyze what kind of connection issues are occurring.",
        thread_id="demo-os-logs",
    )
    os_time = time.time() - start2
    print()
    print(f"  Analysis completed in {os_time:.1f}s")
    print()
    print("-" * 70)
    os_diag = os_result["response"]
    if len(os_diag) > 2000:
        os_diag = os_diag[:2000] + "\n... [truncated]"
    print(os_diag)
    print("-" * 70)

    print_header("STEP 4: MTTR COMPARISON")

    agent_mttr_minutes = agent_time / 60
    improvement = ((manual_mttr_minutes - agent_mttr_minutes) / manual_mttr_minutes) * 100

    print(f"""
  +-----------------------------------+------------------+
  | Metric                            | Value            |
  +-----------------------------------+------------------+
  | Manual MTTR (human engineer)      | {manual_mttr_minutes:>15}m |
  | SRE Copilot MTTR (automated)      | {agent_mttr_minutes:>14.1f}m |
  | MTTR Reduction                    | {improvement:>14.1f}% |
  | Time Saved per Incident            | {manual_mttr_minutes - agent_mttr_minutes:>14.1f}m |
  +-----------------------------------+------------------+

  On-call engineers save ~{manual_mttr_minutes - agent_mttr_minutes:.0f} minutes per P1 incident.
  At an average of 5 P1 incidents/month, that's ~{(manual_mttr_minutes - agent_mttr_minutes) * 5 / 60:.0f} hours saved/month.
""")

    print_header("STEP 5: DOCKER CONTAINER INSPECTION")

    from tools.docker_tool import DockerClient
    dc = DockerClient()
    if dc.is_available():
        containers = dc.list_containers(all_containers=True)
        print_step("5.1", f"Found {len(containers)} Docker containers on this host:")
        for c in containers:
            status = "[RUNNING]" if c["status"] == "running" else "[STOPPED]"
            print(f"       {status} {c['name']} ({c['image']})")

        if containers:
            name = containers[0]["name"]
            print()
            print_step("5.2", f"Inspecting container: {name}")
            info = dc.inspect_container(name)
            if info:
                print(f"       Status: {info['status']}")
                print(f"       Image: {info['image']}")
                print(f"       OOM Killed: {info.get('oom_killed', 'N/A')}")
                print(f"       Restart Count: {info.get('restart_count', 'N/A')}")
    else:
        print_step("5.1", "Docker not available on this host - skipping container inspection")

    print_header("DEMO COMPLETE")
    print("""
  The SRE Copilot demonstrates:
  1. Automated incident triage with chain-of-thought reasoning
  2. Multi-source data correlation (logs, metrics, alerts, Docker)
  3. Root cause diagnosis with evidence-based analysis
  4. Actionable remediation suggestions with risk assessment
  5. Real production log analysis (LogPAI/Loghub)
  6. Docker container inspection and remediation capabilities
  7. MTTR reduction from 45 minutes to seconds

  Try it yourself:
    CLI:  python scripts/cli.py
    Slack: /triage alert-001, /alerts, /analyze payment-api
    Full:  python scripts/simulate_incident.py full
""")


if __name__ == "__main__":
    run_demo()