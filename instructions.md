# UHG Cybersecurity Pipeline Project

## Purpose

This project integrates:
- **LangChain** → Orchestration & automation of the inference pipeline.
- **Custom-trained ML model** → Exported from Google Colab as `.pth`, loaded locally for inference.
- **Unreal Engine** → Visualizes the network graph, consuming a JSON file hosted in GitHub.
- **GitHub JSON** → Stores node/edge data, updated by the pipeline with threat scores.
- **Swimlane (API-only)** → Future integration for SOAR actions (isolation, enrichment, etc.).

The goal is to **classify each network node (benign / suspicious / malicious)** and update the JSON that Unreal reads in real-time.

## Project Structure

```
uhg-cyber-pipeline/
├── configs/
│   └── settings.py          # Configuration settings
├── pipeline/
│   ├── __init__.py
│   ├── io_github.py         # GitHub integration
│   ├── model.py             # ML model loading and inference
│   ├── scoring.py           # Threat scoring logic
│   ├── update_json.py       # JSON data manipulation
│   └── chains.py            # Pipeline orchestration
├── scripts/
│   └── run_once.py          # Main execution script
├── .env                     # Environment variables (not in git)
└── instructions.md          # This file
```

---

## Current State (✅ completed)
1. Python project environment created (`.venv` with dependencies installed).
2. `.env` file configured with:
   - `OPENAI_API_KEY`
   - `GITHUB_TOKEN` (classic PAT, repo: `Unreal-UHG`, **Contents: Read & Write**).
3. Pipeline scaffolding built:
   - `pipeline/io_github.py` → Pull/push JSON via GitHub API.
   - `pipeline/model.py` → Stub inference (deterministic placeholder).
   - `pipeline/scoring.py` → Map scores → benign/suspicious/malicious.
   - `pipeline/update_json.py` → Merge results back into JSON.
   - `pipeline/chains.py` → LangChain glue (RunnableSequence).
   - `scripts/run_once.py` → CLI runner (dry-run or commit).
4. Successfully tested:
   - `python scripts/run_once.py` → Dry run fetch/infer/merge.
   - `python scripts/run_once.py --commit` → Writes updated JSON to repo.

---

## Next Steps (🚀 upcoming work)

### Phase 2 – Model Integration
- Export `.pth` model from Google Colab into `/models/uhg_model.pth`.
- Update `pipeline/model.py`:
  - Load the real model with `torch.load`.
  - Implement feature extraction from JSON node fields → input tensor.
  - Run inference, return `{node_id: threat_score}`.

### Phase 3 – Safe Testing
- Add a script `scripts/run_safe.py`:
  - Writes results to `Data/pipeline_write_test.json` instead of overwriting `network_topology.json`.
  - Use this while iterating on model loading to avoid breaking Unreal.

### Phase 4 – Automation
- Add `scripts/serve_webhook.py`:
  - FastAPI endpoint (`/run`) to trigger pipeline externally.
- Add scheduling with `apscheduler`:
  - Run every X minutes, or triggered by GitHub Actions.

### Phase 5 – Swimlane Integration
- Add `pipeline/triggers.py`:
  - When a node status changes to `suspicious` or `malicious`, call Swimlane REST API (authenticated with `SWIMLANE_API_KEY`).
- This allows automated SOAR actions (isolation, enrichment, etc.).

---

## Setup

### 1. Activate Virtual Environment

```bash
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install pydantic-settings PyGithub langchain-core torch python-dotenv
```

### 3. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Source Repository Configuration (READ-ONLY)
# This is where the pipeline reads the original network topology data
SRC_GITHUB_OWNER=zbovaird
SRC_GITHUB_REPO=Unreal-UHG
SRC_GITHUB_JSON_PATH=Data/network_topology.json
SRC_GITHUB_BRANCH=main

