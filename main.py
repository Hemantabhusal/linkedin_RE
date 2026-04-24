from pathlib import Path
import argparse
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from diagnostics.dump import dump_profile, dump_url
from worker.main import main as run_worker


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinkedIn profile scraper worker")
    subparsers = parser.add_subparsers(dest="command")

    dump_parser = subparsers.add_parser("dump-url", help="Dump an authenticated Voyager JSON response")
    dump_parser.add_argument("url", help="Absolute LinkedIn URL or path beginning with /")
    dump_parser.add_argument("output", help="Output JSON path")

    dump_profile_parser = subparsers.add_parser("dump-profile", help="Dump the main profile payload used by the worker")
    dump_profile_parser.add_argument("linkedin_url", help="LinkedIn profile URL")
    dump_profile_parser.add_argument("output", help="Output JSON path")

    args = parser.parse_args()
    if args.command == "dump-url":
        raise SystemExit(dump_url(args.url, args.output))
    if args.command == "dump-profile":
        raise SystemExit(dump_profile(args.linkedin_url, args.output))
    raise SystemExit(run_worker())
