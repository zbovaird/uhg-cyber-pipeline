from dotenv import load_dotenv; load_dotenv()  # loads .env in this folder

from langgraph.graph import StateGraph, MessagesState
from langchain_openai import ChatOpenAI

# Use any model you have access to. gpt-4o-mini is a good default.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def chat(state: MessagesState):
    resp = llm.invoke(state["messages"])
    return {"messages": state["messages"] + [resp]}

graph = StateGraph(MessagesState)
graph.add_node("chat", chat)
graph.set_entry_point("chat")
graph.set_finish_point("chat")
app = graph.compile()
