from plot_methods import *
st.set_page_config(
        page_title="Causal graphs",
        initial_sidebar_state="expanded",
    )


class Visual():
    file=None

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

                st.markdown('### Entire Directed Graph')
                self.gravis_graph(self.Gdi, show_edge_label=True, links_force_distance=100, edge_curvature=0.4)

                st.markdown('### Entire Graph Indepedent Nodes')
                self.gravis_independent_nodes(self.G)

                st.markdown('### Entire Directed Graph Indepedent Nodes')
                self.gravis_independent_nodes(self.Gdi, show_edge_label=True)

            if self.graph_type == 'Complex Graph':
                st.markdown('### Entire Graph')
                self.gravis_vis(self.G)

                st.markdown('### Entire Directed Graph')
                self.gravis_vis(self.Gdi, show_edge_label=True, edge_curvature=0.4)

                st.markdown('### Entire Graph Indepedent Nodes')
                self.gravis_vis_independent_nodes(self.G)

                st.markdown('### Entire Directed Graph Indepedent Nodes')
                self.gravis_vis_independent_nodes(self.Gdi)

            if self.graph_type == '3D Graph':
                st.markdown('### Brain Graph')
                self.gravis_three(brain_3d_graph(self.G), layout_algorithm_active=False,)

                st.markdown('### Brain Directed Graph')
                self.gravis_three(brain_3d_graph(self.Gdi), layout_algorithm_active=False)



    def initial_text(self):
        # Title and description
        st.title('Construction of causal graphs')

    def generate_graphs(self):
        graphs= get_graphs(self.file, 'linkLag', 'vallag')
        self.G= graphs['Gdict']
        self.Gdi= graphs['Gdidict']
        self.edge_colors= graphs['Edge Colors']

    def make_sidebar(self):
        st.sidebar
        st.sidebar.title('Graph options')
        self.file= st.sidebar.file_uploader('Select a file', type=['mat', 'json'])
        self.graph_type= st.sidebar.selectbox('Select a Graph Type', ['Graph', 'Complex Graph', '3D Graph'])
        self.empty_uploader= st.sidebar.empty()

    def gravis_graph(self, G: dict, **args):
        with st.expander('Graphviz Plott(entire graph)'):
            graph=gv.d3(G,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    **args)
            components.html(graph.to_html(), height=500)
    
    def gravis_independent_nodes(self, G: dict, **args):
        with st.expander('Graphviz Plott(independent nodes)'):
            nodes= st.multiselect('Select nodes', sorted([node for node in G['graph']['nodes']]))
            graph= get_nodes_graph(G, nodes)
            graph=gv.d3(graph,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    **args)
            components.html(graph.to_html(), height=500)


    #check: spring constant
    def gravis_vis(self, G: dict, **args):
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

    def gravis_vis_independent_nodes(self, G: dict, **args):
        with st.expander('Graphviz Vis(independent nodes)'):
            nodes= st.multiselect('Select nodes', sorted([node for node in G['graph']['nodes']]))
            graph= get_nodes_graph(G, nodes)

            graph=gv.vis(graph,
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



    def gravis_three(self, G: dict, **args):
        with st.expander('Graphviz Three(entire graph)'):
            graph=gv.three(G,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    use_z_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    
                    **args)
            components.html(graph.to_html(), height=500)
    


a= Visual()
a.run()