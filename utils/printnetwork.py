import webapp2
import networkx as nx

from google.appengine.ext import db
from utils import conf, sessionmanager

conf = conf.Config()

def loadGraph(nodes, edges):
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node)
    for edge in edges:
        graph.add_edge(edge[0], edge[1])
    graph.name = "Social Network"
    return graph

class MainPage(webapp2.RequestHandler):
    def renderPage(self, extension):
        uid = self.request.get('uid', None)
        network = None
        
        strpage = "Error."
        supported_extensions = [ 'gdf', 'graphml' ]
        if not uid == None and extension in supported_extensions:
            session = sessionmanager.getsession(self)
            if session and session['me']['id'] == uid: 
                q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", uid)
                networks = q.fetch(1)
        
                if not len(networks) == 0:
                    network = networks[0]
                    graph = loadGraph(network.getnodes(), network.getedges())
                    
                    strpage = ''
                    if extension == 'gdf':
                        for line in nx.generate_gdf(graph):
                            strpage += line + '\n'
                        self.response.headers['Content-Type'] = "text/gdf"
                            
                    if extension == 'graphml':
                        for line in nx.generate_graphml(graph):
                            strpage += line + '\n'
                        self.response.headers['Content-Type'] = "xml/graphml"
            
        self.response.out.write(strpage)

    def get(self, extension):
        self.renderPage(extension)

    def post(self, extension):
        self.renderPage(extension)
