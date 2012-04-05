import webapp2
import re
import json
import os.path

from google.appengine.ext import db
from google.appengine.ext.webapp import template
from utils import conf, sessionmanager, fbutils

conf = conf.Config()

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
            q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", frienduid)
            networks  = q.fetch(1)

            if not len(networks) == 0:
                network = networks[0]
                league = network.getleague()
                
                rank = -1
                if league != None:
                    i = 1 
                    rank= 0
                    for row in league:
                        if row[0] == uid: rank = i
                        i += 1
                    
                objreturn['rank'] = rank
                objreturn['nodes'] = len(network.getnodes())
                objreturn['edges'] = len(network.getedges())
            else:
                objreturn['rank'] = None
                objreturn['nodes'] = None
                objreturn['edges'] = None
            
            self.response.out.write(json.dumps(objreturn))
        elif code != None and action == 'postOnFriendWall':
            frienduid = self.request.get('frienduid', None)
            objreturn = {}
            
            objreturn['return'] = False
            objreturn['message'] = 'Method not yet implemented'
            self.response.out.write(json.dumps(objreturn))
        elif code != None and action == 'sendMessageToFriend':
            frienduid = self.request.get('frienduid', None)
            objreturn = {}
            
            objreturn['return'] = False
            objreturn['message'] = 'Method not yet implemented'
            self.response.out.write(json.dumps(objreturn))
        else:
            self.response.out.write("Error, session invalid or invalid action.")

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
        
        q = db.GqlQuery("SELECT * FROM Network WHERE uid = :1", uid)
        networks = q.fetch(1)

        if not len(networks) == 0:
            network = networks[0]
            
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
            'nodes': nodes,
            'edges': edges,
            'league': league,
            'hiddenleague': hiddenleague,
            'friends': app_friends,
            'isdesktop': session['isdesktop'],
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
