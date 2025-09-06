import json
from typing import Dict, Any, Tuple, Optional
from github import Github
from configs.settings import settings

def _repo(owner: str, repo: str):
    """Get a specific repository."""
    return Github(settings.GITHUB_TOKEN).get_repo(f"{owner}/{repo}")

def _source_repo():
    """Get the source repository (read-only)."""
    return _repo(settings.SRC_GITHUB_OWNER, settings.SRC_GITHUB_REPO)

def _output_repo():
    """Get the output repository (write-only)."""
    return _repo(settings.OUT_GITHUB_OWNER, settings.OUT_GITHUB_REPO)

def fetch_source_json() -> Tuple[Dict[str, Any], str]:
    """Fetch JSON data from the source repository. Return (data_dict, original_sha)."""
    repo = _source_repo()
    f = repo.get_contents(settings.SRC_GITHUB_JSON_PATH, ref=settings.SRC_GITHUB_BRANCH)
    data = json.loads(f.decoded_content.decode("utf-8"))
    return data, f.sha

def fetch_previous_snapshot() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Fetch the previous snapshot from output repository for comparison."""
    repo = _output_repo()
    try:
        f = repo.get_contents(settings.OUT_GITHUB_JSON_PATH, ref=settings.OUT_GITHUB_BRANCH)
        data = json.loads(f.decoded_content.decode("utf-8"))
        return data, f.sha
    except Exception:
        return None, None  # First run - no previous snapshot exists

def _put_file(repo, path: str, content: str, message: str, branch: str) -> str:
    """Create or update a file in the repository. Returns commit SHA."""
    try:
        existing_file = repo.get_contents(path, ref=branch)
        # Update existing file
        commit = repo.update_file(
            path=path,
            message=message,
            content=content,
            sha=existing_file.sha,
            branch=branch,
        )
    except Exception:
        # Create new file if it doesn't exist
        commit = repo.create_file(
            path=path,
            message=f"{message} (initial creation)",
            content=content,
            branch=branch,
        )
    return commit["commit"].sha

def write_outputs(new_snapshot: Dict[str, Any], delta_doc: Dict[str, Any], 
                 run_id: str, snapshot_id_hint: str = "") -> str:
    """
    Write complete output set: snapshot + latest delta + history + state index.
    
    Args:
        new_snapshot: Full network topology with updated scores
        delta_doc: Change document for UE consumption
        run_id: Timestamp-based run identifier
        snapshot_id_hint: Optional hint for snapshot ID (unused currently)
        
    Returns:
        Commit SHA of the new snapshot
    """
    repo = _output_repo()
    
    # 1. Write main snapshot (full network topology)
    snapshot_content = json.dumps(new_snapshot, ensure_ascii=False, indent=2) + "\n"
    snapshot_sha = _put_file(
        repo, settings.OUT_GITHUB_JSON_PATH, snapshot_content,
        f"pipeline: snapshot {run_id}", settings.OUT_GITHUB_BRANCH
    )
    
    # Update delta doc with actual snapshot ID
    delta_doc["snapshot_id"] = snapshot_sha
    delta_content = json.dumps(delta_doc, ensure_ascii=False, indent=2) + "\n"
    
    # 2. Write latest delta (for UE polling)
    _put_file(
        repo, settings.OUT_CHANGES_LATEST, delta_content,
        f"pipeline: delta {run_id}", settings.OUT_GITHUB_BRANCH
    )
    
    # 3. Write history delta (for debugging/auditing)
    history_path = f"{settings.OUT_CHANGES_HISTORY_DIR}/{run_id}.json"
    _put_file(
        repo, history_path, delta_content,
        f"pipeline: delta history {run_id}", settings.OUT_GITHUB_BRANCH
    )
    
    # 4. Write state index (metadata for UE)
    state_doc = {
        "latest_run_id": run_id,
        "latest_snapshot_id": snapshot_sha,
        "latest_event_id": delta_doc.get("event_seq", 0)
    }
    state_content = json.dumps(state_doc, ensure_ascii=False, indent=2) + "\n"
    _put_file(
        repo, settings.OUT_STATE_INDEX, state_content,
        f"pipeline: state {run_id}", settings.OUT_GITHUB_BRANCH
    )
    
    return snapshot_sha

# Backward compatibility functions (deprecated)
def fetch_json():
    """Deprecated: Use fetch_source_json() instead."""
    return fetch_source_json()

def commit_json(new_data, original_sha, message="pipeline: update threat scores"):
    """Deprecated: Use write_outputs() for full delta tracking capability."""
    output_repo = _output_repo()
    content = json.dumps(new_data, ensure_ascii=False, indent=2) + "\n"
    return _put_file(output_repo, settings.OUT_GITHUB_JSON_PATH, content, message, settings.OUT_GITHUB_BRANCH)
