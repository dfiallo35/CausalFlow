from plot_methods import *


class Visual():
    sidebar=None
    file=None
    matplotlib_option: str
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
            self.gravis_graph(self.G)
            st.markdown('### Gravis Plott(separated graphs)')
            self.gravis_separated_graph(self.Glist)

            st.markdown('### Gravis Directed Plott(entire graph)')
            self.gravis_graph(self.Gdi)
            # st.markdown('### Gravis Directed Plott(separated graphs)')
            # self.gravis_separated_graph(self.Gdilist)


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



    def gravis_graph(self, G: Graph):
        with st.expander('Graphviz Plott(entire graph)'):
            graph=gv.d3(G,
                    use_y_positioning_force=True,
                    use_x_positioning_force=True,
                    edge_size_factor=2)
            components.html(graph.to_html(), height=500)

    def gravis_separated_graph(self, Glist: list):
        with st.expander('Graphviz Plott(separated graphs)'):
            for G in Glist:
                graph=gv.d3(G,
                        use_y_positioning_force=True,
                        use_x_positioning_force=True,
                        edge_size_factor=2)
                components.html(graph.to_html(), height=500)



a= Visual()
a.run()