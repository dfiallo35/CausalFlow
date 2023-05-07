from plot_methods import *
st.set_page_config(
        page_title="Causal graphs",
        initial_sidebar_state="expanded",
    )


class Visual():
    file=None
    rename_file=None
    pos3d_file=None

    def run(self):
        self.initial_text()
        self.make_sidebar()

        if self.file:
            self.generate_graphs()
            self.make_colorbar_graph()

            if self.graph_type == 'Graph':
                st.markdown('### Entire Graph')
                self.gravis_graph(self.G)

                st.markdown('### Entire Directed Graph')
                self.gravis_graph(self.Gdi, links_force_distance=100, edge_curvature=0.4)

                st.markdown('### Entire Graph Indepedent Nodes')
                self.gravis_independent_nodes(self.G)

                st.markdown('### Entire Directed Graph Indepedent Nodes')
                self.gravis_independent_nodes(self.Gdi, links_force_distance=100, edge_curvature=0.4)

            if self.graph_type == 'Complex Graph':
                st.markdown('### Entire Graph')
                self.gravis_vis(self.G)

                st.markdown('### Entire Directed Graph')
                self.gravis_vis(self.Gdi, edge_curvature=0.4)

                st.markdown('### Entire Graph Indepedent Nodes')
                self.gravis_vis_independent_nodes(self.G)

                st.markdown('### Entire Directed Graph Indepedent Nodes')
                self.gravis_vis_independent_nodes(self.Gdi, edge_curvature=0.4)

            if self.graph_type == '3D Graph':
                if self.pos3d_file:
                    st.markdown('### Brain Graph')
                    self.gravis_three(brain_3d_graph(self.G, self.pos3d_file), layout_algorithm_active=False)

                    # st.markdown('### Brain Directed Graph')
                    # self.gravis_three(brain_3d_graph(self.Gdi, self.pos3d_file), layout_algorithm_active=False)
                else:
                    st.error('Input the 3D Positions File')


    def initial_text(self):
        '''
        Initial text
        '''
        st.title('Construction of causal graphs')

    def generate_graphs(self):
        '''
        Generate the graphs from the file
        '''
        graphs= get_graphs(self.file, 'linkLag', 'vallag', self.rename_file)
        self.G= graphs['Gdict']
        self.Gdi= graphs['Gdidict']
        self.edge_colors= graphs['Edge Colors']

        self.empty_json_graph.download_button(label='Download .json',
                                    data= open(join(data_dir, 'graph.json'), 'rb'),
                                    file_name='graph.json',
                                    mime='application/json'
        )

    def make_sidebar(self):
        '''
        Make the sidebar
        '''
        st.sidebar.title('Graph options')
        self.graph_type= st.sidebar.selectbox('Select a Graph Type', ['Graph', 'Complex Graph', '3D Graph'])

        tab1, tab2, tab3, self.colorbar_tab= st.sidebar.tabs(['Graph', 'Rename', '3D Positions', 'ColorBar'])
        with tab1:
            self.file= st.file_uploader('Select the Graph File', type=['mat', 'json'])
            if self.file:
                self.empty_json_graph= st.empty()
                
        with tab2:
            if self.file:
                a=1
                self.rename_file= st.file_uploader('Select the Rename File', type=['json'])
            else:
                st.error('Input the Graph')
        with tab3:
            if self.file:
                a=1
                self.pos3d_file= st.file_uploader('Select the 3D Positions File', type=['json'])
            else:
                st.error('Input the Graph')
        if not self.file:
            with self.colorbar_tab:
                st.error('Input the Graph')


    def make_colorbar_graph(self):
        '''
        Put the colorbar options in the sidebar
        '''
        if self.file:
            with self.colorbar_tab:
                cb= st.file_uploader('Add ColorBar', type=['png', 'jpg', 'jpeg'])
                if cb:
                    download_sb= st.empty()
                    pic= Image.open(cb)
                    pic.save(join(data_dir, 'graph.png'))
                    add_colorbar(self.edge_colors)

                    st.image(Image.open(join(data_dir, 'graph_colorbar.jpg')), caption='ColorBar Graph', use_column_width=True)
                    with open(join(data_dir, 'graph_colorbar.jpg'), 'rb') as img:
                        download_sb.download_button(label='Download ColorBar Graph',
                                                data= img,
                                                file_name='graph_colorbar.jpg',
                                                mime='image/jpg')


    def gravis_graph(self, G: dict, **args):
        '''
        gravis plot with d3 layout
        '''
        with st.expander('Graphviz Plott(entire graph)'):
            graph=gv.d3(G,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    node_label_size_factor=0.75,
                    node_label_data_source='label',
                    show_edge_label=True,
                    many_body_force_strength=-100,
                    **args)
            components.html(graph.to_html(), height=500)
    
    def gravis_independent_nodes(self, G: dict, **args):
        '''
        gravis plot with independent nodes and d3 layout
        '''
        with st.expander('Graphviz Plott(independent nodes)'):
            nodes= st.multiselect('Select nodes', sorted([node['metadata']['label'] for node in G['graph']['nodes'].values()]))
            graph= get_nodes_graph(G, nodes)
            graph=gv.d3(graph,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    node_label_size_factor=0.75,
                    show_edge_label=True,
                    node_label_data_source='label',
                    many_body_force_strength=-100,
                    **args)
            components.html(graph.to_html(), height=500)


    #check: spring constant
    def gravis_vis(self, G: dict, **args):
        '''
        gravis plot with vis layout
        '''
        with st.expander('Graphviz Vis(entire graph)'):
            graph=gv.vis(G,
                    edge_size_factor=4,
                    edge_label_data_source='label',
                    central_gravity=2,
                    node_label_size_factor=2.5,
                    avoid_overlap=1,
                    layout_algorithm='forceAtlas2Based',
                    spring_constant=0.1,
                    node_size_factor=2.5,
                    edge_label_size_factor=3,
                    show_edge_label_border=True,
                    gravitational_constant=-650,
                    spring_length=100,
                    show_edge_label=True,
                    **args)
            
            components.html(graph.to_html(), height=500)

    def gravis_vis_independent_nodes(self, G: dict, **args):
        '''
        gravis plot with independent nodes and vis layout
        '''
        with st.expander('Graphviz Vis(independent nodes)'):
            nodes= st.multiselect('Select nodes', sorted([node for node in G['graph']['nodes']]))
            graph= get_nodes_graph(G, nodes)

            graph=gv.vis(graph,
                    edge_size_factor=4,
                    edge_label_data_source='label',
                    central_gravity=2,
                    node_label_size_factor=2.5,
                    avoid_overlap=1,
                    layout_algorithm='forceAtlas2Based',
                    spring_constant=0.1,
                    node_size_factor=2.5,
                    edge_label_size_factor=3,
                    show_edge_label_border=True,
                    gravitational_constant=-650,
                    spring_length=100,
                    show_edge_label=True,
                    **args)
            
            components.html(graph.to_html(), height=500)



    def gravis_three(self, G: dict, **args):
        '''
        gravis plot with three layout
        '''
        with st.expander('Graphviz Three(entire graph)'):
            graph=gv.three(G,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    use_z_positioning_force=True,
                    edge_size_factor=2,
                    edge_label_data_source='label',
                    node_label_data_source='label',
                    **args)
            components.html(graph.to_html(), height=500)
    


a= Visual()
a.run()