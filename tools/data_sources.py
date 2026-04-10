import json
from pathlib import Path

from tools.docker_tool import DockerClient
from tools.log_parser import get_open_source_logs, get_available_sources


DATA_DIR = Path(__file__).parent.parent / "data"


class DataSourceManager:
    def __init__(self):
        self._docker = DockerClient()
        self._logs = None
        self._metrics = None
        self._alerts = None

    def _load_json(self, filename: str) -> list | dict:
        filepath = DATA_DIR / filename
        if filepath.exists():
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        return [] if filename == "sample_logs.json" else {}

    def get_logs(self, service: str | None = None, level: str | None = None, limit: int = 50) -> list[dict]:
        if self._logs is None:
            self._logs = self._load_json("sample_logs.json")

        results = self._logs

        if service:
            results = [l for l in results if l.get("service") == service]
        if level:
            results = [l for l in results if l.get("level", "").upper() == level.upper()]

        return results[:limit]

    def get_metrics(self, service: str | None = None) -> dict | list[dict]:
        if self._metrics is None:
            self._metrics = self._load_json("sample_metrics.json")

        if service:
            return self._metrics.get(service, {})
        return self._metrics

    def get_alerts(self, severity: str | None = None) -> list[dict]:
        if self._alerts is None:
            self._alerts = self._load_json("sample_alerts.json")

        if severity:
            return [a for a in self._alerts if a.get("severity") == severity]
        return self._alerts

    def get_container_status(self, name: str | None = None) -> list[dict] | dict | None:
        all_containers = self._docker.list_containers(all_containers=True)
        if not all_containers and not self._docker.is_available():
            return []
        if name:
            for c in all_containers:
                if name in c.get("name", "") or name in c.get("id", ""):
                    return self._docker.inspect_container(c["id"])
            return None
        return all_containers

    def get_container_logs(self, name: str, tail: int = 100) -> list[str]:
        return self._docker.get_container_logs(name, tail=tail)

    def restart_container(self, name: str) -> dict:
        return self._docker.restart_container(name)

    def stop_container(self, name: str) -> dict:
        return self._docker.stop_container(name)

    def get_incident_context(self, service: str) -> dict:
        return {
            "service": service,
            "logs": self.get_logs(service=service, limit=10),
            "metrics": self.get_metrics(service=service),
            "alerts": [a for a in self.get_alerts() if a.get("service") == service],
            "docker_status": self.get_container_status(name=service),
        }

    def get_open_source_logs(self, service: str | None = None, level: str | None = None, limit: int = 50) -> list[dict]:
        return get_open_source_logs(service=service, level=level, limit=limit)

    def get_log_sources(self) -> list[dict]:
        return get_available_sources()