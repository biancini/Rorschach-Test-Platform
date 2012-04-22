import webapp2
import logging
import time, datetime
import os.path

from obj import obj_user
from utils import fbutils, conf, sessionmanager
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache

conf = conf.Config()
cache = memcache.Client()

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        session = sessionmanager.getsession(self)
        
        if session:
            app_friends = fbutils.fql(
                "SELECT uid, name, is_app_user, pic_square "
                "FROM user "
                "WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = me()) AND "
                "  is_app_user = 1", session['access_token'])
            
            users = cache.get("users")
            if users == None:
                users = []
                q = db.GqlQuery("SELECT * FROM User")
                for user in q: users.append(user)
                cache.add("users", users)
            
            curuser = None
            for user in users:
                if user.uid == session['me']['id']: curuser = user

            datefb = session['me']['updated_time'].replace("+0000", "").replace("T", " ")
            datefb = datetime.datetime.fromtimestamp(
                   time.mktime(time.strptime(datefb, "%Y-%m-%d %H:%M:%S")))
            
            if curuser:
                datedb = curuser.updated_time

                if datefb > datedb:
                    curuser.first_name = session['me']['first_name']
                    curuser.last_name = session['me']['last_name']
                    curuser.link = session['me']['link']
                    if 'username' in session['me']:
                        curuser.username = session['me']['username']
                    curuser.updated_time = datefb
                    curuser.put()
                    users = cache.delete("users")
                  
                    logging.info('User updated: ' + session['me']['id'])
            else:
                curuser = obj_user.User(uid = session['me']['id'])
                curuser.first_name = session['me']['first_name']
                curuser.last_name = session['me']['last_name']
                curuser.link = session['me']['link']
                if 'username' in session['me']:
                    curuser.username = session['me']['username']
                curuser.updated_time = datefb
                curuser.put()
                users = cache.delete("users")
                
                logging.info('User added: ' + session['me']['id'])

            indexes = cache.get("%s_indexes" % session['me']['id'])
            if indexes == None:
                indexes = {}
                q = db.GqlQuery("SELECT * FROM Index " +
                                "WHERE uid = :1 " +
                                "ORDER BY updated_time DESC",
                                session['me']['id'])
            
                for index in q:            
                    if not index.networkhash == None and \
                    not index.value == None and \
                    not index.name in indexes.keys():
                        indexes[index.name] = index
                        
                cache.add("%s_indexes" % session['me']['id'], indexes, 60*60)
            
            tests = cache.get("tests")
            if tests == None:
                tests = []
                q = db.GqlQuery("SELECT * FROM Test")
                for test in q: tests.append(test)
                cache.add("tests", tests)
                
            testsactive = []
            for test in tests:
                    if test.active and datetime.date.today() >= test.startdate and datetime.date.today() <= test.enddate:
                        testsactive.append(test)


            template_values = {
                'appId': conf.FBAPI_APP_ID,
                'token': session['access_token'],
                'app_friends': app_friends,
                'app': session['appid'],
                'conf': conf,
                'me': session['me'],
                'roles': session['roles'],
                'computedindexes': indexes.keys(),
                'numindexes': len(conf.INDEXES),
                'tests': testsactive,
                'isdesktop': session['isdesktop'],
                'header': '',
                'code': self.request.get('code') }

            root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
            self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
            self.response.out.write(template.render(os.path.join(root, 'pages/templates/home.html'), template_values))
            self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))
        else:
            template_values = {
                'title': 'Rorschach Test Platform',
                'page' : 'Home',
                'conf': conf,
                'isdesktop': sessionmanager.isDesktop(self.request),
                'loginurl' : fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)) }
            
            root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
            self.response.out.write(template.render(os.path.join(root, 'pages/templates/nologin.html'), template_values))

    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()

