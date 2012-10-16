import webapp2
import hashlib
import json
import conf, libsna, sessionmanager
import logging
from google.appengine.api import taskqueue
from google.appengine.api import memcache

conf = conf.Config()
cache = memcache.Client()

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        uid = self.request.get('id', None)
        if uid == None: uid = self.request.get('uid', None)
        session = sessionmanager.getsession(self, access_token=self.request.get('access_token', None))
        if session: access_token = session['access_token']
        else: access_token = self.request.get('access_token', '') 
        
        nodes = json.loads(self.request.get('nodes', None))
        edges = json.loads(self.request.get('edges', None))
        
        if nodes and edges:
            network = libsna.getusernetwork(uid)
            libSNA = libsna.SocialNetwork()
            libSNA.loadGraph(nodes=nodes, edges=edges)

            h = hashlib.sha1()
            h.update("%s - %s" % (libSNA.graph.nodes(), libSNA.graph.edges()))

            network.networkhash = h.hexdigest()
            network.setnodes(str(nodes))
            network.setedges(str(edges))
            network.setleague(None)
            network.put()
            
            cache.delete("%s_network" % uid)
            cache.add("%s_network" % uid, network)
            
            logging.info('Computation of network league sent to backend backend-indexes.')
            taskqueue.add(url='/networkleague', params={'id': uid,
                                                    'backend': True,
                                                    'code': self.request.get('code', None),
                                                    'access_token': access_token},
                      queue_name='indexes-queue', method='POST', target='backend-indexes')

    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
    