from plot_methods import *


class Visual():
    sidebar=None
    file=None
    matplotlib_option: str
    G: Graph
    Glist: list

    def run(self):
        self.initial_text()
        self.make_sidebar()

        if self.file:
            self.generate_graphs()

            st.markdown('### Gravis Plott(entire graph)')
            self.gravis_graph()
            st.markdown('### Gravis Plott(separated graphs)')
            self.gravis_separated_graph()

            # st.markdown('### Pyvis Plott(entire graph)')
            # self.pyvis_graph()
            # st.markdown('### Pyvis Plott(separated graphs)')
            # self.pyvis_separate_graph()

            # st.markdown('### Matplotlib Plott(entire graph)')
            # self.matplot_graph()
            # st.markdown('### Matplotlib Plott(separated graphs)')
            # self.matplot_separate_graph()

            # st.markdown('### Graphviz Plott')
            # self.graphviz_plott()


    def initial_text(self):
        # Title and description
        st.title('Construction of causal graphs')

    def generate_graphs(self):
        self.G= make_graph_lag0(self.file)
        self.Glist= make_separated_graphs(self.G)


    def make_sidebar(self):
        sidebar= st.sidebar
        sidebar.title('Graph options')
        self.file= sidebar.file_uploader('Select a file')

        # option = sidebar.selectbox('Select the graph type',
        #                         ('Kamada Kawai', 'Shell','Random', 'Spiral', 'Circular', 'Spring'))
        
        # self.matplotlib_option= option



    def gravis_graph(self):
        with st.expander('Graphviz Plott(entire graph)'):
            graph=gv.d3(self.G,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    edge_size_factor=3)
            components.html(graph.to_html(), height=500)

    def gravis_separated_graph(self):
        with st.expander('Graphviz Plott(separated graphs)'):
            for G in self.Glist:
                graph=gv.d3(G,
                        use_y_positioning_force=True,
                        use_x_positioning_force=True,
                        edge_size_factor=3)
                components.html(graph.to_html(), height=500)



    def pyvis_graph(self):
        with st.expander('Pyvis Plott(entire graph)'):
            # Initiate PyVis network object
            net = Network('600px')
            net.from_nx(self.G)

            # Set the physics layout of the network
            net.repulsion(node_distance=50,
                        central_gravity=0.70,
                        spring_length=50,
                        spring_strength=0.20,
                        damping=0.2)

            # Load HTML file in HTML component for display on Streamlit page
            components.html(net.generate_html(), height=610)

    def pyvis_separate_graph(self):
        with st.expander('Pyvis Plott(separated graphs)'):
            for G in self.Glist:
                net = Network('600px')
                net.from_nx(G)

                # Set the physics layout of the network
                net.repulsion(node_distance=100,
                            central_gravity=0.70,
                            spring_length=50,
                            spring_strength=0.20,
                            damping=0.2)

                # Load HTML file in HTML component for display on Streamlit page
                components.html(net.generate_html(), height=610)
    



    #TODO: fix plots
    def matplot_graph(self):
        with st.expander('Matplotlib Plott(entire graph)'):
            fig, _= plt.subplots()
            pltdict = {
                'Kamada Kawai': nx.kamada_kawai_layout,
                'Shell': nx.shell_layout,
                'Random': nx.random_layout,
                'Spiral': nx.spiral_layout,
                'Circular': nx.circular_layout,
                'Spring': nx.spring_layout
            }
            
            nx.draw(self.G, pltdict[self.matplotlib_option](self.G), with_labels=True, )
            st.pyplot(fig)

    def matplot_separate_graph(self):
        with st.expander('Matplotlib Plott(separated graphs'):
            pltdict = {
                'Kamada Kawai': nx.kamada_kawai_layout,
                'Shell': nx.shell_layout,
                'Random': nx.random_layout,
                'Spiral': nx.spiral_layout,
                'Circular': nx.circular_layout,
                'Spring': nx.spring_layout
            }

            for G in self.Glist:
                fig, _= plt.subplots()
                nx.draw(G, pltdict[self.matplotlib_option](G), with_labels=True, )
                st.pyplot(fig)

    def graphviz_plott(self):
        with st.expander("See explanation"):
            #plot with graphviz
            # Create a graphlib graph object
            graph = graphviz.Graph()
            graph.attr('node', shape='circle')
            graph.attr('node', style='filled')
            graph.attr('node', fillcolor='lightblue2')
            graph.attr('node', color='blue')
            graph.attr('node', fontcolor='black')
            graph.attr('node', fontsize='20')
            graph.attr('node', width='0.5')
            graph.attr('node', height='0.5')
            graph.attr('node', fixedsize='true')

            graph.attr('edge', color='blue')
            graph.attr('edge', arrowsize='1')
            graph.attr('edge', penwidth='3')

            for a in self.G.edges:
                graph.edge(str(a[0]), str(a[1]))

            st.graphviz_chart(graph)


a= Visual()
a.run()