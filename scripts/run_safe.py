#!/usr/bin/env python3
"""
Safe testing script that writes to a separate test file to avoid breaking Unreal Engine.
Use this while iterating on model loading and testing new features.
"""

import argparse
from pipeline.chains import build_chain
from pipeline.io_github import commit_json
from configs.settings import settings

def commit_safe_result(state, message="pipeline: safe test run"):
    """Commit results to a separate test file instead of the main data file."""
    # Use a test file path instead of the main network_topology.json
    test_path = "Data/pipeline_write_test.json"
    
    # Temporarily override the JSON path for safe testing
    original_path = settings.GITHUB_JSON_PATH
    settings.GITHUB_JSON_PATH = test_path
    
    try:
        return commit_json(state["new_data"], state["sha"], message=message)
    finally:
        # Restore original path
        settings.GITHUB_JSON_PATH = original_path

def main(do_commit: bool):
    """Run the pipeline safely without affecting the main data file."""
    print("🧪 Running SAFE test mode")
    print(f"📁 Main file: {settings.GITHUB_JSON_PATH}")
    print("📁 Test output: Data/pipeline_write_test.json")
    print()
    
    chain = build_chain()
    state = chain.invoke(None)

    sample_scores = list(state["scores"].items())[:5]
    print("Sample scores:", sample_scores)

    first_node = (state["new_data"].get("nodes") or [{}])[0]
    print("First node keys now include:", sorted(first_node.keys()))

    if do_commit:
        sha = commit_safe_result(state, message="pipeline: safe test run (stub model)")
        print("✅ Safe test committed to Data/pipeline_write_test.json:", sha)
        print("🔒 Main data file (network_topology.json) unchanged")
    else:
        print("🧪 Dry run only. Use --commit to write test file to GitHub.")
        print("🔒 Main data file (network_topology.json) unchanged")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run pipeline safely without affecting main data")
    p.add_argument("--commit", action="store_true", help="Commit to test file")
    args = p.parse_args()
    main(args.commit)

