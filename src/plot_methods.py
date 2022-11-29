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
    




def load_matrix(file):
    data = loadmat(file)
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

    return link_matrix, val_matrix



def make_graph_matrix(file: str):
    lm, _= load_matrix(file)
    G:Graph = nx.from_numpy_matrix(lm[:, :, 0])
    remove_not_linked_nodes(G)
    return G





def get_data_dict(data):
    rowcount=0
    newdata= dict()
    for row in data:
        rowcount+=1
        columncount=0
        for column in row:
            columncount+=1
            if column != 0:
                if newdata.get(rowcount):
                    newdata[rowcount].append(columncount)
                else:
                    newdata[rowcount] = [columncount]
    return newdata

def load_dict(file: str):
    data = loadmat(file)
    linklag0 = get_data_dict(data['linkLag0'])

    return linklag0

def make_graph(file: str):
    G:Graph= Graph()
    linkl= load_dict(file)

    for node in linkl:
        G.add_node(node, label= str(node), title= str(node),
                    scaling= {'min': 10, 'max': 30, 'label': {'enabled': True, 'min': 14, 'max': 30, 'maxVisible': 30, 'drawThreshold': 5}},
                    shadow= {'enabled': True, 'color': 'rgba(0,0,0,0.5)', 'size': 10, 'x': 5, 'y': 5},
                    shapeProperties= {'borderDashes': False, 'borderRadius': 6, 'interpolation': False, 'useImageSize': False, 'useBorderWithImage': False})
        for xnode in linkl[node]:
            G.add_edge(node, xnode, color= 'black')
            
    return G



