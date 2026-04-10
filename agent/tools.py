import json

from langchain_core.tools import tool

from tools.data_sources import DataSourceManager

_ds = DataSourceManager()


@tool
def get_logs(service: str | None = None, level: str | None = None, limit: int = 10) -> str:
    """Retrieve application logs for a given service. Use this to find error messages,
    stack traces, and other diagnostic information.

    Args:
        service: The service name to filter logs for (e.g. 'payment-api', 'auth-service')
        level: Log level to filter by: 'ERROR', 'WARN', 'INFO'
        limit: Maximum number of log entries to return (default 10)
    """
    logs = _ds.get_logs(service=service, level=level, limit=limit)
    if not logs:
        return f"No logs found for service={service}, level={level}"
    return json.dumps(logs, indent=2)


@tool
def get_metrics(service: str | None = None) -> str:
    """Retrieve infrastructure metrics for a service (CPU, memory, latency, error rate, etc).

    Args:
        service: The service name to get metrics for (e.g. 'payment-api'). If None, returns all services.
    """
    metrics = _ds.get_metrics(service=service)
    if not metrics:
        return f"No metrics found for service={service}"
    return json.dumps(metrics, indent=2)


@tool
def get_alerts(severity: str | None = None) -> str:
    """Retrieve active alerts. Use this to understand what incidents are currently firing.

    Args:
        severity: Filter by severity: 'critical', 'warning'. If None, returns all alerts.
    """
    alerts = _ds.get_alerts(severity=severity)
    if not alerts:
        return f"No alerts found for severity={severity}"
    return json.dumps(alerts, indent=2)


@tool
def get_container_status(name: str | None = None) -> str:
    """Get status of Docker containers. Use this to check if containers are running,
    crashed, or in a restart loop.

    Args:
        name: Container name or ID to inspect. If None, lists all containers.
    """
    if name:
        result = _ds.get_container_status(name=name)
        if result is None:
            return f"Container '{name}' not found"
        return json.dumps(result, indent=2)
    containers = _ds.get_container_status()
    if not containers:
        return "No containers found or Docker not available"
    return json.dumps(containers, indent=2)


@tool
def get_container_logs(name: str, tail: int = 50) -> str:
    """Get real-time logs from a Docker container. Use this to investigate a specific
    container's recent output.

    Args:
        name: Container name or ID
        tail: Number of recent log lines to retrieve (default 50)
    """
    logs = _ds.get_container_logs(name=name, tail=tail)
    if not logs:
        return f"No logs found for container '{name}'"
    return "\n".join(logs)


@tool
def restart_container(name: str) -> str:
    """Restart a Docker container. ONLY use this after explaining why and getting
    human confirmation. This is a DESTRUCTIVE action.

    Args:
        name: Container name or ID to restart
    """
    result = _ds.restart_container(name)
    return json.dumps(result, indent=2)


@tool
def stop_container(name: str) -> str:
    """Stop a Docker container. ONLY use this after explaining why and getting
    human confirmation. This is a DESTRUCTIVE action.

    Args:
        name: Container name or ID to stop
    """
    result = _ds.stop_container(name)
    return json.dumps(result, indent=2)


@tool
def get_open_source_logs(source: str | None = None, level: str | None = None, limit: int = 20) -> str:
    """Retrieve real production logs from open-source systems (HDFS, Spark, Hadoop, Zookeeper).
    These are actual logs from the LogPAI/Loghub repository (Stanford). Use this to analyze
    real infrastructure issues from well-known distributed systems.

    Args:
        source: Log source to filter: 'HDFS', 'Spark', 'Hadoop', 'Zookeeper'. If None, returns from all.
        level: Log level filter: 'ERROR', 'WARN', 'INFO'. If None, returns all levels.
        limit: Maximum number of log entries to return (default 20)
    """
    logs = _ds.get_open_source_logs(service=source, level=level, limit=limit)
    if not logs:
        return f"No open-source logs found for source={source}, level={level}"
    return json.dumps(logs, indent=2)


@tool
def list_log_sources() -> str:
    """List available open-source log sources (HDFS, Spark, Hadoop, Zookeeper).
    Use this first to discover what real production logs are available for analysis.
    """
    sources = _ds.get_log_sources()
    return json.dumps(sources, indent=2)


SRE_TOOLS = [
    get_logs,
    get_metrics,
    get_alerts,
    get_container_status,
    get_container_logs,
    restart_container,
    stop_container,
    get_open_source_logs,
    list_log_sources,
]