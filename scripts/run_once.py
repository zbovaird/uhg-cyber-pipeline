import argparse
from datetime import datetime, timezone

from pipeline.chains import build_chain
from pipeline.io_github import fetch_previous_snapshot, write_outputs
from pipeline.diff import compute_changes

def main(do_commit: bool):
    """
    Main pipeline execution with delta tracking for Unreal Engine integration.
    
    Generates both full snapshots and change deltas to enable UE to:
    1. Expand networks with changed nodes
    2. Focus camera on high-priority threats
    3. Efficiently update visualization without full reload
    """
    # Build current result (source → infer → merge)
    chain = build_chain()
    state = chain.invoke(None)
    new_snapshot = state["new_data"]

    # Compare with previous snapshot from output repository
    prev_snapshot, _ = fetch_previous_snapshot()
    changes = compute_changes(prev_snapshot or {"nodes": []}, new_snapshot, delta_min=0.0)

    # Generate run metadata
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    delta_doc = {
        "run_id": run_id,
        "snapshot_id": "",  # Will be filled by write_outputs with actual commit SHA
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "changes": changes,
        "event_seq": len(changes)
    }

    # Display summary
    print(f"🔍 Detected {len(changes)} changed entities")
    
    if changes:
        # Show most significant changes (threshold crossings first)
        priority_changes = [c for c in changes[:3] if c.get("threshold_crossed")]
        if priority_changes:
            print("🚨 Priority changes (threshold crossings):")
            for change in priority_changes:
                node_id = change["id"]
                prev_status = change["prev"]["status"] if change["prev"] else "new"
                curr_status = change["curr"]["status"]
                score = change["curr"]["threat_score"]
                print(f"   - {node_id}: {prev_status} → {curr_status} (score: {score:.2f})")
        
        print("📊 Sample changes:", changes[:3])
    else:
        print("✨ No significant changes detected")

    # Show current state
    sample_scores = list(state["scores"].items())[:5]
    print("📈 Sample scores:", sample_scores)

    first_node = (new_snapshot.get("nodes") or [{}])[0]
    if first_node:
        print("🔧 Node fields:", sorted(first_node.keys()))

    if do_commit:
        # Write complete output set for UE consumption
        snapshot_sha = write_outputs(new_snapshot, delta_doc, run_id)
        print(f"✅ Pipeline complete!")
        print(f"   📸 Snapshot: {snapshot_sha}")
        print(f"   📡 Delta feed: Data/changes/latest.json")
        print(f"   🎮 UE URL: https://raw.githubusercontent.com/{state.get('OUT_GITHUB_OWNER', 'zbovaird')}/Unreal-UHG-Output/main/Data/network_topology_scored.json")
    else:
        print("🧪 Dry run only. Use --commit to write to GitHub.")
        print("   Next: python scripts/run_once.py --commit")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="UHG Cybersecurity Pipeline with Delta Tracking")
    p.add_argument("--commit", action="store_true", 
                   help="Commit results to output repository (otherwise dry run)")
    args = p.parse_args()
    main(args.commit)
