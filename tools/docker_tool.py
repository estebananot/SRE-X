import docker
from docker.errors import DockerException, APIError, NotFound


class DockerClient:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                self._client = docker.from_env()
            except DockerException:
                self._client = None
        return self._client

    def is_available(self) -> bool:
        return self.client is not None

    def list_containers(self, all_containers: bool = False) -> list[dict]:
        if not self.is_available():
            return []
        try:
            containers = self.client.containers.list(all=all_containers)
            return [
                {
                    "id": c.short_id,
                    "name": c.name,
                    "image": str(c.image.tags[0]) if c.image.tags else str(c.image.id[:12]),
                    "status": c.status,
                    "state": c.attrs.get("State", {}).get("Status", "unknown"),
                }
                for c in containers
            ]
        except APIError:
            return []

    def inspect_container(self, container_id_or_name: str) -> dict | None:
        if not self.is_available():
            return None
        try:
            container = self.client.containers.get(container_id_or_name)
            attrs = container.attrs
            state = attrs.get("State", {})
            return {
                "id": container.short_id,
                "name": container.name,
                "image": str(container.image.tags[0]) if container.image.tags else str(container.image.id[:12]),
                "status": container.status,
                "exit_code": state.get("ExitCode"),
                "error": state.get("Error", ""),
                "oom_killed": state.get("OOMKilled", False),
                "restart_count": attrs.get("RestartCount", 0),
                "started_at": state.get("StartedAt", ""),
                "finished_at": state.get("FinishedAt", ""),
                "health": state.get("Health", {}).get("Status", "unknown") if state.get("Health") else None,
            }
        except (NotFound, APIError):
            return None

    def get_container_logs(self, container_id_or_name: str, tail: int = 100) -> list[str]:
        if not self.is_available():
            return []
        try:
            container = self.client.containers.get(container_id_or_name)
            logs = container.logs(tail=tail, timestamps=True)
            if isinstance(logs, bytes):
                logs = logs.decode("utf-8", errors="replace")
            return [line.strip() for line in logs.splitlines() if line.strip()]
        except (NotFound, APIError):
            return []

    def restart_container(self, container_id_or_name: str, timeout: int = 10) -> dict:
        if not self.is_available():
            return {"success": False, "error": "Docker not available"}
        try:
            container = self.client.containers.get(container_id_or_name)
            container.restart(timeout=timeout)
            return {"success": True, "container": container.name, "action": "restart"}
        except (NotFound, APIError) as e:
            return {"success": False, "error": str(e)}

    def stop_container(self, container_id_or_name: str, timeout: int = 10) -> dict:
        if not self.is_available():
            return {"success": False, "error": "Docker not available"}
        try:
            container = self.client.containers.get(container_id_or_name)
            container.stop(timeout=timeout)
            return {"success": True, "container": container.name, "action": "stop"}
        except (NotFound, APIError) as e:
            return {"success": False, "error": str(e)}