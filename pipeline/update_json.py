from typing import Dict, Any
from datetime import datetime, timezone
from pipeline.scoring import score_to_status

def _node_key(n: Dict[str, Any]) -> str:
    return n.get("id") or n.get("hostname") or n.get("name") or n.get("ip_address") or n.get("IP") or ""

def merge_scores(payload: Dict[str, Any], node_scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Merge threat scores into payload and track version changes for delta detection.
    
    Updates node version numbers when threat_score or status changes, enabling
    Unreal Engine to detect and focus on nodes with meaningful changes.
    """
    nodes = payload.get("nodes") or []
    now = datetime.now(timezone.utc).isoformat()

    for n in nodes:
        k = _node_key(n)
        if not k or k not in node_scores:
            continue

        # Get previous values for comparison
        prev_score = float(n.get("threat_score") or 0.0)
        prev_status = n.get("status")
        prev_version = int(n.get("version") or 0)

        # Calculate new values
        new_score = float(node_scores[k])
        new_status = score_to_status(new_score)

        # Increment version if score or status changed significantly
        if (new_score != prev_score) or (new_status != prev_status):
            n["version"] = prev_version + 1
            n["updated_at"] = now

        # Set network_id if not present (for UE clustering)
        if "network_id" not in n:
            # Simple network assignment based on node type or position
            # You can customize this logic based on your network topology
            n["network_id"] = n.get("network_id") or f"net_{k[:3]}" or "net_default"

        # Update the node with new values
        n["threat_score"] = new_score
        n["status"] = new_status

    # Update overall payload timestamp
    payload["updated_at"] = now
    return payload
