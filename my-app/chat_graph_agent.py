#!/usr/bin/env python3
"""
Standalone Chat Graph Agent for UHG Cybersecurity Pipeline

Features:
- Tool-based graph querying (fast, precise)
- Direct HTTP access to GitHub raw data
- No pipeline dependencies
- Comprehensive threat analysis
"""

from __future__ import annotations
import os
import json
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Load .env from same directory as this script
load_dotenv(Path(__file__).resolve().parent / ".env")

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor

DEFAULT_URL = os.environ.get(
    "GRAPH_URL",
    "https://raw.githubusercontent.com/zbovaird/Unreal-UHG-Output/main/Data/network_topology_scored.json"
)

# ---- Simple in-memory cache ----
_GRAPH: Dict[str, Any] | None = None

def _ensure_graph_loaded(url: Optional[str] = None) -> Dict[str, Any]:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _fetch(url or DEFAULT_URL)
    return _GRAPH

def _fetch(url: str) -> Dict[str, Any]:
    """Fetch graph data from URL with error handling."""
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json() if r.headers.get("content-type","").startswith("application/json") else json.loads(r.text)
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object at the root")
        return data
    except Exception as e:
        print(f"Warning: Failed to fetch graph: {e}")
        return {"error": f"Failed to fetch graph: {str(e)}", "nodes": [], "edges": []}

