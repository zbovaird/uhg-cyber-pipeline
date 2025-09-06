"""LangGraph message-handling graph for chat API.

Handles messages from the LangGraph API and returns responses.
"""

from __future__ import annotations

from typing import Any, Dict, List, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
import os


class Context(TypedDict):
    """Context parameters for the agent."""
    model: str


class State(TypedDict):
    """State for message handling."""
    messages: List[BaseMessage]


# Initialize the LLM
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0
)


async def call_model(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Process messages and return AI response."""
    try:
        messages = state.get("messages", [])
        
        # If no messages, return a default response
        if not messages:
            return {
                "messages": messages + [AIMessage(content="Hello! How can I help you?")]
            }
        
        # Call the LLM with the messages
        response = await llm.ainvoke(messages)
        
        return {
            "messages": messages + [response]
        }
    except Exception as e:
        # Return error message instead of crashing
        error_msg = f"Error processing request: {str(e)}"
        return {
            "messages": state.get("messages", []) + [AIMessage(content=error_msg)]
        }


# Define the graph
graph = (
    StateGraph(State, context_schema=Context)
    .add_node("call_model", call_model)
    .add_edge("__start__", "call_model")
    .add_edge("call_model", "__end__")
    .compile(name="Chat Agent")
)
