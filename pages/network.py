import webapp2
import re
import json
import os.path

from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from utils import conf, sessionmanager, fbutils

conf = conf.Config()
cache = memcache.Client()

class MainPage(webapp2.RequestHandler):
    def postPage(self, uid):
        code = self.request.get('code', None)
        frienduid = self.request.get('frienduid', None)
        
        session = sessionmanager.getsession(self)
        try:
            if session['me']['id'] != uid: code = None
        except: code = None
            
        action = self.request.get('action', None)
        if code != None and action == 'getFriendValues':
            objreturn = {}
            
            network = cache.get("%s_network" % frienduid)
            if network == None:
                q = db.GqlQuery("SELECT * FROM Index " +
                                "WHERE uid = :1 " +
                                "ORDER BY updated_time DESC",
                                frienduid)
                
                q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", frienduid)
                network = q.fetch(1)
                if len(network) == 0: network = None
                else:
                    network = network[0]
                    cache.add("%s_network" % frienduid, network, 60*60)

            if network:
                league = network.getleague()
                
                objreturn['nodes'] = len(network.getnodes())
                objreturn['edges'] = len(network.getedges())
                objreturn['friendleagueids'] = league and [row[0] for row in league] or None
                objreturn['friendleaguenames'] = league and [row[1] for row in league] or None
            else:
                objreturn['nodes'] = None
                objreturn['edges'] = None
                objreturn['friendleagueids'] = None
                objreturn['friendleaguenames'] = None
            
            self.response.out.write(json.dumps(objreturn))

    def renderPage(self, uid):
        code = self.request.get('code', None)
        
        session = sessionmanager.getsession(self)
        try:
            if session['me']['id'] != uid: code = None
        except: code = None
        
        nodes = None
        edges = None
        league = None
        hiddenleague = False
        
        network = cache.get("%s_network" % uid)
        if network == None:
            q = db.GqlQuery("SELECT * FROM Index " +
                            "WHERE uid = :1 " +
                            "ORDER BY updated_time DESC",
                            uid)
            
            q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", uid)
            network = q.fetch(1)
            if len(network) == 0: network = None
            else:
                network = network[0]
                cache.add("%s_network" % uid, network, 60*60)

        if network:
            nodes = network.getnodes()
            edges = network.getedges()
            league = network.getleague()
            
            try:
                if not fbutils.is_friend(session['access_token'], session['me']['id'], uid): 
                    for row in league:
                        row[1] = re.sub("\w", "x", row[1]).title()
                    hiddenleague = True
            except:
                for row in league:
                    row[1] = re.sub("\w", "x", row[1]).title()
                hiddenleague = True
        
        if session == None:
            app_friends = None
        else:
            app_friends = fbutils.fql("SELECT uid, name, is_app_user " +
                                      "FROM user " +
                                      "WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = me()) AND is_app_user = 1 " +
                                      "ORDER BY name", session['access_token'])
        
        template_values = {
            'conf': conf,
            'uid': uid,
            'me': session and session['me'] or None,
            'nodes': nodes,
            'edges': edges,
            'league': league,
            'hiddenleague': hiddenleague,
            'friends': app_friends,
            'isdesktop': session and session['isdesktop'] or False,
            'header': 'network',
            'code': code }

        root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
        self.response.out.write(template.render(os.path.join(root, 'pages/templates/network.html'), template_values))
        self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))

    def get(self, uid):
        self.renderPage(uid)

    def post(self, uid):
        self.postPage(uid)
