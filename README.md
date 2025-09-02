# UHG Cybersecurity Pipeline

End-to-end pipeline that:
- fetches a network graph JSON from GitHub,
- runs a (UHG-aware) ML model for threat scoring,
- writes a scored JSON to a separate output repo consumed by Unreal Engine,
- (optionally) triggers SOAR actions via Swimlane APIs.

## Repos
- **Code (this)**: pipeline + orchestration (LangChain, PyTorch)
- **Output JSON**: https://github.com/zbovaird/Unreal-UHG-Output
- **Unreal project**: https://github.com/zbovaird/Unreal-UHG

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in tokens/keys
python -m scripts.run_once           # dry run
python -m scripts.run_once --commit  # writes to output repo
flowchart TD
    A[Source JSON\nUnreal-UHG/Data/network_topology.json] -->|fetch| B[LangChain Pipeline]
    B --> C[Model (.pth)]
    C --> D[Scores]
    D --> E[Merge/Update JSON]
    E -->|commit| F[Output JSON\nUnreal-UHG-Output/Data/network_topology_scored.json]
    F --> G[Unreal Engine\nVisualization]

Provide a **.env.example** (safe to commit):

```bash
cat > .env.example <<'EOF'
# SOURCE (read)
SRC_GITHUB_OWNER=zbovaird
SRC_GITHUB_REPO=Unreal-UHG
SRC_GITHUB_BRANCH=main
SRC_GITHUB_JSON_PATH=Data/network_topology.json

# OUTPUT (write)
OUT_GITHUB_OWNER=zbovaird
OUT_GITHUB_REPO=Unreal-UHG-Output
OUT_GITHUB_BRANCH=main
OUT_GITHUB_JSON_PATH=Data/network_topology_scored.json

# AUTH
GITHUB_TOKEN=__SET_ME__
OPENAI_API_KEY=__OPTIONAL__

# MODEL
MODEL_PATH=./models/uhg_model.pth

# THRESHOLDS
THREAT_SCORE_THRESHOLD_SUSPICIOUS=0.5
THREAT_SCORE_THRESHOLD_MALICIOUS=0.8
