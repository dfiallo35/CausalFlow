from scipy.io import loadmat
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

data = loadmat("./src/graph 360v 70t a0.001 estimulo2 prom_weight links 180.mat")
sorted(data.keys())
n = 360
val_matrix = np.zeros((n, n, 3))
link_matrix = np.zeros((n, n, 3))


val_matrix[:, :, 0] = data['vallag0']
val_matrix[:, :, 1] = data['vallag1']
val_matrix[:, :, 2] = data['vallag2']


link_matrix[:, :, 0] = data['linkLag0']
link_matrix[:, :, 1] = data['linkLag1']
link_matrix[:, :, 2] = data['linkLag2']


def links(matrix):
    for a in range(0, 3):
        for i in range(0, n):
            for j in range(0, n):
                if matrix[i, j, a] == 1:
                    print(i, j, a)

# links(link_matrix)


def make_list(input_matrix):
    matrix=[]
    for a in input_matrix:
        temp=[]
        for b in a:
            temp.append(list(b))
        matrix.append(temp)
    return matrix


def save_matrix(output_file, matrix):
    file = open(output_file, 'w')
    file.write(str(matrix))

val_m= make_list(val_matrix)
link_m= make_list(link_matrix)





def create_graph(val_matrix,link_matrix,n):
    G = nx.Graph() #make a digraph for general case
    G.add_nodes_from([i for i in range(n)])
    for i in G.nodes:
        for j in G.nodes:                    
            if link_matrix[i,j,0]==1:
                G.add_edge(i,j)   
    empty_nodes=[]
    for node in G.nodes:
        if(len(G.edges(node))==0):
            empty_nodes.append(node)
            # G.remove_node(node)
    G.remove_nodes_from(empty_nodes)
    #Good for this case
    # nx.draw_kamada_kawai(G,with_labels=True)
    nx.draw_circular(G,with_labels=True)
    # nx.draw_random(G,with_labels=True)
    # nx.draw_shell(G,with_labels=True)

    #Bad for this case
    # nx.draw_networkx(G)  
    # nx.draw(G,with_labels=True)
    # # nx.draw_planar(G,with_labels=True)
    # nx.draw_spectral(G,with_labels=True)
    # nx.draw_spring(G,with_labels=True)



# print(link_matrix)


create_graph(val_matrix,link_matrix,n)
plt.show()



save_matrix( './matrix/val_m.txt', val_m)
save_matrix( './matrix/link_m.txt', link_m)