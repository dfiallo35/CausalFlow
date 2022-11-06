from leer_mat_files import *



import networkx as nx
import matplotlib.pyplot as pl


G = nx.from_numpy_matrix(link_matrix[:, :, 0])
nx.draw_kamada_kawai(G, with_labels=True)
pl.axis('equal')
pl.show()
