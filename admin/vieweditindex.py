import webapp2
import os
import logging
import datetime
import json

from obj import obj_index
from utils import fbutils, conf, sessionmanager, computeprofileindex
from google.appengine.ext.webapp import template
from google.appengine.ext import db

conf = conf.Config()

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
            
            if action == "selectUid":
                objreturn = {}
                objreturn['indexes'] = []
                
                q = db.GqlQuery("SELECT * FROM Index WHERE uid = :1", uid)
                for index in q:
                    if not index.name in objreturn['indexes']: objreturn['indexes'].append(index.name)
                
                self.response.out.write(json.dumps(objreturn))
            elif action == "computeIndex":
                indexname = self.request.get('indexname', None)
                libSNA = computeprofileindex.getLibSNA(self, session)
                objreturn = computeprofileindex.computeIndex(self, libSNA, indexname, False, session, saveInDatastore=False)
                
                if 'nodes' in objreturn: objreturn['nodes'] = str(objreturn['nodes']) 
                if 'edges' in objreturn: objreturn['edges'] = str(objreturn['edges']) 
                self.response.out.write(json.dumps(objreturn))
            elif action == "saveIndex":
                indexname = self.request.get('indexname', None)
                networkhash = self.request.get('networkhash', None)
                value = self.request.get('value', None)
                edges = self.request.get('edges', None)
                nodes = self.request.get('nodes', None)
                
                index = obj_index.Index(uid = self.request.get('uid', None), name = indexname)
                index.updated_time = datetime.datetime.now()
                index.networkhash = networkhash
            
                index.value = float(value)
                if not edges == None: index.set_edgevalues(edges)
                if not nodes == None: index.set_nodevalues(nodes)
                index.put()
    
                logging.info("Updated index data for user: " + uid)
                self.redirect('/tech/viewindex?uid=' + uid + '&code=' + code)
            else:
                self.redirect('/tech/viewindex?uid=' + uid + '&code=' + code)

def parsePost(self):
    session = sessionmanager.getsession(self)
    
    if session:
        roles = session['roles']
        
        if not 'administrator' in roles:
            self.response.out.write("You are not an administrator for this site. Access denied.")
            return
    
        action = self.request.get('action', None)
        uid = self.request.get('uid', None)
        
        if action == "selectUid":
            objreturn = {}
            objreturn['indexes'] = []
            
            q = db.GqlQuery("SELECT * FROM Index WHERE uid = :1", uid)
            for index in q:
                if not index.name in objreturn['indexes']: objreturn['indexes'].append(index.name)
            
            self.response.out.write(json.dumps(objreturn))
            
        elif action == "computeIndex":
            indexname = self.request.get('indexname', None)
            libSNA = computeprofileindex.getLibSNA(self, session)
            objreturn = computeprofileindex.computeIndex(self, libSNA, indexname, False, session)
            
            renderPage(self, 'admin')
        else:
            renderPage(self, 'admin')

def renderPage(self, mode='admin'):
    session = sessionmanager.getsession(self)
    
    if self.request.get('code', None) and session:
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
        index = None
        
        if uid == None:
            upload_url = '/' + mode + '/viewindex?code=' + code
            users = []
            q = db.GqlQuery("SELECT * FROM User")
            for user in q: users.append(user)
        else:
            if mode == 'tech': upload_url = '/tech/saveindex?uid=' + uid + '&code=' + code
            else: upload_url = '/admin?code=' + code
            
            indexname = self.request.get('indexname', None)
            
            if indexname != "_new_":
                q = db.GqlQuery("SELECT * FROM Index WHERE uid = :1 AND name = :2 ORDER BY updated_time DESC",
                                uid, indexname)
                index = q.fetch(1)

                if len(index) == 0: index = None
                else: index = index[0]
            else:
                index = None
            
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
            'index': index,
            'isdesktop': session and session['isdesktop'] or False,
            'header': '',
            'code': code }
        
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
        self.response.out.write(template.render(os.path.join(root, 'admin/templates/vieweditindex.html'), template_values))
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