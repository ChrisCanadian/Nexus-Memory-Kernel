import hashlib
import json
from datetime import datetime, timezone
from typing import Any

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def make_receipt(*, action: str, user_id: str, target_id: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    material = {
        "action": action,
        "user_id": user_id,
        "target_id": target_id,
        "payload": payload,
    }
    canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
    return {
        "timestamp": utc_now(),
        "action": action,
        "user_id": user_id,
        "target_id": target_id,
        "payload_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }
