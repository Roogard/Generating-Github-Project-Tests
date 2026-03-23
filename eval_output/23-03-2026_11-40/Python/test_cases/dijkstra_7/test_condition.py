from graphs.dijkstra import dijkstra

# condition: while heap: True (loop runs) and False (loop doesn't run)
def test_empty_graph_start_equals_end():
    # while heap: True initially, then after popping, heap becomes empty, loop condition becomes False
    graph = {}
    # start == end, so u == end: True, returns cost 0 without exploring neighbors
    assert dijkstra(graph, "A", "A") == 0

# condition: u in visited: True (skip) and False (process)
def test_node_already_visited():
    # while heap: True
    # u in visited: False for first pop, True for second pop (skip)
    graph = {"A": [("B", 1)], "B": []}
    # Start at A, cost 0, visited {A}, push B with cost 1
    # Pop B, cost 1, B not visited, B == end? No, process neighbors (none)
    # Pop (1, B) again? Actually heap only has one B entry. Need to create a case where same node is pushed twice.
    # Instead, test with a graph where a node is reachable via two paths, second path is longer.
    graph = {"A": [("B", 1), ("C", 3)], "B": [("C", 1)], "C": []}
    # Shortest path A->C is A->B->C cost 2, not A->C cost 3.
    # Heap: (0,A), pop A, push B(1), C(3). Pop B(1), push C(2). Heap: (2,C), (3,C).
    # Pop C(2), C not visited, C==end? Yes, return 2.
    # The (3,C) remains in heap but never popped because end found.
    # To trigger u in visited: True, we need a node to be popped after being visited.
    # Let's use a graph where we force a longer duplicate entry.
    graph = {"A": [("B", 1)], "B": [("C", 1)], "C": [("B", 1)]}
    # Start A, end C.
    # Heap: (0,A). Pop A, push B(1). Heap: (1,B).
    # Pop B, push C(2) and B(2) via C->B edge? Wait, from B we push C(2). Heap: (2,C).
    # Pop C, C==end? Yes, return 2.
    # Not triggering visited skip.
    # Let's explicitly test with a simple case: start == end, but also push the same node again.
    # Actually, the function pushes only unvisited neighbors. So duplicate nodes only appear if there are multiple paths.
    # Use a diamond graph.
    graph = {"A": [("B", 1), ("C", 2)], "B": [("D", 1)], "C": [("D", 1)], "D": []}
    # Start A, end D.
    # Paths: A->B->D cost 2, A->C->D cost 3.
    # Heap: (0,A). Pop A, push B(1), C(2). Heap: (1,B), (2,C).
    # Pop B, push D(2). Heap: (2,C), (2,D).
    # Pop C, push D(3). Heap: (2,D), (3,D).
    # Pop D (cost 2), D not visited, D==end? Yes, return 2.
    # The (3,D) remains in heap, never popped.
    # To trigger u in visited: True, we need to pop D again after it's visited. But end is found, function returns.
    # So we need a graph where the shortest path to end is not the first time we pop end? That's impossible because heap is min-heap.
    # Therefore, u in visited: True can only occur for nodes that are not the end, and we have already visited them via a shorter path.
    # Example: graph with a cycle.
    graph = {"A": [("B", 1)], "B": [("C", 1), ("A", 1)], "C": []}
    # Start A, end C.
    # Heap: (0,A). Pop A, push B(1). Heap: (1,B).
    # Pop B, push C(2) and A(2). Heap: (2,A), (2,C).
    # Pop A (cost 2), A is already visited (u in visited: True), skip.
    # Pop C (cost 2), C not visited, C==end? Yes, return 2.
    # So u in visited: True is triggered for node A.
    assert dijkstra(graph, "A", "C") == 2

# condition: u == end: True (return cost) and False (continue)
def test_start_not_end_found():
    # while heap: True
    # u == end: False for first pop, True for later pop
    graph = {"A": [("B", 1)], "B": []}
    assert dijkstra(graph, "A", "B") == 1

