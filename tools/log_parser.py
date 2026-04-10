import re
import json
from pathlib import Path
from datetime import datetime


RAW_LOGS_DIR = Path(__file__).parent.parent / "data" / "raw_logs"

LOG_SOURCE_MAP = {
    "HDFS": {
        "file": "HDFS_2k.log",
        "service": "hdfs-namenode",
        "pattern": re.compile(r"^(\d{6} \d{6})\s+(\d+)\s+(\w+)\s+(.+?):\s+(.+)$"),
        "fields": ("date", "pid", "level", "component", "message"),
    },
    "Spark": {
        "file": "Spark_2k.log",
        "service": "spark-executor",
        "pattern": re.compile(r"^(\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(.+?):\s+(.+)$"),
        "fields": ("date", "level", "component", "message"),
    },
    "Zookeeper": {
        "file": "Zookeeper_2k.log",
        "service": "zookeeper-node",
        "pattern": re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+-\s+(\w+)\s+\[(.+?)\]\s+-\s+(.+)$"),
        "fields": ("date", "level", "thread", "message"),
    },
    "Hadoop": {
        "file": "Hadoop_2k.log",
        "service": "hadoop-jobtracker",
        "pattern": re.compile(r"^(\d{6} \d{6})\s+(\d+)\s+(\w+)\s+(.+?):\s+(.+)$"),
        "fields": ("date", "pid", "level", "component", "message"),
    },
}


def parse_log_file(source_name: str, limit: int = 200) -> list[dict]:
    source = LOG_SOURCE_MAP.get(source_name)
    if not source:
        return []

    log_path = RAW_LOGS_DIR / source["file"]
    if not log_path.exists():
        return []

    parsed_logs = []
    with open(log_path, encoding="utf-8", errors="replace") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            match = source["pattern"].match(line)
            if not match:
                continue

            groups = match.groups()
            field_names = source["fields"]
            log_entry = {"_field_names": field_names}
            for i, name in enumerate(field_names):
                log_entry[name] = groups[i] if i < len(groups) else ""

            level = ""
            if "level" in log_entry:
                level = log_entry["level"].upper()
            elif "level" in field_names:
                level_idx = field_names.index("level")
                level = groups[level_idx].upper() if level_idx < len(groups) else "INFO"

            message = log_entry.get("message", line)
            component = log_entry.get("component", source["service"])
            timestamp = log_entry.get("date", "")
            pid = log_entry.get("pid", str(line_num))

            parsed_logs.append({
                "timestamp": timestamp,
                "level": level,
                "service": source["service"],
                "component": component,
                "message": message,
                "host": source["service"],
                "source": source_name,
                "line_number": line_num,
            })

            if len(parsed_logs) >= limit:
                break

    return parsed_logs


def get_open_source_logs(service: str | None = None, level: str | None = None, limit: int = 50) -> list[dict]:
    all_logs = []
    for source_name in LOG_SOURCE_MAP:
        logs = parse_log_file(source_name, limit=500)
        all_logs.extend(logs)

    if service:
        all_logs = [l for l in all_logs if service in l.get("service", "") or service in l.get("source", "")]
    if level:
        all_logs = [l for l in all_logs if l.get("level", "").upper() == level.upper()]

    return all_logs[:limit]


def get_available_sources() -> list[str]:
    available = []
    for source_name, source in LOG_SOURCE_MAP.items():
        log_path = RAW_LOGS_DIR / source["file"]
        available.append({
            "source": source_name,
            "file": source["file"],
            "service": source["service"],
            "available": log_path.exists(),
        })
    return available