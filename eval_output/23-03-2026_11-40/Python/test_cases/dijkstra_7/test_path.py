import heapq
import pytest
from graphs.dijkstra import dijkstra

# Helper graphs for testing
G = {
    "A": [("B", 2), ("C", 5)],
    "B": [("A", 2), ("C", 1)],
    "C": [("A", 5), ("B", 1)],
    "E": [("C", 6)],
    "D": []
}
G2 = {
    "E": [("F", 3)],
    "F": []
}
G3 = {
    "E": [("D", 1), ("F", 3)],
    "D": [("F", 1)],
    "F": []
}
G_DISCONNECTED = {
    "A": [("B", 1)],
    "B": [],
    "C": [("D", 2)],
    "D": []
}
G_SINGLE = {
    "A": []
}

# Path enumeration:
# 1. Outer while loop: heap non‑empty (True) or empty (False)
# 2. Inside while: u in visited? (True → continue, False → proceed)
# 3. After visited.add(u): u == end? (True → return cost, False → proceed)
# 4. Inner for loop over graph[u]: zero iterations, one iteration, many iterations
# 5. Inside for: v in visited? (True → continue, False → push)
# Combined feasible paths:

# Path 1: heap empty at start → while False → return -1
# graph with start node not present (or start node has no entry)
# Actually, if start not in graph, graph[u] in for loop will raise KeyError.
# So we need a graph where start exists but heap becomes empty immediately.
# That's impossible because heap is initialized with (0, start).
# Therefore this path is infeasible. Skip.

# Path 2: heap non‑empty → u already visited → continue → loop again (same path) → eventually heap empty → return -1
def test_dijkstra_all_visited_never_reach_end():
    # We need a case where we keep popping visited nodes until heap empties.
    # This happens if we push duplicates and visited prevents progress.
    graph = {"A": [("B", 1)], "B": []}
    # Start at A, end at C (unreachable). We'll push B, but if we later push B again
    # with higher cost, it will be visited already.
    # Actually, the algorithm only pushes each neighbor once per discovery? No, it can push multiple times.
    # Let's craft: start A, end C. Graph: A->B, B->A (cycle). We'll eventually visit A, B, then heap empties.
    graph_cycle = {"A": [("B", 1)], "B": [("A", 2)]}
    assert dijkstra(graph_cycle, "A", "C") == -1

# Path 3: heap non‑empty → u not visited → u == end → return cost (immediate, no inner loop)
def test_dijkstra_start_equals_end():
    # start == end, heap has (0, start), pop, not visited, u == end → return 0
    assert dijkstra(G_SINGLE, "A", "A") == 0

# Path 4: heap non‑empty → u not visited → u != end → inner loop zero iterations → loop again → eventually heap empty → return -1
def test_dijkstra_no_neighbors_unreachable_end():
    # start has no neighbors, end different, heap becomes empty after one pop
    assert dijkstra(G_SINGLE, "A", "B") == -1

# Path 5: heap non‑empty → u not visited → u != end → inner loop one iteration → v already visited → continue → loop again → eventually heap empty → return -1
# start A, neighbor B, but B already visited (how? we need to push B twice with different costs)
# Actually, visited starts empty. To have v visited, we need to have popped v earlier.
# So we need a graph where we go start -> neighbor, then later pop neighbor again (duplicate in heap).
# graph = {"A": [("B", 1)], "B": []}
# We'll manually interfere? Not possible without modifying function.
# Instead, consider a graph where B is reachable from another path? Not here.
# This path may be infeasible for simple graphs. Skip.

# Path 6: heap non‑empty → u not visited → u != end → inner loop one iteration → v not visited → push → loop again → eventually reach end → return cost
def test_dijkstra_direct_edge():
    # start E, end F, direct edge cost 3
    assert dijkstra(G2, "E", "F") == 3

# Path 7: heap non‑empty → u not visited → u != end → inner loop many iterations → mix of visited and unvisited neighbors → pushes → loop again → eventually reach end → return cost
def test_dijkstra_multiple_neighbors():
    # start E in G3, end F, two neighbors D and F
    # The shortest path is E -> D -> F = 1 + 1 = 2, not the direct edge E -> F = 3.
    assert dijkstra(G3, "E", "F") == 2

# Path 8: heap non‑empty → u not visited → u != end → inner loop many iterations → all neighbors already visited → no pushes → loop again → heap empty → return -1
def test_dijkstra_all_neighbors_visited_unreachable():
    # start A, neighbors B and C, but B and C already visited, end D unreachable
    # Need to set up visited state by earlier pops.
    # Use a graph with a cycle where we revisit nodes.
    graph = {
        "A": [("B", 1), ("C", 2)],
        "B": [("A", 1)],
        "C": [("A", 2)],
        "D": []
    }
    # Start A, end D. We'll visit A, then B (pushes A again), then C (pushes A again), then heap empties.
    assert dijkstra(graph, "A", "D") == -1

# Path 9: heap non‑empty → u not visited → u != end → inner loop zero iterations → loop again → next node is end → return cost
# start A, end B, but A has no edges, B separate node → unreachable, so not this path.
# Instead, consider graph where first node has no neighbors, second node (popped later) is end.
# That requires heap to have multiple entries initially? Only one initial entry.
# So we need a graph where start has no neighbors, but we push another node from somewhere else? Not possible.
# This path may be infeasible. Skip.

# Path 10: heap non‑empty → u not visited → u != end → inner loop one iteration → v not visited → push → later pop v → v == end → return cost
def test_dijkstra_one_hop():
    graph = {"A": [("B", 5)], "B": []}
    assert dijkstra(graph, "A", "B") == 5

# Path 11: heap non‑empty → u not visited → u != end → inner loop many iterations → some visited, some not → pushes → later pop one of them → that node == end → return cost
def test_dijkstra_complex_path():
    # Use G from docstring: start E, end C, path E->C cost 6
    assert dijkstra(G, "E", "C") == 6

# Additional path: loop multiple times with mixed continue/ push patterns until end found.
# Already covered by above tests.

# Summary of written tests:
# 1. All visited until heap empty (path 2)
# 2. Start equals end (path 3)
# 3. No neighbors, unreachable end (path 4)
# 4. Direct edge (path 6)
# 5. Multiple neighbors (path 7)
# 6. All neighbors visited, unreachable (path 8)
# 7. One hop (path 10)
# 8. Complex multi‑node (path 11)

# Note: Some enumerated paths were infeasible and skipped.