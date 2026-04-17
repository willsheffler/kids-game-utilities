from __future__ import annotations

import argparse
from pathlib import Path

from .http_api import run_http_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the kids-game-utilities v1 backend server.")
    parser.add_argument("--root", default=".", help="workspace root to store .kids-game-utilities state under")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run_http_server(root=Path(args.root).resolve(), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
