import networkx as nx

G = nx.DiGraph()
G.add_edge("Push y Pop", "DFS pila LIFO")
G.add_edge("DFS pila LIFO", "complejidad O(D)")
G.add_edge("BFS cola FIFO", "DFS pila LIFO")
# ... resto de conexiones

pr = nx.pagerank(G, alpha=0.85)
print(pr)