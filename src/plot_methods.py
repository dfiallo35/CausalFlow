import networkx as nx
from networkx import Graph

from scipy.io import loadmat

import gravis as gv

import streamlit as st
import streamlit.components.v1 as components

import json
from os import path


#fix: escala de colores de to_hexa_rgb
#todo: agregar colormap(se puede tomar la foto guardada y agregarselo despues en una opcion extra)

#todo: agregarle nombre a los nodos
#todo: compactar el grafo para que sea mas legible
#todo: agregar metodos para separar los grafos en subgrafos

#fix: ajustar el gravis_vis para que se vea bien en streamlit
#fix: ajustar gravis three para que se vea bien en streamlit
#todo: tomar diferentes tipos de archivos de entrada

#todo: agregar about en sidebar

#todo: agregarle un boton para que se pueda descargar el grafo como json
#todo: tomar json como entrada

#todo: investigar sobre la representacion con forma de cerebro

def to_networkx_graph(data:dict):
    if data['graph']['directed']:
        G = nx.DiGraph()
        for node in data['graph']['nodes']:
            G.add_node(node,
                    **data['graph']['nodes'][node]['metadata']
            )
        for edge in data['graph']['edges']:
            G.add_edge(edge['source'], edge['target'],
                    **edge['metadata']
            )
    
    else:
        G = nx.Graph()
        for node in data['graph']['nodes']:
            G.add_node(node,
                    **data['graph']['nodes'][node]['metadata']
            )
        for edge in data['graph']['edges']:
            G.add_edge(edge['source'], edge['target'],
                    **edge['metadata']
            )

    return G

def to_dict(G:Graph):
    data = {
        'graph': {
            'directed': False,
            'nodes': dict(G.nodes(data=True)),
            'edges': list(G.edges(data=True)),
        }
    }
    return data



def load_json(file:str):
    data = json.load(open(file))
    return data

def load_mat(file:str):
    return loadmat(file)



def save_json(file:str, data:dict):
    with open(file, 'w') as outfile:
        json.dump(data, outfile)


def get_math_data(data:dict, linkLag:str, valLag:str):
    newdata= dict()
    
    count=0
    linkl= linkLag + str(count)
    vall= valLag + str(count)
    linkval= []
    while linkl in data and vall in data:
        linkval.append((linkl, vall))
        newdata[linkl]= {}
        newdata[vall]= []

        for row, data_row in enumerate(data[linkl]):
            for column, data_column in enumerate(data_row):
                if data_column != 0:
                    newdata[linkl][row + 1]= {}
                    newdata[vall].append({'source': row + 1, 'target': column + 1, 'weight': data[vall][row][column]})
        count+=1
        linkl= linkLag + str(count)
        vall= valLag + str(count)
    
    graphdict= {
        'graph': {
            'directed': False,
            'metadata': {},

            'nodes': {},
            'edges': [],
        }
    }
    link, val= linkval[0]
    for node in newdata[link]:
        graphdict['graph']['nodes'][node]= {'metadata': {'label': str(node), 'title': str(node), 'opacity': 0.7, 'border_color': 'black', 'border_size': 2, 'color': 'gray'}}
    
    edge_colors= colors([c['weight'] for c in newdata[val]])
    for edge in newdata[val]:
        graphdict['graph']['edges'].append({'source': edge['source'], 'target': edge['target'], 'metadata': {'color': edge_colors[edge['weight']]}})


    digraphdict= {
        'graph': {
            'directed': True,
            'metadata': {},

            'nodes': {},
            'edges': [],
        }
    }
    edges= dict()
    for link, val in linkval[1:]:
        for node in newdata[link]:
            digraphdict['graph']['nodes'][node]= {'metadata': {'label': str(node), 'title': str(node), 'opacity': 0.7, 'border_color': 'black', 'border_size': 2, 'color': 'gray'}}
    
        for edge in newdata[val]:
            if edges.get((edge['source'], edge['target'])):
                edges[(edge['source'], edge['target'])].append({'weight':edge['weight'], 'lags':val[len(valLag):]})
            else:
                edges[(edge['source'], edge['target'])]= [{'weight':edge['weight'], 'lags':val[len(valLag):]}]

    
    for edge in edges:

        if edge[0] != edge[1]:
            #todo: add color
            lags= ','.join([e['lags'] for e in edges[edge]])
            w= sum([e['weight'] for e in edges[edge]])/len(edges[edge])
            digraphdict['graph']['edges'].append({'source': edge[0], 'target': edge[1], 'metadata': {'color': w, 'label':lags}})
            node = edge[1]
            digraphdict['graph']['nodes'][node]= {'metadata': {'label': str(node), 'title': str(node), 'opacity': 0.7, 'border_color': 'black', 'border_size': 2, 'color': 'gray'}}

    edge_colors= colors([c['metadata']['color'] for c in digraphdict['graph']['edges']])
    for edge in digraphdict['graph']['edges']:
        edge['metadata']['color']= edge_colors[edge['metadata']['color']]


    return graphdict, digraphdict



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



