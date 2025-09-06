"""
Change detection module for tracking node/edge differences between pipeline runs.
Provides delta feeds for Unreal Engine to identify which networks to expand and focus on.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone

def _node_key(n: Dict[str, Any]) -> str:
    """Extract unique identifier from node data."""
    return n.get("id") or n.get("hostname") or n.get("name") or n.get("ip_address") or n.get("IP") or ""

def index_nodes(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Create a lookup index of nodes by their unique key."""
    return {_node_key(n): n for n in (payload.get("nodes") or []) if _node_key(n)}

def compute_changes(prev: Dict[str, Any], curr: Dict[str, Any], delta_min: float = 0.0) -> List[Dict[str, Any]]:
    """
    Compare previous and current snapshots to identify changed nodes.
    
    Args:
        prev: Previous snapshot data (can be None for first run)
        curr: Current snapshot data
        delta_min: Minimum score change threshold to consider significant
        
    Returns:
        List of change records with prev/curr state and metadata for UE
    """
    if not prev:
        prev = {"nodes": []}
        
    prev_idx = index_nodes(prev)
    curr_idx = index_nodes(curr)
    changes: List[Dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()

    for node_id, curr_node in curr_idx.items():
        prev_node = prev_idx.get(node_id)
        
        if not prev_node:
            # New node detected
            changes.append({
                "entity": "node",
                "id": node_id,
                "network_id": curr_node.get("network_id"),
                "prev": None,
                "curr": {
                    "threat_score": curr_node.get("threat_score"),
                    "status": curr_node.get("status"),
                    "version": curr_node.get("version")
                },
                "threshold_crossed": True,
                "reason": "new_node",
                "updated_at": curr_node.get("updated_at") or now,
            })
            continue

        # Compare existing node
        prev_score = float(prev_node.get("threat_score") or 0.0)
        curr_score = float(curr_node.get("threat_score") or 0.0)
        prev_status = prev_node.get("status")
        curr_status = curr_node.get("status")
        prev_version = int(prev_node.get("version") or 0)
        curr_version = int(curr_node.get("version") or 0)

        # Determine if this is a significant change
        score_changed = abs(curr_score - prev_score) > delta_min
        status_changed = prev_status != curr_status
        version_changed = curr_version != prev_version
        
        if score_changed or status_changed or version_changed:
            # Determine change reason and significance
            threshold_crossed = status_changed
            if status_changed:
                reason = "status_change"
            elif score_changed and abs(curr_score - prev_score) >= 0.2:
                reason = "significant_score_delta"
                threshold_crossed = True
            elif score_changed:
                reason = "score_delta"
            else:
                reason = "version_update"

            changes.append({
                "entity": "node",
                "id": node_id,
                "network_id": curr_node.get("network_id"),
                "prev": {
                    "threat_score": prev_score,
                    "status": prev_status,
                    "version": prev_version
                },
                "curr": {
                    "threat_score": curr_score,
                    "status": curr_status,
                    "version": curr_version
                },
                "threshold_crossed": threshold_crossed,
                "reason": reason,
                "updated_at": curr_node.get("updated_at") or now,
            })

    # Sort by significance (threshold crossings first, then by score magnitude)
    changes.sort(key=lambda x: (
        -int(x["threshold_crossed"]),  # Threshold crossings first
        -float(x["curr"]["threat_score"] or 0.0)  # Then by threat score (high to low)
    ))

    return changes

