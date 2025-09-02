# Model definitions and data structures for the cyber pipeline
from typing import Dict, List, Any, Tuple
import torch

def load_model() -> Tuple[torch.nn.Module, torch.device]:
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    class _Identity(torch.nn.Module):
        def forward(self, x):  # placeholder
            return x
    return _Identity().to(device).eval(), device

def infer_nodes(model: torch.nn.Module, device: torch.device, nodes: List[Dict[str, Any]]) -> Dict[str, float]:
    """Return {node_key: threat_score in [0,1]} (stubbed for now)."""
    def key(n: Dict[str, Any]) -> str:
        return n.get("id") or n.get("hostname") or n.get("name") or n.get("ip_address") or n.get("IP") or ""

    out: Dict[str, float] = {}
    for n in nodes:
        k = key(n)
        if not k:
            continue
        tail = "".join([c for c in k if c.isalnum()])[-2:] or "00"
        try:
            val = int(tail, 16) if any(c.isalpha() for c in tail) else int(tail, 10)
        except Exception:
            val = sum(ord(c) for c in tail)
        out[k] = float((val % 100) / 100.0)
    return out