# Output Repository Configuration (WRITE-ONLY)  
# This is where the pipeline writes the scored/analyzed data for Unreal Engine
OUT_GITHUB_OWNER=zbovaird
OUT_GITHUB_REPO=Unreal-UHG-Output
OUT_GITHUB_JSON_PATH=Data/network_topology_scored.json
OUT_GITHUB_BRANCH=main

# Authentication
GITHUB_TOKEN=ghp_your_classic_token_here

# OpenAI Configuration (for future LangChain features)
OPENAI_API_KEY=your_openai_key_here

# Model Configuration
MODEL_PATH=./models/uhg_model.pth
THREAT_SCORE_THRESHOLD_SUSPICIOUS=0.5
THREAT_SCORE_THRESHOLD_MALICIOUS=0.8

# Future: Swimlane Integration
# SWIMLANE_API_KEY=your_swimlane_key_here
# SWIMLANE_BASE_URL=https://your-instance.swimlane.com
```

**Important**: Use a **Classic Personal Access Token** with `repo` scope, not a fine-grained token.

### 4. GitHub Token Setup

1. Go to [GitHub Settings → Personal Access Tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select the **`repo`** scope (full repository access)
4. Copy the token and add it to your `.env` file

---

## Data Flow Diagram

```mermaid
flowchart TD
    A[GitHub JSON<br/>(network_topology.json)] -->|fetch| B[LangChain Pipeline]
    B --> C[Model Loader<br/>(pipeline/model.py)]
    C --> D[Inference<br/>(generate threat scores)]
    D --> E[Scoring + Update<br/>(pipeline/update_json.py)]
    E -->|commit| A
    E --> F[Swimlane API<br/>(optional trigger)]
    A --> G[Unreal Engine<br/>Visualize nodes/edges]
```

---

## LangGraph Dev Server Setup

### Clean Relaunch & Smoke Test

#### 0) Prerequisites

- **Project root:** `~/Projects/uhg-cyber-pipeline`
- **App folder:** `~/Projects/uhg-cyber-pipeline/my-app`
- **Virtualenv:** `~/Projects/uhg-cyber-pipeline/.venv`

#### 1) Environment Configuration

Create/update `~/Projects/uhg-cyber-pipeline/.env`:

```bash
# OpenAI
OPENAI_API_KEY=sk-proj_...           # from the funded project
OPENAI_MODEL=gpt-4o-mini

# (Optional) LangSmith tracing
LANGSMITH_API_KEY=lsv2_...           # optional
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=uhg-demo

# For libs that still read these names:
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=${LANGSMITH_API_KEY}
LANGCHAIN_ENDPOINT=${LANGSMITH_ENDPOINT}
```

⚠️ **Tip:** Keep `.env` out of git.

#### 2) Start Server (Terminal A)

```bash
# Kill anything old
lsof -ti :2024 | xargs -r kill -9
lsof -ti :2030 | xargs -r kill -9

# Go to the app & activate venv
cd ~/Projects/uhg-cyber-pipeline/my-app
source ../.venv/bin/activate

# Optional: clear bytecode
find . -name '__pycache__' -type d -prune -exec rm -rf {} +

# Launch the server (PYTHONUNBUFFERED prints logs immediately)
PYTHONUNBUFFERED=1 langgraph dev
```

If you need to force the module export explicitly:
```bash
PYTHONUNBUFFERED=1 LANGGRAPH_APP=app:app langgraph dev --app app:app
```

#### 3) Verify API (Terminal B)

```bash
API=http://127.0.0.1:2024

# Health check
curl -s "$API/ok"; echo

# Discover assistant
ASSIST_JSON=$(curl -s "$API/assistants/search" \
  -H "Content-Type: application/json" \
  -d '{"query": ""}')
echo "$ASSIST_JSON" | jq

ASSIST_ID=$(echo "$ASSIST_JSON" | jq -r '.[0].assistant_id')
GRAPH_ID=$(echo "$ASSIST_JSON" | jq -r '.[0].graph_id')
echo "ASSIST_ID=$ASSIST_ID  GRAPH_ID=$GRAPH_ID"

