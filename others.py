import networkx as nx
from networkx import Graph

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


def make_separated_graphs(G: Graph):
    '''
    Separate the graph G in subgraphs and return a list of graphs
    :param G: Graph created with networkx
    :type G: Graph
    :return: List of subgraphs
    :rtype: list
    '''
    Glist = separate_graphs(G)
    Glist.sort(key=lambda x: len(x.nodes), reverse=True)
    biggest_graph: Graph = Glist[0]
    if biggest_graph.number_of_nodes() > G.number_of_nodes() / 2:
        for graph in Glist:
            if graph == biggest_graph:
                Glist.remove(graph)
        Gnew= merge_graphs(Glist)
        return [biggest_graph, Gnew]
    
    return G

separated_graphs= make_separated_graphs(to_networkx_graph(Gdict))












#visual
def gravis_separated_graph(self, Glist: list, **args):
    with st.expander('Graphviz Plott(separated graphs)'):
        for G in Glist:
            graph=gv.d3(G,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    **args)
            components.html(graph.to_html(), height=500)




    def gravis_vis_separated(self, Glist: list, **args):
        with st.expander('Graphviz Vis(separated graph)'):
            for G in Glist:
                graph=gv.vis(G,
                        edge_size_factor=2,
                        edge_label_data_source='label',
                        central_gravity=1.5,
                        node_label_size_factor=2.5,
                        avoid_overlap=1,
                        layout_algorithm='hierarchicalRepulsion',
                        spring_constant=0,
                        node_size_factor=2.5,
                        **args)
                
                components.html(graph.to_html(), height=500)



    def gravis_three_separated(self, Glist: list, **args):
        with st.expander('Graphviz Three(separated graphs)'):
            for G in Glist:
                graph=gv.three(G,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    use_z_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    **args)
                components.html(graph.to_html(), height=500)


    def gravis_three_independent_nodes(self, G: dict, **args):
        with st.expander('Graphviz Three(independent nodes)'):
            nodes= st.multiselect('Select nodes', sorted([node for node in G['graph']['nodes']]))
            graph= get_nodes_graph(G, nodes)

            graph=gv.three(graph,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    use_z_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    **args)
            components.html(graph.to_html(), height=500)