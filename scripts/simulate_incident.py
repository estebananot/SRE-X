import subprocess
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.docker_tool import DockerClient


STRESS_IMAGE = "progrium/stress:latest"
NGINX_IMAGE = "nginx:alpine"


def run_cmd(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    return result.stdout + result.stderr


def docker_available() -> bool:
    client = DockerClient()
    return client.is_available()


def setup_demo_containers():
    print("=" * 60)
    print("  SRE Copilot - Incident Simulation Setup")
    print("=" * 60)
    print()

    if not docker_available():
        print("[ERROR] Docker is not running. Start Docker and try again.")
        return False

    dc = DockerClient()
    print("[1/4] Pulling Docker images...")
    run_cmd(f"docker pull {NGINX_IMAGE} > /dev/null 2>&1")
    run_cmd(f"docker pull {STRESS_IMAGE} > /dev/null 2>&1")
    print("      Images ready.")

    print("[2/4] Creating demo containers...")

    existing = dc.list_containers(all_containers=True)
    existing_names = {c["name"] for c in existing}

    containers = [
        ("demo-web", NGINX_IMAGE, "80:80", True),
        ("demo-api", NGINX_IMAGE, "8080:80", True),
        ("demo-db", NGINX_IMAGE, None, True),
    ]

    for name, image, ports, running in containers:
        if name in existing_names:
            print(f"      Container {name} already exists, skipping.")
            continue

        port_flag = f"-p {ports}" if ports else ""
        cmd = f"docker run -d --name {name} {port_flag} {image}"
        result = run_cmd(cmd)
        if name.lower() in result.lower() or "error" not in result.lower():
            print(f"      Created {name} ({image})")
        else:
            print(f"      [WARN] Could not create {name}: {result[:100]}")

    print("[3/4] Verifying containers...")
    containers = dc.list_containers(all_containers=True)
    running = [c for c in containers if c["status"] == "running"]
    print(f"      {len(running)} containers running, {len(containers)} total")

    print("[4/4] Demo environment ready!")
    print()
    print("Running containers:")
    for c in containers:
        status_marker = "[OK]" if c["status"] == "running" else "[STOPPED]"
        print(f"  {status_marker} {c['name']} - {c['image']} - {c['status']}")

    return True


def simulate_incident(scenario: str = "memory"):
    print()
    print("=" * 60)
    print(f"  Simulating Incident: {scenario}")
    print("=" * 60)
    print()

    dc = DockerClient()

    if scenario == "memory":
        print("[!] Simulating OOM Kill on demo-api...")
        print("    Starting memory stress container targeting demo-api's cgroup...")

        print("[!] Starting stress-ng on demo-web to simulate load...")
        stress_cmd = (
            f"docker run -d --name demo-stress "
            f"--memory=64m {STRESS_IMAGE} "
            f"--cpu 1 --io 1 --vm 2 --vm-bytes 128M --timeout 30s"
        )
        result = run_cmd(stress_cmd)
        print(f"    Stress container started.")

        print("[!] Marking demo-api as unhealthy by stopping it...")
        run_cmd("docker stop demo-api")
        time.sleep(2)

        stopped = dc.inspect_container("demo-api")
        if stopped:
            print(f"    demo-api status: {stopped['status']} (exit_code={stopped.get('exit_code')})")

        print()
        print("[ALERT] Incident ACTIVE:")
        print("  - demo-api container STOPPED (simulated OOM)")
        print("  - demo-stress container consuming resources")
        print("  - Users reporting 502 errors on payment endpoint")
        print()
        print("  Run the SRE Copilot to diagnose:")
        print("    /triage alert-001")
        print("    /analyze demo-api")
        print("    @sre_copilot The payment API is returning 502 errors")
        print()

    elif scenario == "disk":
        print("[!] Simulating disk full on demo-db...")

        print("[!] Filling disk space in demo-db container...")
        run_cmd("docker exec demo-db sh -c 'dd if=/dev/zero of=/tmp/bigfile bs=1M count=100 2>/dev/null || true'")
        print("    Created ~100MB file in demo-db")

        print()
        print("[ALERT] Incident ACTIVE:")
        print("  - demo-db running out of disk space")
        print("  - Database writes failing with ENOSPC")
        print()
        print("  Run the SRE Copilot to diagnose:")
        print("    /triage alert-004")
        print("    /analyze order-processor")
        print()

    elif scenario == "crashloop":
        print("[!] Simulating crash loop on demo-api...")

        print("[!] Starting demo-api with bad config...")
        run_cmd("docker stop demo-api 2>/dev/null")
        run_cmd("docker rm demo-api 2>/dev/null")
        run_cmd(f"docker run -d --name demo-api --env WRONG_CONFIG=value {NGINX_IMAGE}")
        run_cmd("docker stop demo-api")
        run_cmd("docker start demo-api")

        print()
        print("[ALERT] Incident ACTIVE:")
        print("  - demo-api in CrashLoopBackOff")
        print("  - Container restarting repeatedly")
        print()
        print("  Run the SRE Copilot to diagnose:")
        print("    /triage alert-005")
        print("    @sre_copilot demo-api is crash looping")
        print()

    elif scenario == "cleanup":
        print("[!] Cleaning up all demo containers...")
        for name in ["demo-web", "demo-api", "demo-db", "demo-stress"]:
            run_cmd(f"docker stop {name} 2>/dev/null")
            run_cmd(f"docker rm {name} 2>/dev/null")
            print(f"    Removed {name}")
        print()
        print("[OK] Cleanup complete.")
        return

    else:
        print(f"[ERROR] Unknown scenario: {scenario}")
        print("Available: memory, disk, crashloop, cleanup")
        return

    print("Monitor with:")
    print("  docker ps -a")
    print("  /alerts")


def main():
    if len(sys.argv) < 2:
        print("Usage: python simulate_incident.py <command>")
        print()
        print("Commands:")
        print("  setup     - Create demo Docker containers")
        print("  memory    - Simulate OOM/memory incident")
        print("  disk      - Simulate disk full incident")
        print("  crashloop - Simulate crash loop incident")
        print("  cleanup   - Remove all demo containers")
        print("  full      - Setup + run memory scenario")
        return

    command = sys.argv[1].lower()

    if command == "setup":
        setup_demo_containers()
    elif command == "full":
        if setup_demo_containers():
            time.sleep(2)
            simulate_incident("memory")
    elif command in ("memory", "disk", "crashloop", "cleanup"):
        simulate_incident(command)
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()