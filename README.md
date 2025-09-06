# UHG Cybersecurity Pipeline

🛡️ **End-to-end cybersecurity pipeline** that integrates machine learning threat detection with real-time visualization.

## Features

- **🔍 Threat Detection**: ML model analyzes network nodes for security threats
- **🔄 Automated Pipeline**: LangChain orchestrates fetch → analyze → score → commit workflow  
- **🎮 Unreal Integration**: Delta tracking system provides real-time updates to Unreal Engine
- **🤖 LangGraph API**: Interactive chat interface for pipeline monitoring and control
- **🚨 SOAR Ready**: Future integration with Swimlane for automated response actions
- **🧪 Safe Testing**: Test mode that doesn't affect production data
- **📊 Change Tracking**: Sophisticated delta detection for efficient Unreal Engine updates

## Architecture

```mermaid
flowchart TD
    A[Source JSON<br/>Unreal-UHG/network_topology.json] -->|fetch| B[LangChain Pipeline]
    B --> C[Model Loader<br/>(pipeline/model.py)]
    C --> D[Inference<br/>(generate threat scores)]
    D --> E[Scoring + Update<br/>(pipeline/update_json.py)]
    E -->|commit| F[Output JSON<br/>Unreal-UHG-Output/network_topology_scored.json]
    E --> G[Swimlane API<br/>(optional trigger)]
    F --> H[Unreal Engine<br/>Visualize nodes/edges]
```

## Quick Start

### 1. Setup Environment
```bash
git clone <this-repo>
cd uhg-cyber-pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Create .env file with dual-repository configuration
# See instructions.md for complete .env template
```

### 3. Run Pipeline
```bash
python scripts/run_once.py           # dry run
python scripts/run_once.py --commit  # commit results
python scripts/run_safe.py --commit  # safe test mode
```

### 4. Start LangGraph Server (Optional)
```bash
cd my-app && source ../.venv/bin/activate
PYTHONUNBUFFERED=1 langgraph dev
# Server runs on http://localhost:2024
```

## Repository Links

- **🔧 Pipeline Code**: This repository
- **📊 Data Source**: [Unreal-UHG](https://github.com/zbovaird/Unreal-UHG) (original network topology)
- **📤 Data Output**: [Unreal-UHG-Output](https://github.com/zbovaird/Unreal-UHG-Output) (scored results)
- **🎮 Visualization**: Unreal Engine project consuming the scored JSON data

## Documentation

📖 **[Complete Setup & Usage Guide](instructions.md)** - Detailed documentation with:
- Step-by-step setup instructions
- LangGraph dev server setup and troubleshooting
- Delta tracking system for Unreal Engine
- Configuration options and environment setup
- Development phases roadmap
- Integration details and API testing