# (Optional) See the graph nodes
curl -s "$API/assistants/$ASSIST_ID/graph" | jq '.nodes[].id'

# Make a thread
THREAD_ID=$(curl -s -X POST "$API/threads" -H "Content-Type: application/json" -d '{}' | jq -r '.thread_id')
echo "THREAD_ID=$THREAD_ID"

# Run a simple turn (happy path)
RUN_ID=$(curl -s -X POST "$API/threads/$THREAD_ID/runs" \
  -H "Content-Type: application/json" \
  -d '{"assistant_id":"'"$ASSIST_ID"'","input":{"messages":[{"role":"user","content":"Say hi in one line."}]}}' \
  | jq -r '.run_id')

# Check status + last message
curl -s "$API/threads/$THREAD_ID/runs/$RUN_ID" | jq '.status'
curl -s "$API/threads/$THREAD_ID/state" | jq -r '.values.messages[-1].content'
```

You should see `status: "success"` and a one-line reply.

#### 4) Quick One-Liner (copy/paste to restart fast)

```bash
lsof -ti :2024 | xargs -r kill -9; lsof -ti :2030 | xargs -r kill -9; \
cd ~/Projects/uhg-cyber-pipeline/my-app && source ../.venv/bin/activate && \
PYTHONUNBUFFERED=1 langgraph dev
```

#### 5) Troubleshooting

- **Brown LangSmith banner:** Server env doesn't see `LANGSMITH_API_KEY`. Export it in the same terminal you start the server, or put it in `.env` and ensure your app calls `load_dotenv()`.

- **429 insufficient_quota:** Make sure the key is from the funded project; check project/org budgets > $0; keep `gpt-4o-mini`.

- **'NoneType' object has no attribute 'get':** You're running an old app module. Ensure your hardened node is in use (our current code normalizes input and catches errors). If needed, start with `--app app:app`.

---

## Running the Cybersecurity Pipeline

### Activate Virtual Environment
```bash
source .venv/bin/activate
```

### Run Pipeline (Dry Run)

Test the pipeline without committing changes:

```bash
python scripts/run_once.py
```

This will:
- Fetch data from GitHub (`Data/network_topology.json`)
- Generate threat scores using the stub model
- Show sample results
- Display what would be committed

### Run Pipeline (With Commit)

Execute the full pipeline and commit results:

```bash
python scripts/run_once.py --commit
```

This will:
- Fetch the latest network topology data
- Generate threat scores for all nodes
- Add `threat_score` and `status` fields to each node
- Commit the updated data back to GitHub for Unreal Engine consumption

## Pipeline Components

### 1. Data Fetching (`pipeline/io_github.py`)
- Connects to GitHub repository
- Fetches JSON data from specified path
- Retrieves current file SHA for updates

### 2. Model Inference (`pipeline/model.py`)
- **Current**: Stub inference with deterministic placeholder scores
- **Future**: Load real `.pth` model from Google Colab
- Processes network nodes and generates threat scores (0.0 to 1.0 range)

### 3. Scoring Logic (`pipeline/scoring.py`)
- Converts numerical scores to status categories:
  - `benign`: score < 0.5
  - `suspicious`: 0.5 ≤ score < 0.8
  - `malicious`: score ≥ 0.8

### 4. Data Updates (`pipeline/update_json.py`)
- Merges threat scores into original data
- Adds timestamps
- Preserves existing data structure

### 5. Pipeline Orchestration (`pipeline/chains.py`)
- Coordinates the entire workflow using LangChain RunnableSequence
- Handles fetch → infer → merge → commit pipeline
- Provides state management between pipeline steps

## Configuration Options

### Threat Score Thresholds

Modify in your `.env` file:

```bash
THREAT_SCORE_THRESHOLD_SUSPICIOUS=0.5
THREAT_SCORE_THRESHOLD_MALICIOUS=0.8
```

### Model Path

Specify custom model location:

```bash
MODEL_PATH=./models/custom_model.pth
```

## Output Format

The pipeline adds these fields to each network node:

```json
{
  "id": "node_123",
  "threat_score": 0.75,
  "status": "suspicious",
  // ... existing fields preserved
}
```

## Troubleshooting

### Common Issues

1. **403 Forbidden Error**
   - Ensure you're using a Classic Personal Access Token
   - Verify the token has `repo` scope
   - Check that the repository path is correct

2. **Module Not Found**
   - Install missing dependencies: `pip install <package-name>`
   - Ensure you're in the project directory

3. **File Not Found**
   - Verify `GITHUB_JSON_PATH` in `.env` is correct
   - Check that the file exists in the repository

### Debug Mode

For detailed debugging, you can modify the scripts to add more logging or create custom test scripts.

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- Use Classic Personal Access Tokens for better compatibility
- Regularly rotate your GitHub tokens
- Monitor repository access logs

## Development

### Current Architecture
- **LangChain**: Orchestrates the pipeline workflow
- **PyTorch**: Model loading and inference (stub implementation)
- **GitHub API**: Data source and target for Unreal Engine
- **Pydantic**: Configuration management

### Future Integrations
1. **Real ML Model**: Replace stub with trained model from Google Colab
2. **Safe Testing**: `scripts/run_safe.py` for testing without breaking Unreal
3. **Automation**: FastAPI webhook + scheduling for continuous operation
4. **SOAR Integration**: Swimlane API for automated response actions

### Adding New Features

1. **New scoring algorithms**: Modify `pipeline/scoring.py`
2. **Different data sources**: Extend `pipeline/io_github.py`
3. **Custom models**: Update `pipeline/model.py`
4. **Pipeline steps**: Modify `pipeline/chains.py`
5. **SOAR triggers**: Add `pipeline/triggers.py` for Swimlane integration

### Testing

Always test changes with dry runs before committing:

```bash
python scripts/run_once.py  # Test without commit
```

## Integration Points

### Unreal Engine
- Consumes: `Data/network_topology.json` from GitHub
- Expects: Node objects with `threat_score` and `status` fields
- Updates: Real-time visualization based on threat classifications

### Google Colab
- Exports: Trained `.pth` model files
- Target: `/models/uhg_model.pth` in this project

### Output Repository Options

**Current Implementation**: Separate repository approach ✅
- **Source**: `zbovaird/Unreal-UHG/Data/network_topology.json` (read-only)
- **Output**: `zbovaird/Unreal-UHG-Output/Data/network_topology_scored.json` (write-only)
- **Unreal Engine URL**: `https://raw.githubusercontent.com/zbovaird/Unreal-UHG-Output/main/Data/network_topology_scored.json`

