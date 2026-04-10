import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from agent.triage import IncidentTriage

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main():
    triage = IncidentTriage()

    print("=" * 60)
    print("  SRE Copilot - Incident Triage Agent")
    print("=" * 60)
    print()
    print("Commands:")
    print("  alerts              - List all active alerts")
    print("  triage <alert_id>   - Run full triage on an alert (e.g. triage alert-001)")
    print("  analyze <service>  - Analyze a service (e.g. analyze payment-api)")
    print("  chat <message>     - Free-form question to the SRE agent")
    print("  quit                - Exit")
    print()

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        if user_input.lower() == "alerts":
            alerts = triage.list_alerts()
            print(f"\nActive Alerts ({len(alerts)}):")
            print("-" * 60)
            for a in alerts:
                marker = "[CRITICAL]" if a["severity"] == "critical" else "[WARNING]"
                print(f'{marker} [{a["id"]}] {a["service"]}: {a["title"]}')
            continue

        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""

        if command == "triage" and argument:
            print(f"\n>> Running triage for alert: {argument}...")
            print("-" * 60)
            try:
                result = triage.triage_alert(argument)
                if "error" in result:
                    print(f"ERROR: {result['error']}")
                else:
                    print(f"  Triage time: {result['triage_time_seconds']}s")
                    print(f"  Service: {result['service']} | Severity: {result['severity']}")
                    print()
                    print(result["diagnosis"])
            except Exception as e:
                print(f"ERROR: {e}")

        elif command == "analyze" and argument:
            print(f"\n>> Analyzing service: {argument}...")
            print("-" * 60)
            try:
                result = triage.triage_service(argument)
                if "error" in result:
                    print(f"❌ {result['error']}")
                else:
                    print(f"⏱  Analysis time: {result['triage_time_seconds']}s")
                    print()
                    print(result["diagnosis"])
            except Exception as e:
                print(f"ERROR: {e}")

        elif command == "chat":
            if not argument:
                argument = "What's the current status of our infrastructure?"
            print(f"\n>> Thinking...")
            print("-" * 60)
            try:
                result = triage.interactive(argument)
                print(result["response"])
            except Exception as e:
                print(f"ERROR: {e}")

        else:
            print("Unknown command. Use: alerts, triage <id>, analyze <service>, chat <message>, quit")


if __name__ == "__main__":
    main()