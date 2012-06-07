from networkx import Graph
from networkx import degree_centrality, closeness_centrality, eigenvector_centrality, betweenness_centrality
from networkx import find_cliques
import logging
import conf
import datetime
import numpy as np

import networkx as nx
from myexceptions import network_big
from google.appengine.ext import db
from google.appengine.api import memcache
from obj import obj_network

conf = conf.Config()
cache = memcache.Client()

def getusernetwork(uidin):
    network = cache.get("%s_network" % uidin)
    if network == None:
        q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", uidin)
        network = q.fetch(1)
        if len(network) == 0: network = None
        else:
            network = network[0]
            cache.add("%s_network" % uidin, network, 60*60)
    
    if not network:
        network = obj_network.Network(uid = uidin)
        network.updated_time = datetime.datetime.now()
        network.put()
        
    return network

class SocialNetwork(object):
    """Object oriented interface for conducting social network analysis."""
    valid_indexes = []
    for index_name in conf.INDEXES.keys():
            valid_indexes.append(index_name)
            
    cache = None
    
    def __init__(self):
        logging.info("libSNA object created.")
        self.graph = Graph()
        self.measures = {}
        self.nodesmeasures = {}
        self.edgesmeasures = {}
        for index in self.valid_indexes: self.measures[index] = None
        
    def getNodes(self):
        nodes = self.graph.nodes()
        nodes.sort()
        return nodes
        
    def getEdges(self):
        edges = self.graph.edges()
        return edges
        
    def loadGraph(self, nodes, edges):
        logging.info("Loading network from input variables")
        for node in nodes:
            self.graph.add_node(node)
        for edge in edges:
            self.graph.add_edge(edge[0], edge[1])
        self.graph.name = "Social Network"
        logging.info("Finished loading network.")

    def runMeasure(self, measure_name, backend):
        if measure_name in self.valid_indexes:
            eval('self.calculate_' + measure_name.replace(' ', '_') + '(backend)')
        else:
            logging.error("Unable to calculate the measure (%s)"%(measure_name))
            
    def returnResults(self, measure_name, value = 'value'):
        if measure_name in self.valid_indexes:
            if value == 'value': return self.measures[measure_name]
            elif value == 'nodes': return self.nodesmeasures[measure_name]
            elif value == 'edges': return self.edgesmeasures[measure_name]
        else:
            return None
            
    def displayResults(self, measure_name, value = 'value'):
        if measure_name in self.valid_indexes:
            if value == 'value': logging.info((conf.INDEX_TYPES[measure_name] + '.') % self.measures[measure_name])
            elif value == 'nodes': logging.info(str(self.nodesmeasures[measure_name] or '<null>'))
            elif value == 'edges': logging.info(str(self.edgesmeasures[measure_name] or '<null>'))
        else:
            logging.error("Unable to calculate the measure (%s)"%(measure_name))
            
    def calculateMeasures(self, backend=False):
        for measure_name in self.valid_indexes:
            self.runMeasure(measure_name, backend=False)
    
    def calculate_density(self, backend=False):        
        logging.info("Calculating density.")
        
        nodes = self.graph.nodes()
        edges = self.graph.edges()
        tot_edges = float(len(nodes) * (len(nodes)-1))
        tot_edges = tot_edges / 2
        num_edges = float(len(edges))
        
        w = {}
        for n1 in nodes:
            for n2 in nodes:
                w[n1,n2] = 0.0
        
        for n1,n2 in edges:
            w[n1,n2] = 1.0
            
        
        self.measures['density'] = num_edges / tot_edges * 100
        self.nodesmeasures['density'] = None
        self.edgesmeasures['density'] = w 
        
    def calculate_geodesic(self, backend=False):        
        logging.info("Calculating geodesic.")
        
        path = self.floyd_warshall(backend)
        nodes = self.graph.nodes()
        dividend = 0
        geodesic = float(0)
        geodesic_edges = {}
        
        for i in nodes:
            for j in nodes:
                try:
                    geodesic_edges[i,j] = path[i,j]
                    geodesic += path[i,j]
                    dividend += 1
                except KeyError:
                    pass
        
        geodesic /= dividend
        
        self.measures['geodesic'] = geodesic
        self.nodesmeasures['geodesic'] = None
        self.edgesmeasures['geodesic'] = geodesic_edges
        
    def calculate_fragmentation(self, backend=False):        
        logging.info("Calculating fragmentation.")
        
        nodes = self.graph.nodes()
        w = self.floyd_warshall(backend)
        fragmentation = float(0)
        
        for i in nodes:
            for j in nodes:
                try:
                    w[i,j]
                except KeyError:
                    fragmentation += 1
                    pass
        
        fragmentation /= len(nodes)*(len(nodes)-1)
        self.measures['fragmentation'] = fragmentation * 100
        self.nodesmeasures['fragmentation'] = None
        self.edgesmeasures['fragmentation'] = w
        
    def calculate_diameter(self, backend=False):        
        logging.info("Calculating diameter.")
        
        path = self.floyd_warshall(backend)
        nodes = self.graph.nodes()
        diameter = float(0)
        
        for i in nodes:
            for j in nodes:
                try:
                    diameter = max(diameter, path[i,j])
                except KeyError:
                    pass
    
        self.measures['diameter'] = diameter
        self.nodesmeasures['diameter'] = None
        self.edgesmeasures['diameter'] = path
        
    def calculate_degree(self, backend=False):
        logging.info("Calculating degree.")
        
        degrees = degree_centrality(self.graph)
        degree = float(sum(degrees.values())/len(degrees.values()))
        
        self.measures['degree'] = degree * 100
        self.nodesmeasures['degree'] = degrees
        self.edgesmeasures['degree'] = None
        
    def calculate_centralization(self, backend=False):
        logging.info("Calculating centralization.")
        
        degrees = degree_centrality(self.graph)
        centralization = float(0)
        maxdegree = max(degrees.values())
        for degree in degrees.values():
            centralization += maxdegree-degree
        centralization /= len(degrees.values())-1
        
        self.measures['centralization'] = centralization * 100
        self.nodesmeasures['centralization'] = degrees
        self.edgesmeasures['centralization'] = None
        
    def calculate_closeness(self, backend=False):        
        logging.info("Calculating closeness.")

        closenesses = closeness_centrality(self.graph)
        closeness = float(sum(closenesses.values())/len(closenesses.values()))
        
        self.measures['closeness'] = closeness * 100
        self.nodesmeasures['closeness'] = closenesses
        self.edgesmeasures['closeness'] = None
        
    def calculate_eigenvector(self, backend=False):        
        logging.info("Calculating eigenvector.")
        
        eigenvectors = eigenvector_centrality(self.graph)
        eigenvector = float(sum(eigenvectors.values())/len(eigenvectors.values()))
        
        self.measures['eigenvector'] = eigenvector * 100
        self.nodesmeasures['eigenvector'] = eigenvectors
        self.edgesmeasures['eigenvector'] = None
        
    def calculate_betweenness(self, backend=False):
        logging.info("Calculating betweenness.")
        
        betweennesses = betweenness_centrality(self.graph)
        betweenness = float(sum(betweennesses.values())/len(betweennesses.values()))
        
        self.measures['betweenness'] = betweenness * 100
        self.nodesmeasures['betweenness'] = betweennesses
        self.edgesmeasures['betweenness'] = None

    def calculate_cliques(self, backend=False):
        logging.info("Calculating cliques.")
        cliques = list(find_cliques(self.graph))
        
        w = {}
        nodes = self.graph.nodes()
        for node in nodes:
            w[node] = 0.0
            for clique in cliques:
                if node in clique:
                    w[node] += 1
        
        self.measures['cliques'] = len(cliques)
        self.nodesmeasures['cliques'] = w
        self.edgesmeasures['cliques'] = None
                
    def calculate_comembership(self, backend=False):
        logging.info("Calculating comembership.")
        
        nodes = self.graph.nodes()
        n = len(nodes)
        if not backend and n > 500:
            raise network_big.NetworkTooBigException(n)
        
        cliques = list(find_cliques(self.graph))
        
        w = {}
        for clique in cliques:
            for node1 in clique:
                for node2 in clique:
                    try:
                        w[node1,node2] += 1
                    except KeyError:
                        w[node1,node2] = 1
                        
        nodes = w.keys()
        comembership = float(0)
        for node1, node2 in nodes:
            if node1 != node2: comembership += w[node1,node2]
            
        num_nodes = len(self.graph.nodes())
        comembership /= num_nodes*(num_nodes-1)
        
        self.measures['comembership'] = comembership
        self.nodesmeasures['comembership'] = None
        self.edgesmeasures['comembership'] = w
        
    def calculate_components(self, backend=False):
        logging.info("Calculating components.")
        components = nx.connected_component_subgraphs(self.graph)
        
        w = {}
        nodes = self.graph.nodes()
        for node in nodes:
            w[node] = 0.0
        
        for component in components:
            if len(component) > 1:
                for node in component:
                    w[node] += 1
        
        self.measures['components'] = len(components)
        self.nodesmeasures['components'] = w
        self.edgesmeasures['components'] = None
    
    def floyd_warshall(self, backend):
        nodes = self.graph.nodes()
        
        if not backend and len(nodes) > 400:
            raise network_big.NetworkTooBigException(len(nodes))
        
        logging.info("Computing Floyd-Warshall.")
        
        infvalue = 127 #sys.maxint
        F = nx.floyd_warshall_numpy(self.graph, dtype=np.int8, infvalue=infvalue)
       
        w = {}
        for i in range(0, len(nodes)):
            for j in range(0, len(nodes)):
                if not F[i,j] == infvalue:
                    w[nodes[i],nodes[j]] = F[i,j]
        
        return w