### Setup Steps:
1. **Create Output Repository**: Create a new GitHub repository named `Unreal-UHG-Output`
2. **Configure Environment**: Use the dual-repository `.env` configuration shown above
3. **Update Unreal Engine**: Point your Unreal Engine project to the new output URL
4. **Run Pipeline**: The pipeline will automatically read from source and write to output repo

---

## Delta Tracking for Unreal Engine Integration

The pipeline now provides **real-time change detection** to enable Unreal Engine to:
- **Expand networks** containing changed nodes (collapsed by default)
- **Focus camera** on high-priority threats
- **Efficiently update** visualization without full reloads

### Output Structure

The pipeline writes to your `Unreal-UHG-Output` repository with this structure:

```
Data/
├── network_topology_scored.json        # Full snapshot (current state)
├── changes/
│   ├── latest.json                     # Latest delta feed for UE polling
│   └── history/
│       └── 2025-01-15T14-22-10Z.json   # Immutable per-run deltas
└── state/
    └── index.json                      # Metadata pointers
```

### Snapshot Format (`network_topology_scored.json`)

Full network topology with enhanced node data:

```json
{
  "nodes": [
    {
      "id": "node_42",
      "network_id": "net_a",
      "label": "srv-42",
      "threat_score": 0.83,
      "status": "malicious",
      "version": 7,
      "updated_at": "2025-01-15T14:22:10Z",
      // ... original node properties preserved
    }
  ],
  "edges": [...],
  "updated_at": "2025-01-15T14:22:10Z"
}
```

