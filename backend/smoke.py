from __future__ import annotations

import argparse
import base64
import json
import threading
import urllib.request
from pathlib import Path

from .http_api import KidsGameHTTPServer


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a narrow smoke test against the kids-game-utilities backend.")
    parser.add_argument("--root", default=".", help="workspace root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    server = KidsGameHTTPServer(("127.0.0.1", 0), root)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        base = f"http://{host}:{port}"
        with urllib.request.urlopen(f"{base}/bootstrap?userId=will", timeout=3) as resp:
            bootstrap = json.loads(resp.read().decode("utf-8"))
        payload = json.dumps(
            {
                "imageBase64": base64.b64encode(b"smoke-bytes").decode("ascii"),
                "imageFilename": "smoke.png",
                "label": "smoke",
                "projectSlug": "tower-defense",
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{base}/artifacts",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            upload = json.loads(resp.read().decode("utf-8"))
        upload_path = upload["result"]["artifact"]["path"]
        with urllib.request.urlopen(f"{base}{upload_path}", timeout=3) as resp:
            uploaded_bytes = resp.read()
        print(
            json.dumps(
                {
                    "ok": True,
                    "bootstrap_ok": bootstrap.get("ok", False),
                    "upload_path": upload_path,
                    "static_bytes": uploaded_bytes.decode("utf-8"),
                },
                indent=2,
            )
        )
        return 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    raise SystemExit(main())
