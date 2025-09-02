from github import Github
from configs.settings import settings

repo = Github(settings.GITHUB_TOKEN).get_repo(f"{settings.GITHUB_OWNER}/{settings.GITHUB_REPO}")
f = repo.get_contents(settings.GITHUB_JSON_PATH, ref=settings.GITHUB_BRANCH)
print("✅ Read succeeded. Bytes:", len(f.decoded_content))
