import os
import urllib.request
from pathlib import Path

RAW_LOGS_DIR = Path(__file__).parent.parent / "data" / "raw_logs"

LOGHUB_BASE_URL = "https://raw.githubusercontent.com/logpai/loghub/master"

LOG_FILES = {
    "HDFS": "HDFS/HDFS_2k.log",
    "Spark": "Spark/Spark_2k.log",
    "Zookeeper": "Zookeeper/Zookeeper_2k.log",
    "Hadoop": "Hadoop/Hadoop_2k.log",
}


def download_logs():
    RAW_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    for name, path in LOG_FILES.items():
        url = f"{LOGHUB_BASE_URL}/{path}"
        filename = path.split("/")[-1]
        dest = RAW_LOGS_DIR / filename

        if dest.exists():
            print(f"  [SKIP] {filename} already exists")
            continue

        print(f"  [DOWNLOAD] {name}: {url}")
        try:
            urllib.request.urlretrieve(url, dest)
            print(f"  [OK] {filename} downloaded ({dest.stat().st_size} bytes)")
        except Exception as e:
            print(f"  [ERROR] Failed to download {filename}: {e}")


if __name__ == "__main__":
    print("Downloading open-source logs from LogPAI/Loghub (Stanford)...")
    download_logs()
    print("\nDone!")