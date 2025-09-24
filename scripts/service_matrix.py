"""
Service Matrix: non-destructive readiness check for local dev stack.

Checks reachability and basic responses for:
- n8n (http port)
- Supabase (http port)
- Postgres (tcp port)
- n8n-mcp stdio (file/binary presence only; stdio handshake is IDE-owned)
- Filesystem root path

Usage:
  PYTHONPATH=src python3 scripts/service_matrix.py

Outputs one JSON report to stdout.
"""
from __future__ import annotations

import json
import os
import socket
import time
from pathlib import Path
from typing import Any, Dict

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover
    requests = None  # Fallback to socket-only checks if requests missing


def http_probe(url: str, timeout: float = 2.0) -> Dict[str, Any]:
    t0 = time.time()
    if not requests:
        return {"ok": False, "error": "requests-not-installed", "latency_ms": int((time.time()-t0)*1000)}
    try:
        r = requests.get(url, timeout=timeout)
        return {
            "ok": True,
            "status": r.status_code,
            "latency_ms": int((time.time() - t0) * 1000),
            "excerpt": (r.text[:120] if isinstance(r.text, str) else None),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "latency_ms": int((time.time()-t0)*1000)}


def tcp_probe(host: str, port: int, timeout: float = 1.0) -> Dict[str, Any]:
    t0 = time.time()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return {"ok": True, "latency_ms": int((time.time() - t0) * 1000)}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "latency_ms": int((time.time()-t0)*1000)}


def exists(path: str) -> bool:
    return Path(path).exists()


def main() -> None:
    report: Dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "services": []
    }

    # n8n http
    n8n = {"name": "n8n", "checks": []}
    p = http_probe("http://localhost:5678/rest/workflows")
    n8n["checks"].append({"name": "GET /rest/workflows", **p})
    n8n["available"] = bool(p.get("ok"))
    report["services"].append(n8n)

    # supabase http
    supa = {"name": "supabase", "checks": []}
    p = http_probe("http://localhost:8000")
    supa["checks"].append({"name": "GET /", **p})
    supa["available"] = bool(p.get("ok"))
    report["services"].append(supa)

    # postgres tcp
    pg = {"name": "postgres", "checks": []}
    p = tcp_probe("127.0.0.1", 5432)
    pg["checks"].append({"name": "tcp 5432", **p})
    pg["available"] = bool(p.get("ok"))
    report["services"].append(pg)

    # n8n-mcp stdio presence
    mcp = {"name": "n8n-mcp-stdio", "checks": []}
    binary = exists("/Volumes/SSD_OSX/Devssd/Projects/n8n-mcp/dist/mcp/index.js")
    db = exists("/Volumes/SSD_OSX/Devssd/Projects/n8n-mcp/data/nodes.db")
    mcp["checks"].append({"name": "binary", "ok": binary})
    mcp["checks"].append({"name": "nodes.db", "ok": db})
    mcp["available"] = binary and db
    report["services"].append(mcp)

    # filesystem path presence
    fs = {"name": "filesystem-root", "checks": []}
    root_ok = exists("/Volumes/SSD_OSX/Devssd/Projects/n8n-mcp")
    fs["checks"].append({"name": "path exists", "ok": root_ok})
    fs["available"] = root_ok
    report["services"].append(fs)

    # summary
    ok_count = sum(1 for s in report["services"] if s.get("available"))
    report["summary"] = {"services_total": len(report["services"]), "services_ok": ok_count}

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
