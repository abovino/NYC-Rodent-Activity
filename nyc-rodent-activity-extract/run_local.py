import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from src.app import lambda_handler


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("event_file")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    event_path = Path(args.event_file).resolve()

    with event_path.open("r", encoding="utf-8") as f:
        event = json.load(f)

    result = lambda_handler(event, None)
    print(json.dumps(result, indent=2, default=str))