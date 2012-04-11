import webapp2
import libsna, conf, fbutils, sessionmanager

from google.appengine.ext import db
import networkx as nx
from google.appengine.api import memcache

conf = conf.Config()
cache = memcache.Client()

def sorted_map(inmap):
        return sorted(inmap.iteritems(), key=lambda (k,v): (-v,k))

def computeLeague(libSNA, session):
    d = nx.degree(libSNA.graph)
    c = nx.closeness_centrality(libSNA.graph)
    b = nx.betweenness_centrality(libSNA.graph)
    
    ds = sorted_map(d)
    cs = sorted_map(c)
    bs = sorted_map(b)
    
    weights = [.50, .30, .20]
    
    names1 = [x[0] for x in ds[:10]]
    names2 = [x[0] for x in cs[:10]]
    names3 = [x[0] for x in bs[:10]]
    
    names = list(set(names1) | set(names2) | set(names3))
    names = sorted(names, key = lambda name: (float(d[name])/ds[0][1])*weights[0] + (float(c[name])/cs[0][1])*weights[1] + (float(b[name])/bs[0][1])*weights[2], reverse = True)
    
    result = fbutils.fql(
        "SELECT uid, name FROM user WHERE uid IN ( " \
        "SELECT uid2 FROM friend WHERE uid1 = me() )",
        session['access_token'])
    
    nodes = {}
    for node in result:
        nodes[str(node['uid'])] = node['name']
    
    return [[name, nodes[name], str(d[name]), str(c[name]), str(b[name])] for name in names]

class MainPage(webapp2.RequestHandler):
    def getLibSNA(self, session):
        network = libsna.getusernetwork(self.request.get('id', None))
        libSNA = libsna.SocialNetwork()
        
        if network.getnodes() == None or network.getedges() == None: return None
        else: libSNA.loadGraph(nodes=network.getnodes(), edges=network.getedges())
        
        return libSNA

    def renderPage(self):
        session = {}
        
        uid = self.request.get('id', None)
        backend = self.request.get('backend', False)
        nodes = self.request.get('nodes', None)
        edges = self.request.get('edges', None)
        
        if backend: session['access_token'] = self.request.get('access_token', '') 
        else: session = sessionmanager.getsession(self)

        if nodes == None or edges == None:
            libSNA = self.getLibSNA(session)
        else:
            libSNA = libsna.SocialNetwork()
            libSNA.loadGraph(nodes, edges)
        
        table = computeLeague(libSNA, session)
        
        network = cache.get("%s_network" % uid)
        if network == None:
            q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", uid)
            network = q.fetch(1)
            if len(network) == 0: network = None
            else:
                network = network[0]
                cache.add("%s_network" % uid, network, 60*60)
        if network > 0:
            network = network[0]
            network.setleague(str(table))
            network.put()
            cache.delete("%s_network" % uid)
                
        self.response.out.write(str(table))

    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
