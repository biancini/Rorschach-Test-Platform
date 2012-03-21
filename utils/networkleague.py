import webapp2
import libsna, conf, fbutils, sessionmanager

from google.appengine.ext import db
import networkx as nx

conf = conf.Config()

def sorted_map(inmap):
        return sorted(inmap.iteritems(), key=lambda (k,v): (-v,k))

def computeLeague(libSNA, session):
    d = nx.degree(libSNA.graph)
    c = nx.closeness_centrality(libSNA.graph)
    b = nx.betweenness_centrality(libSNA.graph)
    
    ds = sorted_map(d)
    cs = sorted_map(c)
    bs = sorted_map(b)
    
    names1 = [x[0] for x in ds[:10]]
    names2 = [x[0] for x in cs[:10]]
    names3 = [x[0] for x in bs[:10]]
    
    names = list(set(names1) | set(names2) | set(names3))
    names = sorted(names, key = lambda name: d[name]/ds[0][1]*300 + c[name]/cs[0][1]*200 + b[name]/bs[0][1]*100, reverse = True)
    
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
        
        q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", uid)
        network = q.fetch(1)
    
        if len(network) > 0:
            network = network[0]
            network.setleague(str(table))
            network.put()
                
        self.response.out.write(str(table))

    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
