from leer_mat_files import *

import networkx as nx
from networkx import Graph
from pyvis.network import Network

import streamlit as st
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
from os import getcwd
from os.path import join




def remove_not_linked_nodes(G: Graph):
    to_remove=[]
    for node in G.nodes:
        if len(G.edges(node)) == 0:
            to_remove.append(node)

    G.remove_nodes_from(to_remove)


# st.title('Hello Networkx')
# st.markdown('Graphs are cool')


# G:Graph = nx.from_numpy_matrix(link_matrix[:, :, 0])
# remove_not_linked_nodes(G)


# fig, ax = plt.subplots()
# pos = nx.kamada_kawai_layout(G)
# nx.draw(G,pos, with_labels=True)
# st.pyplot(fig)
# st.balloons()




st.title('Hello Networkx')
st.markdown('Graphs are cool')

st.file_uploader('Select a file')
st.text_area('text', value='text', height=300)




# Define function to create network graph
G:Graph = nx.from_numpy_matrix(link_matrix[:, :, 0])
G= G.to_directed()
remove_not_linked_nodes(G)



# Initiate PyVis network object
net = Network('600px', directed=True)

# # Take Networkx graph and translate it to a PyVis graph format
net.from_nx(G)

# # Generate network with specific layout settings
net.repulsion(node_distance=100, central_gravity=0.10,
                    spring_length=200, spring_strength=0.10,
                    damping=0.55)

# # Save and read graph as HTML file (on Streamlit Sharing)

net.save_graph('pyvis_graph.html')
HtmlFile = open(join(getcwd(), 'pyvis_graph.html'), 'r', encoding='utf-8')
HtmlFiletext = HtmlFile.read()
HtmlFile.close()

# Load HTML file in HTML component for display on Streamlit page
components.html(HtmlFiletext, height=435)

fig, ax = plt.subplots()
pos = nx.kamada_kawai_layout(G)
nx.draw(G,pos, with_labels=True)
st.pyplot(fig)


# nx_graph = nx.cycle_graph(10)
# nx_graph.nodes[1]['title'] = 'Number 1'
# nx_graph.nodes[1]['group'] = 1
# nx_graph.nodes[3]['title'] = 'I belong to a different group!'
# nx_graph.nodes[3]['group'] = 10
# nx_graph.add_node(20, size=20, title='couple', group=2)
# nx_graph.add_node(21, size=15, title='couple', group=2)
# nx_graph.add_edge(20, 21, weight=5)
# nx_graph.add_node(25, size=25, label='lonely', title='lonely node', group=3)
# nt = Network('500px', '500px')
# # populates the nodes and edges data structures
# nt.from_nx(nx_graph)
# nt.show('nx.html')