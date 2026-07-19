import time
import uuid
from datetime import datetime, timezone

# Path to the shared volume
SHARED_FILE_PATH = "/usr/src/app/shared/log.txt"

# Generate random string once on startup
RANDOM_VALUE = str(uuid.uuid4())

def format_timestamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def main() -> None:
    print(f"Writer started. UUID: {RANDOM_VALUE}", flush=True)
    while True:
        timestamp = format_timestamp(datetime.now(timezone.utc))
        log_line = f"{timestamp}: {RANDOM_VALUE}\n"
        
        # Append to the shared file
        try:
            with open(SHARED_FILE_PATH, "a") as f:
                f.write(log_line)
        except Exception as e:
            print(f"Error writing to file: {e}", flush=True)
            
        time.sleep(5)

if __name__ == "__main__":
    main()