# condition: v in visited: True (skip) and False (push to heap)
def test_neighbor_already_visited():
    # while heap: True
    # v in visited: True for some neighbor, False for others
    graph = {"A": [("B", 1), ("C", 2)], "B": [("C", 1)], "C": []}
    # Start A, end C.
    # Path: A->B->C cost 2, A->C cost 2 (equal).
    # Heap: (0,A). Pop A, visited {A}. Push B(1), C(2). Heap: (1,B), (2,C).
    # Pop B, visited {A,B}. Push C(2) via B->C. But C is not visited yet, so push (2,C). Heap: (2,C), (2,C).
    # Pop C (cost 2), C==end? Yes, return 2.
    # Here, when processing B, neighbor C is not visited yet, so v in visited: False.
    # To get v in visited: True, we need a neighbor that is already in visited set.
    # Example: graph with a cycle back to visited node.
    graph = {"A": [("B", 1)], "B": [("A", 1), ("C", 1)], "C": []}
    # Start A, end C.
    # Heap: (0,A). Pop A, visited {A}. Push B(1). Heap: (1,B).
    # Pop B, visited {A,B}. Push A(2) and C(2). But A is already visited (v in visited: True), so skip A. Push C(2). Heap: (2,C).
    # Pop C, visited {A,B,C}, C==end? Yes, return 2.
    # So v in visited: True for neighbor A when processing B.
    assert dijkstra(graph, "A", "C") == 2

# condition: while heap: False initially (empty heap)
def test_no_path_exists():
    # while heap: False after first pop? Actually heap starts with (0,start).
    # To have while heap: False initially, graph must be empty and start != end.
    # But heap is initialized with (0,start), so heap is non-empty.
    # However, if start not in graph, graph[start] will raise KeyError.
    # The function assumes graph is a dict with all vertices as keys.
    # Let's test with a disconnected graph.
    graph = {"A": [], "B": []}
    # Start A, end B. Heap: (0,A). Pop A, visited {A}. A != end, no neighbors. Heap empty.
    # Loop condition while heap: now False, exit loop, return -1.
    assert dijkstra(graph, "A", "B") == -1

# Additional test to cover all sub-expressions in conditions:
# Conditions and sub-expressions:
# 1. while heap: (no sub-expressions)
# 2. if u in visited: (sub-expression: u in visited)
# 3. if u == end: (sub-expression: u == end)
# 4. for v, c in graph[u]: (loop condition, not boolean)
# 5. if v in visited: (sub-expression: v in visited)
# We need each sub-expression to be True and False at least once.
# We have covered:
# - u in visited: True (test_node_already_visited), False (most tests)
# - u == end: True (test_start_not_end_found when popping end), False (when popping start)
# - v in visited: True (test_neighbor_already_visited), False (most tests)
# - while heap: True (many tests), False (test_no_path_exists after first iteration)
# Let's also test start == end to cover u == end True on first pop.
def test_start_equals_end_non_empty_graph():
    graph = {"A": [("B", 1)], "B": []}
    # Heap: (0,A). Pop A, u == end: True, return 0.
    assert dijkstra(graph, "A", "A") == 0

# Test with a more complex graph to ensure all conditions are exercised.
def test_complex_graph_all_conditions():
    graph = {
        "A": [("B", 1), ("C", 4)],
        "B": [("C", 2), ("D", 5)],
        "C": [("D", 1)],
        "D": [("A", 1)],  # cycle back to A
    }
    # Start A, end D.
    # Shortest path: A->B->C->D cost 4? Let's compute: A->B(1), B->C(2), C->D(1) total 4.
    # Alternative: A->C->D cost 5.
    # Heap: (0,A). Pop A, visited {A}. Push B(1), C(4). Heap: (1,B), (4,C).
    # Pop B, visited {A,B}. Push C(3) via B->C, D(6) via B->D. Heap: (3,C), (4,C), (6,D).
    # Pop C (cost 3), visited {A,B,C}. Push D(4) via C->D. Heap: (4,C), (4,D), (6,D).
    # Pop C (cost 4), C already visited? Yes (u in visited: True), skip.
    # Pop D (cost 4), D not visited, D==end? Yes, return 4.
    # Conditions: u in visited: True for second C pop, v in visited: True when processing D? Not in this run.
    # Let's also ensure v in visited: True when processing D's neighbor A? But D is end, we return.
    # To cover v in visited: True, we need a node that has a neighbor already visited.
    # In this graph, when processing C (first time), neighbor D is not visited.
    # When processing D (if we didn't return), neighbor A is visited.
    # But we return early. So let's test with end not D, say end E not in graph? Then we process all.
    graph = {
        "A": [("B", 1), ("C", 4)],
        "B": [("C", 2), ("D", 5)],
        "C": [("D", 1)],
        "D": [("A", 1)],
        "E": []  # unreachable
    }
    # Start A, end E.
    # Process all nodes until heap empty.
    # When processing D, neighbor A is visited -> v in visited: True.
    assert dijkstra(graph, "A", "E") == -1