def _label_counts(nodes: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count nodes by status/label."""
    counts: Dict[str, int] = {}
    for n in nodes:
        # Check both 'status' and 'label' fields for compatibility
        label = n.get("status") or n.get("label", "unknown")
        counts[label] = counts.get(label, 0) + 1
    return counts

def _threat_stats(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate comprehensive threat statistics."""
    if not nodes:
        return {"total": 0, "avg_score": 0.0, "max_score": 0.0}
    
    scores = []
    for n in nodes:
        # Handle both 'threat_score' and 'score' fields
        score = float(n.get("threat_score") or n.get("score", 0.0))
        scores.append(score)
    
    return {
        "total": len(nodes),
        "avg_score": round(sum(scores) / len(scores), 3),
        "max_score": round(max(scores), 3),
        "min_score": round(min(scores), 3)
    }

# ---- Tools ----
@tool
def fetch_graph(url: Optional[str] = None) -> str:
    """
    Fetch and cache the graph JSON from URL. Returns summary with threat analysis.
    """
    global _GRAPH
    _GRAPH = _fetch(url or DEFAULT_URL)
    
    if "error" in _GRAPH:
        return json.dumps(_GRAPH, indent=2)
    
    keys = list(_GRAPH.keys())
    nodes = _GRAPH.get("nodes", [])
    edges = _GRAPH.get("edges", [])
    
    summary = {
        "url": url or DEFAULT_URL,
        "root_keys": keys,
        "nodes_count": len(nodes) if isinstance(nodes, list) else "n/a",
        "edges_count": len(edges) if isinstance(edges, list) else "n/a",
        "status_counts": _label_counts(nodes) if isinstance(nodes, list) else {},
        "threat_stats": _threat_stats(nodes) if isinstance(nodes, list) else {}
    }
    return json.dumps(summary, indent=2)

@tool
def list_nodes(status: Optional[str] = None, min_score: float = 0.0, top_n: int = 25) -> str:
    """
    List nodes filtered by status (benign/suspicious/malicious) and min threat_score.
    Returns top_n nodes sorted by score descending.
    """
    g = _ensure_graph_loaded()
    nodes = g.get("nodes", [])
    out = []
    
    for n in nodes:
        # Handle both 'threat_score' and 'score' fields
        score = float(n.get("threat_score") or n.get("score", 0.0))
        node_status = n.get("status") or n.get("label", "unknown")
        
        if score < min_score:
            continue
        if status and (node_status != status):
            continue
            
        out.append({
            "id": n.get("id") or n.get("ip_address") or n.get("hostname"),
            "hostname": n.get("hostname"),
            "ip_address": n.get("ip_address"),
            "threat_score": score,
            "status": node_status,
            "network_id": n.get("network_id"),
            "version": n.get("version", 0)
        })
    
    out.sort(key=lambda x: x["threat_score"], reverse=True)
    return json.dumps(out[:top_n], indent=2)

@tool
def node_info(identifier: str) -> str:
    """
    Get full details for a node by id/hostname/ip_address. Exact match.
    """
    g = _ensure_graph_loaded()
    nodes = g.get("nodes", [])
    ident = identifier.strip()
    
    for n in nodes:
        if ident in {str(n.get("id")), str(n.get("ip_address")), str(n.get("hostname"))}:
            return json.dumps(n, indent=2)
    
    return json.dumps({"error": f"Node '{identifier}' not found"}, indent=2)

@tool
def list_edges(src: Optional[str] = None, dst: Optional[str] = None, status: Optional[str] = None, top_n: int = 50) -> str:
    """
    List edges filtered by source/destination nodes and/or status.
    Returns top_n edges sorted by score descending.
    """
    g = _ensure_graph_loaded()
    edges = g.get("edges", [])
    out = []
    
    for e in edges:
        if src and e.get("src") != src:
            continue
        if dst and e.get("dst") != dst:
            continue
        if status and (e.get("status") or e.get("label")) != status:
            continue
            
        out.append({
            "src": e.get("src"),
            "dst": e.get("dst"),
            "score": float(e.get("score", 0.0)),
            "status": e.get("status") or e.get("label")
        })
    
    out.sort(key=lambda x: x["score"], reverse=True)
    return json.dumps(out[:top_n], indent=2)

@tool
def threat_summary() -> str:
    """
    Get comprehensive threat analysis summary of current graph data.
    """
    g = _ensure_graph_loaded()
    nodes = g.get("nodes", [])
    
    if not nodes:
        return json.dumps({"error": "No nodes available"}, indent=2)
    
    # Analyze threat levels
    benign = suspicious = malicious = 0
    scores = []
    high_risk_nodes = []
    
    for node in nodes:
        score = float(node.get("threat_score") or node.get("score", 0.0))
        scores.append(score)
        
        if score >= 0.8:
            malicious += 1
            high_risk_nodes.append({
                "id": node.get("id") or node.get("hostname") or node.get("ip_address"),
                "score": score,
                "network_id": node.get("network_id")
            })
        elif score >= 0.5:
            suspicious += 1
        else:
            benign += 1
    
    total = len(nodes)
    summary = {
        "total_nodes": total,
        "threat_distribution": {
            "benign": {"count": benign, "percentage": round(benign/total*100, 1)},
            "suspicious": {"count": suspicious, "percentage": round(suspicious/total*100, 1)},
            "malicious": {"count": malicious, "percentage": round(malicious/total*100, 1)}
        },
        "threat_scores": {
            "average": round(sum(scores)/total, 3),
            "maximum": round(max(scores), 3),
            "minimum": round(min(scores), 3)
        },
        "high_risk_nodes": sorted(high_risk_nodes, key=lambda x: x["score"], reverse=True)[:10]
    }
    
    return json.dumps(summary, indent=2)

# ---- Agent Setup ----
TOOLS = [fetch_graph, list_nodes, node_info, list_edges, threat_summary]

SYSTEM = """You are the UHG Cybersecurity Pipeline Assistant, an expert AI agent for network threat analysis.

IMPORTANT: You analyze NETWORK TOPOLOGY DATA (nodes, edges, threat scores) from a cybersecurity system. You do NOT create visual graphs or charts. When users say "fetch the graph" they mean "load the network topology data".

Your capabilities:
🔍 **Network Data Analysis**: Query network topology, nodes, edges with precise filtering
🛡️ **Threat Assessment**: Analyze threat scores, classify risks, identify patterns  
📊 **Security Insights**: Provide actionable cybersecurity recommendations

Key Context:
- You work with NETWORK TOPOLOGY DATA (JSON format with nodes and edges)
- Threat scores: 0.0 (benign) → 1.0 (malicious)
- Status levels: "benign" (<0.5), "suspicious" (0.5-0.8), "malicious" (>0.8)
- ALWAYS call fetch_graph tool first to load current network data
- Use threat_summary for comprehensive analysis

Available Tools (USE THESE TOOLS):
- fetch_graph: Load current network topology data from GitHub
- list_nodes: Filter network nodes by status/score
- node_info: Get detailed info for specific network node
- list_edges: Analyze network connections between nodes
- threat_summary: Get comprehensive threat analysis of the network

When a user asks to "fetch the graph" or similar, IMMEDIATELY use the fetch_graph tool to load network data.

Communication Style:
- Be precise and security-focused
- Use bullet points for clarity
- Highlight critical threats with appropriate urgency
- Provide specific node IDs and scores when relevant
- Always use tools to get actual data before responding
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

def make_agent() -> AgentExecutor:
    """Create the cybersecurity chat agent."""
    llm = ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=TOOLS, verbose=False)

def main():
    """Interactive chat session."""
    print("🛡️ UHG Cybersecurity Pipeline - Standalone Chat Agent")
    print("Features: Fast graph querying + Threat analysis")
    print("\nSample queries:")
    print("  • fetch the graph")
    print("  • show threat summary")
    print("  • list top malicious nodes")
    print("  • node info 185.175.0.7")
    print("  • edges from suspicious nodes")
    print("\nType 'quit' to exit")
    print("=" * 60)
    
    agent = make_agent()
    
    while True:
        try:
            q = input("\n💬 You: ").strip()
            if not q: 
                continue
            if q.lower() in {"exit", "quit", "bye"}:
                print("\n👋 Stay secure!")
                break
                
            print("\n🤖 Assistant: ", end="")
            resp = agent.invoke({"input": q})
            print(resp["output"], "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Chat ended. Stay secure!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()