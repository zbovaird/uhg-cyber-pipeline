import json
from github import Github
from configs.settings import settings

def _repo():
    return Github(settings.GITHUB_TOKEN).get_repo(
        f"{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}"
    )

def fetch_json():
    """Return (data_dict, sha)."""
    repo = _repo()
    f = repo.get_contents(settings.GITHUB_JSON_PATH, ref=settings.GITHUB_BRANCH)
    data = json.loads(f.decoded_content.decode("utf-8"))
    return data, f.sha

def commit_json(new_data, sha, message="pipeline: update threat scores"):
    repo = _repo()
    content = json.dumps(new_data, ensure_ascii=False, indent=2) + "\n"
    commit = repo.update_file(
        path=settings.GITHUB_JSON_PATH,
        message=message,
        content=content,
        sha=sha,
        branch=settings.GITHUB_BRANCH,
    )
    return commit["commit"].sha
