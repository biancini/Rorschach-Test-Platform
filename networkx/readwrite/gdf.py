"""
*******
GDF
*******
Read and write graphs in GDF format.

Notes
-----
This implementation does not support mixed graphs (directed and unidirected 
edges together) hyperedges, nested graphs, or ports. 

Format
------
GraphML is an CSV format.  See 
https://gephi.org/users/supported-graph-formats/gdf-format/ for the specification.
"""
from networkx.utils import open_file

@open_file(1,mode='wb')
def write_gdf(G, path, encoding='utf-8'):
    """Write G in GDF CVS format to path

    Parameters
    ----------
    G : graph
       A networkx graph
    path : file or string
       File or filename to write.  
       Filenames ending in .gz or .bz2 will be compressed.
    encoding : string (optional)
       Encoding for text data.

    Examples
    --------
    >>> G=nx.path_graph(4)
    >>> nx.write_gdf(G, "test.gdf")

    Notes
    -----
    This implementation does not support mixed graphs (directed and unidirected 
    edges together) hyperedges, nested graphs, or ports. 
    """
    writer = GDFWriter(encoding=encoding)
    writer.add_graph_element(G)
    writer.dump(path)

def generate_gdf(G, encoding='utf-8'):
    """Generate GDF lines for G

    Parameters
    ----------
    G : graph
       A networkx graph
    encoding : string (optional)
       Encoding for text data.

    Examples
    --------
    >>> G=nx.path_graph(4)
    >>> linefeed=chr(10) # linefeed=\n
    >>> s=linefeed.join(nx.generate_gdf(G))  # doctest: +SKIP
    >>> for line in nx.generate_gdf(G):  # doctest: +SKIP
    ...    print(line)

    Notes
    -----
    This implementation does not support mixed graphs (directed and unidirected 
    edges together) hyperedges, nested graphs, or ports. 
    """
    writer = GDFWriter(encoding=encoding)
    writer.add_graph_element(G)
    for line in str(writer).splitlines():
        yield line

@open_file(0,mode='rb')
def read_graphml(path,node_type=str):
    """Read graph in GraphML format from path.

    Parameters
    ----------
    path : file or string
       File or filename to write.  
       Filenames ending in .gz or .bz2 will be compressed.

    node_type: Python type (default: str)
       Convert node ids to this type 

    Returns
    -------
    graph: NetworkX graph
        If no parallel edges are found a Graph or DiGraph is returned.
        Otherwise a MultiGraph or MultiDiGraph is returned.

    Notes
    -----
    This implementation does not support mixed graphs (directed and unidirected 
    edges together), hypergraphs, nested graphs, or ports. 
    
    For multigraphs the GraphML edge "id" will be used as the edge
    key.  If not specified then they "key" attribute will be used.  If
    there is no "key" attribute a default NetworkX multigraph edge key
    will be provided.

    Files with the yEd "yfiles" extension will can be read but the graphics
    information is discarded.

    yEd compressed files ("file.graphmlz" extension) can be read by renaming
    the file to "file.graphml.gz".

    """
    reader = GDFReader(node_type=node_type)
    # need to check for multiple graphs
    glist = list(reader(path))
    return glist[0]


class GDFWriter(object):
    def __init__(self, graph=None, encoding="utf-8"):
        self.encoding = encoding
        self.csv = ''

        if graph is not None:
            self.add_graph_element(graph)
    
    def __str__(self):
        return self.csv

    def add_graph_element(self, G):
        """
        Serialize graph G in GDF to the stream.
        """
        strpage  = "nodedef>name VARCHAR\n"
        for node in G.nodes():
            strpage += node + "\n"
            
        strpage += "edgedef>node1 VARCHAR,node2 VARCHAR\n"
        for node1, node2 in G.edges():
                strpage += node1 + "," + node2 + "\n"
        
        self.csv = strpage

    def add_graphs(self, graph_list):
        """
        Add many graphs to this GraphML document.
        """
        for G in graph_list:
            self.add_graph_element(G)

    def dump(self, stream):
        file_or_filename = stream
        encoding=self.encoding
        
        if hasattr(file_or_filename, "write"):
            oFile = file_or_filename
        else:
            oFile = open(file_or_filename, "wb")
        write = oFile.write
        if not encoding: encoding = "us-ascii"
        
        write(self.csv.encode(encoding))
        
        if file_or_filename is not oFile:
            oFile.close()

class GDFReader(object):
    """Read a GraphML document.  Produces NetworkX graph objects.
    """
    def __init__(self, node_type=str):
        self.node_type=node_type
        
    def __call__(self, stream):
        if not hasattr(stream, "read"):
            source = open(stream, "rb")
        
        strpage = ''
        while 1:
            data = source.read(65536)
            if not data:
                break
            strpage += data
            
        self.csv = strpage
        return self.csv
    
        