### Delta Feed Format (`changes/latest.json`)

Only changed nodes with before/after states:

```json
{
  "run_id": "2025-01-15T14-22-10Z",
  "snapshot_id": "164fab69b35d...",
  "generated_at": "2025-01-15T14:22:10Z",
  "changes": [
    {
      "entity": "node",
      "id": "node_42",
      "network_id": "net_a",
      "prev": { 
        "threat_score": 0.62, 
        "status": "suspicious", 
        "version": 6 
      },
      "curr": { 
        "threat_score": 0.83, 
        "status": "malicious", 
        "version": 7 
      },
      "threshold_crossed": true,
      "reason": "status_change",
      "updated_at": "2025-01-15T14:22:10Z"
    }
  ],
  "event_seq": 1
}
```

### State Index (`state/index.json`)

Metadata for UE polling optimization:

```json
{
  "latest_run_id": "2025-01-15T14-22-10Z",
  "latest_snapshot_id": "164fab69b35d...",
  "latest_event_id": 1
}
```

### Unreal Engine Integration

#### Polling Strategy

1. **Poll `changes/latest.json`** every X seconds with cache-busting:
   ```
   https://raw.githubusercontent.com/zbovaird/Unreal-UHG-Output/main/Data/changes/latest.json?v=<timestamp>
   ```

2. **Check `run_id`** - if different from last seen:
   - Process `changes` array (sorted by priority)
   - For each change: expand `network_id` and focus on `id`
   - Store new `run_id` to avoid reprocessing

3. **Fetch full snapshot** if needed:
   ```
   https://raw.githubusercontent.com/zbovaird/Unreal-UHG-Output/main/Data/network_topology_scored.json
   ```

#### Blueprint/C++ Logic

```cpp
// Pseudo-code for UE integration
void PollForChanges() {
    string latestDelta = FetchURL("Data/changes/latest.json?v=" + GetTimestamp());
    auto deltaDoc = ParseJSON(latestDelta);
    
    if (deltaDoc.run_id != lastProcessedRunId) {
        for (auto& change : deltaDoc.changes) {
            if (change.threshold_crossed) {
                ExpandNetwork(change.network_id);
                FocusCamera(change.id);
                
                // Optional: Flash/highlight the node
                HighlightNode(change.id, change.curr.status);
            }
        }
        lastProcessedRunId = deltaDoc.run_id;
    }
}
```

### Change Detection Logic

The pipeline detects changes by:

1. **Version Tracking**: Each node has a `version` number incremented on changes
2. **Score Thresholds**: Significant score changes (≥0.2) trigger alerts  
3. **Status Changes**: Any status transition (benign ↔ suspicious ↔ malicious)
4. **Priority Sorting**: Threshold crossings ranked higher than minor score changes

### Environment Configuration

Add these to your `.env` file:

```bash
# Delta tracking paths (already configured)
OUT_CHANGES_LATEST=Data/changes/latest.json
OUT_CHANGES_HISTORY_DIR=Data/changes/history  
OUT_STATE_INDEX=Data/state/index.json
```

### Swimlane (Future)
- Triggers: Automated SOAR actions on threat detection
- Authentication: `SWIMLANE_API_KEY` in `.env`
- Actions: Node isolation, enrichment, incident creation

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your `.env` configuration
3. Test with dry runs first
4. Review GitHub repository permissions

## Version History

- **v1.0**: Initial pipeline implementation with stub model
- **Current**: Basic threat scoring and GitHub integration
- **Next**: Real model integration and safe testing framework