def get_nodes_graph(G: dict, nodes: list):
    '''
    Get a subgraph of G containing only the nodes in nodes
    :param G: Graph
    :type G: Graph
    :param nodes: List of nodes
    :type nodes: list
    :return: Subgraph
    :rtype: Graph
    '''
    if G['graph']['directed']:
        newG = {
            'graph': {
                'metadata': {},
                'directed': True,
                'nodes': {},
                'edges': [],
            }
        }
        for node in G['graph']['nodes']:
            if node in nodes:
                newG['graph']['nodes'][node]= G['graph']['nodes'][node]

        for edge in G['graph']['edges']:
            if newG['graph']['nodes'].get(edge['source']):
                newG['graph']['edges'].append(edge)
                newG['graph']['nodes'][node]= G['graph']['nodes'][edge['target']]
    
    else:
        newG = {
            'graph': {
                'metadata': {},
                'directed': False,
                'nodes': {},
                'edges': [],
            }
        }
        for node in G['graph']['nodes']:
            if node in nodes:
                newG['graph']['nodes'][node]= G['graph']['nodes'][node]

        for edge in G['graph']['edges']:
            if edge['source'] in nodes:
                newG['graph']['edges'].append(edge)
                newG['graph']['nodes'][edge['source']]= G['graph']['nodes'][edge['target']]
                newG['graph']['nodes'][edge['target']]= G['graph']['nodes'][edge['target']]

    return newG



def get_graphs(file:str, linkLag:str, valLag:str, rename_file:str=None):
    _, extension= path.splitext(file.name)

    if extension == '.mat':
        Gdict, Gdidict = get_math_data(load_mat(file), linkLag, valLag)
        separated_graphs= make_separated_graphs(to_networkx_graph(Gdict))

    if extension == '.json':
        data= load_json(file)
        Gdict, Gdidict = None
    
    return {'Gdict': Gdict, 'Gdidict': Gdidict, 'Separated Graphs': separated_graphs}



def find_max_min_w(wlist: list):
    max= 0
    min= 0
    for w in wlist:
        if w >= max:
            max= w
        if w <= min:
            min=w
    return max, min

def _to_hexa_rgb(n: int):    
    n= str(hex(n))[2:]
    return '#' + 'ff' + n + n


def to_hexa_rgb(n: int, max, min):
    '''
    Convert a number to a hexa color
    :param number: Number to convert
    :type number: int
    :return: Hexa color
    :rtype: str
    '''
    if(min < 0):
        max=max-min
        n=n-min
        min=0        
    range=max-min 
    colors = []
    color=int(abs(n-min)/range *200)+25
    colors.append(_to_hexa_rgb(color))
    return colors


def colors(wlist: list):
    d= dict()
    for w in wlist:
        d[w]= '#ff0000'
    return d

# def to_hexa_rgb(number: int, max: int, min: int):
#     '''
#     Convert a number to a hexa color
#     :param number: Number to convert
#     :type number: int
#     :return: Hexa color
#     :rtype: str
#     '''
#     if number >= 0:
#         color= 255/max
#         n= int(abs(255 - color * number))
#         n= str(hex(n))[2:]
#         return '#' + 'ff' + n + n
#     else:
#         color= 255/min
#         n= int(abs(255 - color * number))
#         n= str(hex(n))[2:]
#         return '#' + n + 'ff' + n