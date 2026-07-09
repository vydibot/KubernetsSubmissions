import time
import uuid
from datetime import datetime, timezone


def format_timestamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def main() -> None:
    random_value = str(uuid.uuid4())

    try:
        while True:
            timestamp = format_timestamp(datetime.now(timezone.utc))
            print(f"{timestamp}: {random_value}", flush=True)
            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopping logger.", flush=True)


if __name__ == "__main__":
    main()
