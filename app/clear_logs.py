"""
`app/clear_logs.py`

Run this script to clear the logs directory if it gets too cluttered
"""

from pathlib import Path

def clear_logs():
    # logs/ is sibling of app/, so go one level up from current file
    logs_dir = Path(__file__).resolve().parent.parent / "logs"

    if not logs_dir.exists():
        print(f"No logs directory found at {logs_dir}")
        return

    deleted = 0
    for log_file in logs_dir.iterdir():
        if log_file.is_file():
            log_file.unlink()
            deleted += 1

    print(f"Deleted {deleted} log file(s) from {logs_dir}")

if __name__ == "__main__":
    clear_logs()