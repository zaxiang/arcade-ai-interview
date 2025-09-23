"""
Task 1 runner: Identify User Interactions: List out the actions the user did in a human readable format

- Writes interactions.md
- Prints the same lines to stdout
"""
from pathlib import Path
from interactions import read_flow, extract_interactions

def _to_lines(interactions):
    """
    Convert interactions to simple markdown bullet lines.
    """
    return ["- {}".format(i.description) for i in interactions]


def main():
    """
    Identify User Interactions runner
    """
    flow = read_flow("flow.json")
    interactions = extract_interactions(flow)

    print("========== Identifying User Interactions ==========")
    # Print for quick testing
    for line in _to_lines(interactions):
        print(line)

    # Write markdown file
    out_path = Path("interactions.md")
    lines = ["# Interactions", ""]
    lines.extend(_to_lines(interactions))
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote {}".format(out_path.resolve()))

if __name__ == "__main__":
    main()
