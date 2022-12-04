import networkx as nx
from networkx import Graph

from scipy.io import loadmat

import gravis as gv

import streamlit as st
import streamlit.components.v1 as components



#TODO: ajustar el colormap a los minimos y maximos de los lags
#TODO: arreglar la escala de colores de to_hexa_rgb
#TODO: agregar colormap(se puede tomar la foto guardada y agregarselo despues en una opcion extra)
#TODO: agregarle nombre a los nodos
#TODO: separar el grafo dirigido en subgrafos(el no dirigido ya está separado, pero esa funcion no es valida para los dirigidos)
#TODO: compactar el grafo para que sea mas legible
#TODO: ajustar el gravis_vis para que se vea bien en streamlit
#TODO: ajustar gravis three para que se vea bien en streamlit
#TODO: tomar diferentes tipos de archivos de entrada
#TODO: agregar about en sidebar


def get_data_linkLag(datalink, dataval):
    '''
    Create a dictionary from two lists
    :param datalink: List of links
    :type datalink: list
    :param dataval: List of values
    :type dataval: list
    :return: Dictionary
    :rtype: dict
    '''
    rowcount=0
    newdata= dict()

    for row in datalink:
        rowcount+=1
        columncount=0

        for column in row:
            columncount+=1

            if column != 0:
                if newdata.get(rowcount):
                    newdata[rowcount][columncount]= dataval[rowcount-1][columncount-1]
                else:
                    newdata[rowcount] = {columncount: dataval[rowcount-1][columncount-1]}

    return newdata


def load_dict(file: str, linkLag: str, valLag: str):
    """
    Load a dictionary from a .mat file
    :param file: Path to the .mat file
    :type file: str
    :param linkLag: Name of the dictionary in the .mat file
    :type linkLag: str
    :param valLag: Name of the dictionary in the .mat file
    :type valLag: str
    :return: Dictionary
    :rtype: dict
    """
    data = loadmat(file)
    datalink = []

    for i in data[linkLag]:
        temp=[]
        for j in i:
            temp.append(j)
        datalink.append(temp)
    
    dataval = []
    for i in data[valLag]:
        temp=[]
        for j in i:
            temp.append(round(j, 4))
        dataval.append(temp)

    return get_data_linkLag(datalink, dataval)


def merge_lags(lags: list, n: int):
    newlag= dict()
    for i in range(n):
        for j in range(n):
            count= 1
            edge= []
            avg= 0
            for lag in lags:
                if lag.get(i) and lag[i].get(j) and i != j:
                    avg+= lag[i][j]
                    edge.append(str(count))
                count+=1
            if edge != []:
                if newlag.get(i) == None:
                    newlag[i]= {j: {'text': ','.join(edge), 'avg': avg/len(edge)}}
                else:
                    newlag[i][j]= {'text': ','.join(edge), 'avg': avg/len(edge)}
    return newlag


def make_directed_graph(file):
    G= nx.DiGraph()
    vallag_list= []
    elements= list(loadmat(file).keys())

    n=1
    while 'vallag'+str(n) in elements and 'linkLag'+str(n) in elements:
        vallag_list.append(('linkLag'+str(n), 'vallag'+str(n)))
        n+=1
    
    lag_dicts= []
    for lag in vallag_list:
        lag_dicts.append(load_dict(file, lag[0], lag[1]))

    lags_merged= merge_lags(lag_dicts, len(loadmat(file)[vallag_list[0][0]]))

    for node in lags_merged:
        G.add_node(node,
                label= str(node),
                title= str(node),
                opacity=0.7,
                border_color='black',
                border_size=2,
                color= 'gray')
        for xnode in lags_merged[node]:
            G.add_node(xnode,
                label= str(node),
                title= str(node),
                opacity=0.7,
                border_color='black',
                border_size=2,
                color= 'gray')
            
            G.add_edge(node, xnode,
                    color= to_hexa_rgb(lags_merged[node][xnode]['avg']),
                    label= lags_merged[node][xnode]['text'])
    return G


def make_graph_lag0(file: str):
    '''
    Create a graph from a .mat file
    :param file: Path to the .mat file
    :type file: str
    :return: Graph
    :rtype: Graph
    '''
    G:Graph= Graph()
    linkl= load_dict(file, 'linkLag0', 'vallag0')

    for node in linkl:
        G.add_node(node,
                label= str(node),
                title= str(node),
                opacity=0.7,
                border_color='black',
                border_size=2,
                color= 'gray')
        for xnode in linkl[node]:
            G.add_edge(node, xnode, color= to_hexa_rgb(linkl[node][xnode]))
    return G


def make_separated_graphs(G: Graph):
    '''
    Separate the graph G in subgraphs and return a list of graphs
    :param G: Graph created with networkx
    :type G: Graph
    :return: List of subgraphs
    :rtype: list
    '''
    Glist = separate_graphs(G)
    biggest_graph: Graph = find_biggest_graph(Glist)
    if biggest_graph.number_of_nodes() > G.number_of_nodes() / 2:
        for graph in Glist:
            if graph == biggest_graph:
                Glist.remove(graph)
        Gnew= merge_graphs(Glist)
        return [biggest_graph, Gnew]
    
    return G


def separate_graphs(G: Graph):
    '''
    Separate the graph G in subgraphs
    :param G: Graph created with networkx
    :type G: Graph
    :return: List of subgraphs
    :rtype: list
    '''
    return [G.subgraph(c).copy() for c in nx.connected_components(G)]


def merge_graphs(Glist: list):
    '''
    Merge a list of graphs into one graph
    :param Gs: List of graphs
    :type Gs: list
    :return: Graph
    :rtype: Graph
    '''
    G = nx.Graph()
    for g in Glist:
        G = nx.compose(G, g)
    return G


def find_biggest_graph(Glist: list):
    '''
    Find the biggest graph in a list of graphs
    :param Gs: List of graphs
    :type Gs: list
    :return: Graph
    :rtype: Graph
    '''
    Glist.sort(key=lambda x: len(x.nodes), reverse=True)
    return Glist[0]


def to_hexa_rgb(number: int):
    '''
    Convert a number to a hexa color
    :param number: Number to convert
    :type number: int
    :return: Hexa color
    :rtype: str
    '''
    n= str(hex(int((abs(number) * 230) + 25)))[2:]
    if number >= 0:
        return '#' + n + '0000'
    else:
        return '#' + '00' + n + '00'

