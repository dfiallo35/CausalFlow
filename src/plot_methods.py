# networkx
import networkx as nx
from networkx import Graph

# pyvis
from pyvis.network import Network

# graphviz
import graphviz

# streamlit
import streamlit as st
import streamlit.components.v1 as components

# matplotlib
import matplotlib.pyplot as plt

# os
from os import getcwd
from os.path import join

# scipy and numpy
from scipy.io import loadmat
import numpy as np



def remove_not_linked_nodes(G: Graph):
    '''
    Remove nodes that are not linked to any other node 
    in the graph G created with networkx
    :param G: Graph created with networkx
    :type G: Graph
    '''
    to_remove=[]
    for node in G.nodes:
        if len(G.edges(node)) == 0:
            to_remove.append(node)
    G.remove_nodes_from(to_remove)


def generate_graph(matrix: np.ndarray, n: int, directed: bool):
    '''
    Generate a graph with networkx from a matrix of links
    '''
    ...

def generate_graph_directed(): ...
    








    link_matrix[:, :, 0] = data['linkLag0']
    link_matrix[:, :, 1] = data['linkLag1']
    link_matrix[:, :, 2] = data['linkLag2']

    return link_matrix, val_matrix



    return G







    return linklag0





