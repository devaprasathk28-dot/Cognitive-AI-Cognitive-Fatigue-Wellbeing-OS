import csv
import json
import os
from collections import defaultdict

INPUT_FILE = "data/usage_sessions.csv"
OUTPUT_FILE = "data/cognitive_graph.json"


def load_sessions():

    if not os.path.exists(INPUT_FILE):
        print("Session file not found.")
        return []

    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_transition_graph(sessions):

    graph = defaultdict(lambda: defaultdict(int))

    for i in range(len(sessions) - 1):

        current_app = sessions[i]["app_display_name"]
        next_app = sessions[i + 1]["app_display_name"]

        graph[current_app][next_app] += 1

    return graph


def compute_focus_chains(graph):

    chains = []

    for src in graph:

        for dst in graph[src]:

            weight = graph[src][dst]

            if weight >= 3:
                chains.append({
                    "from": src,
                    "to": dst,
                    "frequency": weight
                })

    return chains


def save_graph(graph, chains):

    data = {
        "graph": graph,
        "focus_chains": chains
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main():

    print("🧠 Cognitive Graph Engine Running")

    sessions = load_sessions()

    if not sessions:
        print("No session data available.")
        return

    graph = build_transition_graph(sessions)

    chains = compute_focus_chains(graph)

    save_graph(graph, chains)

    print("Graph built successfully")
    print(f"Nodes: {len(graph)}")
    print(f"Chains detected: {len(chains)}")


if __name__ == "__main__":
    main()