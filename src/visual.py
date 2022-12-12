from plot_methods import *


class Visual():
    sidebar=None
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

            st.markdown('### Gravis Plott(entire graph)')
            self.gravis_graph(self.G, show_edge_label=True)
            st.markdown('### Gravis Plott(separated graphs)')
            self.gravis_separated_graph(self.Glist)

            st.markdown('### Gravis Directed Plott(entire graph)')
            self.gravis_graph(self.Gdi, show_edge_label=True)

            st.markdown('### Gravis Vis(entire graph)')
            self.gravis_vis(self.G)
            st.markdown('### Gravis Vis(separated graphs)')
            self.gravis_separated_vis(self.Glist)

            st.markdown('### Gravis Vis Directed(entire graph)')
            self.gravis_vis(self.Gdi, show_edge_label=True)

            st.markdown('### Gravis Three(entire graph)')
            self.gravis_three(self.G)
            st.markdown('### Gravis Three(separated graphs)')
            self.gravis_separated_three(self.Glist)


            

    def initial_text(self):
        # Title and description
        st.title('Construction of causal graphs')

    def generate_graphs(self):
        self.G= make_graph_lag0(self.file)
        self.Glist= make_separated_graphs(self.G)
        self.Gdi= make_directed_graph(self.file)
        # self.Gdilist= make_separated_graphs(self.Gdi)


    def make_sidebar(self):
        sidebar= st.sidebar
        sidebar.title('Graph options')
        self.file= sidebar.file_uploader('Select a file')
        self.plott_type= sidebar.selectbox('Select a plott type', ['Plott', 'Complex Plott', '3D Plott', 'Independ'])



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
        
    def gravis_separated_vis(self, Glist: list, **args):
        with st.expander('Graphviz Vis(separated graph)'):
            for G in Glist:
                graph=gv.vis(G,
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

    def gravis_separated_three(self, Glist: list, **args):
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
    


a= Visual()
a.run()