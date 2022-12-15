from plot_methods import *


class Visual():
    file=None

    G: Graph
    Glist: list

    Gdi: Graph
    Gdilist: list

    def run(self):
        self.initial_text()
        self.make_sidebar()

        if self.file:
            self.generate_graphs()
            cb= self.empty_uploader.file_uploader('Add ColorBar', type=['png', 'jpg', 'jpeg'])
            if cb:
                pic= Image.open(cb)
                pic.save(join(data_dir, 'graph.png'))
                add_colorbar(self.edge_colors)
            
            if self.graph_type == 'Graph':
                st.markdown('### Entire Graph')
                self.gravis_graph(self.G, show_edge_label=True)
                st.markdown('### Separated Graphs')
                self.gravis_separated_graph(self.Glist)

                st.markdown('### Entire Directed Graph')
                self.gravis_graph(self.Gdi, show_edge_label=True)

                st.markdown('### Entire Graph Indepedent Nodes')
                self.gravis_independent_nodes(self.G)
                st.markdown('### Entire Directed Graph Indepedent Nodes')
                self.gravis_independent_nodes(self.Gdi, show_edge_label=True)

            if self.graph_type == 'Complex Graph':
                st.markdown('### Entire Graph')
                self.gravis_vis(self.G)
                st.markdown('### Separated Graphs')
                self.gravis_vis_separated(self.Glist)

                st.markdown('### Entire Directed Graph')
                self.gravis_vis(self.Gdi, show_edge_label=True)

                st.markdown('### Entire Graph Indepedent Nodes')
                self.gravis_vis_independent_nodes(self.G)
                st.markdown('### Entire Directed Graph Indepedent Nodes')
                self.gravis_vis_independent_nodes(self.Gdi)

            if self.graph_type == '3D Graph':
                st.markdown('### Entire Graph')
                self.gravis_three(self.G)
                st.markdown('### Separated Graphs')
                self.gravis_three_separated(self.Glist)

                st.markdown('### Entire Graph Indepedent Nodes')
                self.gravis_three_independent_nodes(self.G)
                st.markdown('### Entire Directed Graph Indepedent Nodes')
                self.gravis_vis_independent_nodes(self.Gdi)

                st.markdown('### Brain Graph')
                self.gravis_three(brain_3d_graph(self.G), layout_algorithm_active=False,)
                st.markdown('### Brain Directed Graph')
                self.gravis_three(brain_3d_graph(self.Gdi), layout_algorithm_active=False,)


            

    def initial_text(self):
        # Title and description
        st.title('Construction of causal graphs')

    def generate_graphs(self):
        graphs= get_graphs(self.file, 'linkLag', 'vallag')
        self.G= graphs['Gdict']
        self.Glist= graphs['Separated Graphs']
        self.Gdi= graphs['Gdidict']
        self.edge_colors= graphs['Edge Colors']

    def make_sidebar(self):
        st.sidebar
        st.sidebar.title('Graph options')
        self.file= st.sidebar.file_uploader('Select a file', type=['mat', 'json'])
        self.graph_type= st.sidebar.selectbox('Select a Graph Type', ['Graph', 'Complex Graph', '3D Graph'])
        self.empty_uploader= st.sidebar.empty()

    def gravis_graph(self, G: Graph, **args):
        with st.expander('Graphviz Plott(entire graph)'):
            graph=gv.d3(G,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    **args)
            components.html(graph.to_html(), height=500)

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
    
    def gravis_independent_nodes(self, G: Graph, **args):
        with st.expander('Graphviz Plott(independent nodes)'):
            nodes= st.multiselect('Select nodes', sorted(to_networkx_graph(G).nodes))
            graph= get_nodes_graph(G, nodes)
            graph=gv.d3(graph,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    **args)
            components.html(graph.to_html(), height=500)



    def gravis_vis(self, G: Graph, **args):
        with st.expander('Graphviz Vis(entire graph)'):
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

    def gravis_vis_separated(self, Glist: list, **args):
        with st.expander('Graphviz Vis(separated graph)'):
            for G in Glist:
                graph=gv.vis(G,
                        edge_size_factor=2,
                        edge_label_data_source='label',
                        **args)
                
                components.html(graph.to_html(), height=500)

    def gravis_vis_independent_nodes(self, G: Graph, **args):
        with st.expander('Graphviz Vis(independent nodes)'):
            nodes= st.multiselect('Select nodes', sorted(to_networkx_graph(G).nodes))
            graph= get_nodes_graph(G, nodes)

            graph=gv.vis(graph,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    **args)
            
            components.html(graph.to_html(), height=500)



    def gravis_three(self, G: Graph, **args):
        with st.expander('Graphviz Three(entire graph)'):
            graph=gv.three(G,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    use_z_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    
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
    
    def gravis_three_independent_nodes(self, G: Graph, **args):
        with st.expander('Graphviz Three(independent nodes)'):
            nodes= st.multiselect('Select nodes', sorted(to_networkx_graph(G).nodes))
            graph= get_nodes_graph(G, nodes)

            graph=gv.three(graph,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    use_z_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    **args)
            components.html(graph.to_html(), height=500)

a= Visual()
a.run()