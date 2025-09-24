import json
import time
from typing import Any, Dict


def log(event: str, **fields: Dict[str, Any]) -> None:
    payload = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        **fields,
    }
    # Redact obvious secrets
    for key in list(payload.keys()):
        lower = key.lower()
        if any(s in lower for s in ("token", "secret", "apikey")):
            payload[key] = "***redacted***"
    print(json.dumps(payload, ensure_ascii=False))

