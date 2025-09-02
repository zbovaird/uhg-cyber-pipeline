from typing import Dict, Any
from datetime import datetime, timezone
from pipeline.scoring import score_to_status

def _node_key(n: Dict[str, Any]) -> str:
    return n.get("id") or n.get("hostname") or n.get("name") or n.get("ip_address") or n.get("IP") or ""

def merge_scores(payload: Dict[str, Any], node_scores: Dict[str, float]) -> Dict[str, Any]:
    nodes = payload.get("nodes") or []
    for n in nodes:
        k = _node_key(n)
        if not k:
            continue
        if k in node_scores:
            s = float(node_scores[k])
            n["threat_score"] = s
            n["status"] = score_to_status(s)
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    return payload
