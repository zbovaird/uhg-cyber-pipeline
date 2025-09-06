from typing import Dict, Any
from langchain_core.runnables import RunnableLambda, RunnableSequence
from pipeline.io_github import fetch_source_json, commit_json
from pipeline.model import load_model, infer_nodes
from pipeline.update_json import merge_scores

def build_chain():
    def _fetch(_):
        data, sha = fetch_source_json()
        return {"data": data, "sha": sha}

    def _infer(state):
        model, device = load_model()
        scores = infer_nodes(model, device, state["data"].get("nodes", []))
        state["scores"] = scores
        return state

    def _merge(state):
        state["new_data"] = merge_scores(state["data"], state["scores"])
        return state

    return RunnableSequence(
        RunnableLambda(_fetch),
        RunnableLambda(_infer),
        RunnableLambda(_merge),
    )

def commit_result(state: Dict[str, Any], message: str = "pipeline: update threat scores"):
    return commit_json(state["new_data"], state["sha"], message=message)
