import webapp2
import os
import logging
import datetime
import json
import hashlib
import networkx as nx

from obj import obj_network
from utils import libsna, fbutils, conf, sessionmanager
from google.appengine.ext.webapp import template
from google.appengine.ext import db

conf = conf.Config()

def getNodesEdges(self, uid, session):
    result = fbutils.fql(
            "SELECT uid2 FROM friend WHERE uid1 = " + uid,
            session['access_token'])
    nodes = []
    for node in result:
        nodes.append(node['uid2'])
        
    result = fbutils.fql(
        "SELECT uid1, uid2 FROM friend WHERE " +
        "uid1 IN (SELECT uid2 FROM friend WHERE uid1 = " + uid + ") AND " +
        "uid2 IN (SELECT uid1 FROM friend WHERE uid2 = " + uid + ")",
        session['access_token']);
    
    edges = []
    for edge in result:
        edges.append([edge['uid1'], edge['uid2']])
        
    libSNA = libsna.SocialNetwork() 
    libSNA.loadGraph(nodes=nodes, edges=edges)

    h = hashlib.sha1()
    h.update("%s - %s" % (libSNA.graph.nodes(), libSNA.graph.edges()))
    networkhash = h.hexdigest()
    
    return nodes, edges, networkhash

def sorted_map(inmap):
        return sorted(inmap.iteritems(), key=lambda (k,v): (-v,k))
    
def computeLeague(libSNA, uid, session):
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
        "SELECT uid2 FROM friend WHERE uid1 = " + uid + ")",
        session['access_token'])
    
    nodes = {}
    for node in result:
        nodes[str(node['uid'])] = node['name'] 
    
    return [[name, nodes[name], str(d[name]), str(c[name]), str(b[name])] for name in names]

class PostHandler(webapp2.RequestHandler):    
    def post(self):
        session = sessionmanager.getsession(self)
        
        if session:
            roles = session['roles']
            
            if not 'technician' in roles:
                self.response.out.write("You are not a technician for this site. Access denied.")
                return
        
            action = self.request.get('action', None)
            code = self.request.get('code', None)
            uid = self.request.get('uid', None)
            
            if action == "getNodes":
                objreturn = {}
                nodes, edges, networkhash = getNodesEdges(self, uid, session)
                
                objreturn['nodes'] = str(nodes)
                objreturn['edges'] = str(edges)
                objreturn['networkhash'] = networkhash
                
                self.response.out.write(json.dumps(objreturn))
            elif action == "computeLeague":
                objreturn = {}
                nodes = eval(self.request.get('nodes', None))
                edges = eval(self.request.get('edges', None))
                
                libSNA = libsna.SocialNetwork() 
                libSNA.loadGraph(nodes=nodes, edges=edges)
    
                table = computeLeague(libSNA, uid, session)
                objreturn["league"] = str(table)               
                self.response.out.write(json.dumps(objreturn))
            elif action == "saveNetwork":
                networkhash = self.request.get('networkhash', None)
                nodes = self.request.get('nodes', None)
                edges = self.request.get('edges', None)
                league = self.request.get('league', None)
                
                q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", uid)
                network = q.fetch(1)
    
                if len(network) == 0: network = obj_network.Network(uid = uid)
                else: network = network[0]

                network.updated_time = datetime.datetime.now()
                network.networkhash = networkhash
                network.setnodes(nodes)
                network.setedges(edges)
                network.setleague(league)
                network.put()
    
                logging.info("Updatet network data for user: " + uid)
                self.redirect('/tech/viewnetwork?uid=' + uid + '&code=' + code)
            else:
                self.redirect('/tech/viewnetwork?uid=' + uid + '&code=' + code)

def parsePost(self):
    session = sessionmanager.getsession(self)
    
    if session:
        roles = session['roles']
        
        if not 'administrator' in roles:
            self.response.out.write("You are not an administrator for this site. Access denied.")
            return
    
        action = self.request.get('action', None)
        uid = self.request.get('uid', None)
        
        if action == "getNodes":
            objreturn = {}
            nodes, edges, networkhash = getNodesEdges(self, uid, session)
            
            q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", uid)
            network = q.fetch(1)

            if len(network) == 0: network = obj_network.Network(uid = uid)
            else: network = network[0]
            
            network.updated_time = datetime.datetime.now()
            network.setnodes(str(nodes))
            network.setedges(str(edges))
            network.networkhash = networkhash
            network.put()
            
            objreturn['nodes'] = str(nodes)
            objreturn['edges'] = str(edges)
            objreturn['networkhash'] = networkhash
            
            self.response.out.write(json.dumps(objreturn))
        elif action == "computeLeague":
            objreturn = {}
            nodes = eval(self.request.get('nodes', None))
            edges = eval(self.request.get('edges', None))
            
            libSNA = libsna.SocialNetwork() 
            libSNA.loadGraph(nodes=nodes, edges=edges)

            table = computeLeague(libSNA, uid, session)
            
            q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", uid)
            network = q.fetch(1)

            if len(network) == 0: network = obj_network.Network(uid = uid)
            else: network = network[0]
            
            network.updated_time = datetime.datetime.now()
            network.setleague(str(table))
            network.put()
            
            objreturn["league"] = str(table)               
            self.response.out.write(json.dumps(objreturn))
        else:
            renderPage(self, 'admin')

def renderPage(self, mode='admin'):
    session = sessionmanager.getsession(self)
    
    if session:
        roles = session['roles']
    
        if mode == 'admin' and not 'administrator' in roles:
            self.response.out.write("You are not an administrator for this site. Access denied.")
            return
        elif not 'technician' in roles:
            self.response.out.write("You are not a technician for this site. Access denied.")
            return
        
        code = self.request.get('code', None)
        uid = self.request.get('uid', None)
        
        users = None
        network = None
        
        if uid == None:
            upload_url = '/' + mode + '/viewnetwork?code=' + code
            users = []
            q = db.GqlQuery("SELECT * FROM User")
            for user in q: users.append(user)
        else:
            if mode == 'tech': upload_url = '/tech/savenetwork?uid=' + uid + '&code=' + code
            else: upload_url = '/admin?code=' + code
            
            if uid == "_new_":
                network = None
            else:
                q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", uid)
                network = q.fetch(1)
    
                if len(network) == 0: network = None
                else: network = network[0]
            
        
        template_values = {
            'appId': conf.FBAPI_APP_ID,
            'token': session['access_token'], 
            'app': session['appid'],
            'conf': conf,
            'me': session['me'],
            'roles': roles,
            'upload_url': upload_url,
            'mode': mode,
            'uid': uid,
            'users': users,
            'network': network,
            'isdesktop': session['isdesktop'],
            'header': '',
            'code': code }
    
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
        self.response.out.write(template.render(os.path.join(root, 'admin/templates/vieweditnetwork.html'), template_values))
        self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))
    else:
        self.redirect(fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)))
            
class MainViewPage(webapp2.RequestHandler):
    def get(self):
        renderPage(self, 'admin')

    def post(self):
        parsePost(self)

class MainEditPage(webapp2.RequestHandler):
    def get(self):
        renderPage(self, 'tech')

    def post(self):
        renderPage(self, 'tech')