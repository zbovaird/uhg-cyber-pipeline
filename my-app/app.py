# app.py — single-node hardened graph (works with __start__ -> call_model -> __end__)
from dotenv import load_dotenv
load_dotenv()

import os
from typing import Any, Dict, List

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    AIMessage, HumanMessage, SystemMessage, ToolMessage, BaseMessage
)

# -------- LLM base --------
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
BASE_LLM = ChatOpenAI(model=DEFAULT_MODEL, temperature=0, timeout=30)

# -------- helpers --------
def _coerce_role(v: Any) -> str:
    r = (str(v or "")).strip().lower()
    if r in {"user", "human"}: return "human"
    if r in {"assistant", "ai", "bot"}: return "ai"
    if r == "system": return "system"
    if r in {"tool", "function"}: return "tool"
    return "human"

def _to_msg(x: Any) -> BaseMessage:
    if isinstance(x, str):
        return HumanMessage(content=x)
    if not isinstance(x, dict):
        return HumanMessage(content=str(x))
    role = _coerce_role(x.get("role") or x.get("type"))
    # find content in common keys
    content = ""
    for k in ("content", "text", "message"):
        v = x.get(k)
        if isinstance(v, (str, int, float)):
            content = str(v); break
    if role == "system": return SystemMessage(content=content)
    if role == "ai":     return AIMessage(content=content)
    if role == "tool":   return ToolMessage(content=content, tool_call_id=x.get("tool_call_id") or x.get("function_call_id"))
    return HumanMessage(content=content)

def _normalize_payload(maybe: Any) -> Dict[str, Any]:
    """
    Accepts either the raw run payload or just the inner 'input'.
    Tolerates None. Returns {'messages': [...], 'model': <opt>}.
    """
    # step 0: tolerate None
    if maybe is None:
        return {"messages": [AIMessage(content="Input error: missing input. Provide 'message' or 'messages'.")]}
    # step 1: if outer shape contained {"input": {...}}, unwrap/merge
    if isinstance(maybe, dict) and isinstance(maybe.get("input"), dict):
        # merge but favor inner keys
        outer = {k: v for k, v in maybe.items() if k != "input"}
        maybe = {**outer, **maybe["input"]}
    # now parse a message or messages
    if isinstance(maybe, dict):
        # simple string forms
        for k in ("message", "text"):
            v = maybe.get(k)
            if isinstance(v, str) and v.strip():
                out = {"messages": [HumanMessage(content=v)]}
                if isinstance(maybe.get("model"), str): out["model"] = maybe["model"]
                return out
        # list of messages
        msgs = maybe.get("messages")
        if isinstance(msgs, list) and msgs:
            out = {"messages": [_to_msg(m) for m in msgs]}
            if isinstance(maybe.get("model"), str): out["model"] = maybe["model"]
            return out
    # fallback
    return {"messages": [AIMessage(content="Input error: please provide 'message' (string) or 'messages' (list).")]}

# -------- single hardened node --------
def call_model(state: Any) -> Dict[str, Any]:
    # Accept literally anything
    norm = _normalize_payload(state)
    messages: List[BaseMessage] = norm.get("messages") or [HumanMessage(content="(empty)")]
    model_override = norm.get("model")

    # Pick model
    llm = BASE_LLM
    if isinstance(model_override, str) and model_override.strip():
        try:
            llm = ChatOpenAI(model=model_override.strip(), temperature=0, timeout=30)
        except Exception:
            return {"messages": [AIMessage(content=f"OpenAI error: invalid_model. Details: could not initialize `{model_override}`")]}

    # If normalization already produced an AIMessage error, just return it
    if len(messages) == 1 and isinstance(messages[0], AIMessage) and messages[0].content.startswith("Input error:"):
        return {"messages": messages}

    # Call model with shielding
    try:
        result = llm.invoke(messages)  # returns AIMessage
        return {"messages": [result]}
    except Exception as e:
        s = str(e).lower()
        if "insufficient_quota" in s or "exceeded your current quota" in s or "429" in s:
            kind = "insufficient_quota"
        elif "invalid_api_key" in s or "incorrect api key" in s or "401" in s:
            kind = "invalid_api_key"
        elif "rate limit" in s:
            kind = "rate_limited"
        else:
            kind = "unexpected_error"
        return {"messages": [AIMessage(content=f"OpenAI error: {kind}. Details: {e}")]}

# -------- wire graph (single node) --------
builder = StateGraph(dict)  # accept raw dict
builder.add_node("call_model", call_model)
builder.add_edge(START, "call_model")
builder.add_edge("call_model", END)

graph = builder.compile(checkpointer=MemorySaver())

# expose under both names so Studio/CLI hit this graph
assistants = {"agent": graph, "call_model": graph}
app = assistants

print(">>> Loaded hardened SINGLE-NODE app.py from:", __file__, flush=True)
print(">>> Exposed assistants:", list(app.keys()), flush=True)
