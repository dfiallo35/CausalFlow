
import networkx as nx
import matplotlib.pyplot as plt

graph = nx.gnp_random_graph(20,1/5)

graph_K3_3=nx.complete_bipartite_graph(3,3)
# grafo = {'A':['E','I'],   #Grafo dirigido en python
#    'E':['I','A'],
#    'I':['O'],
#    'O':['A']}


# nx.draw_networkx(graph)
# nx.draw_kamada_kawai(graph)

nx.draw_planar(graph_K3_3)
# plt.axis('equal')
plt.show()