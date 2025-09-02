import argparse
from pipeline.chains import build_chain, commit_result

def main(do_commit: bool):
    chain = build_chain()
    state = chain.invoke(None)

    sample_scores = list(state["scores"].items())[:5]
    print("Sample scores:", sample_scores)

    first_node = (state["new_data"].get("nodes") or [{}])[0]
    print("First node keys now include:", sorted(first_node.keys()))

    if do_commit:
        sha = commit_result(state, message="pipeline: update threat scores (stub model)")
        print("✅ Committed:", sha)
    else:
        print("🧪 Dry run only. Use --commit to write to GitHub.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--commit", action="store_true")
    args = p.parse_args()
    main(args.commit)
