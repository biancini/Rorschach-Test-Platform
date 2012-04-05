import webapp2
import logging
import time, datetime
import os.path

from obj import obj_user
from utils import fbutils, conf, sessionmanager
from google.appengine.ext.webapp import template
from google.appengine.ext import db

conf = conf.Config()

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        session = sessionmanager.getsession(self)
        
        if session:
            app_friends = fbutils.fql(
                "SELECT uid, name, is_app_user, pic_square "
                "FROM user "
                "WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = me()) AND "
                "  is_app_user = 1", session['access_token'])
            
            q = db.GqlQuery("SELECT * FROM User WHERE uid = :1", session['me']['id'])
            users = q.fetch(1)

            datefb = session['me']['updated_time'].replace("+0000", "").replace("T", " ")
            datefb = datetime.datetime.fromtimestamp(
                   time.mktime(time.strptime(datefb, "%Y-%m-%d %H:%M:%S")))
            
            if len(users) > 0:
                curuser = users[0]
                datedb = curuser.updated_time

                if datefb > datedb:
                    curuser.first_name = session['me']['first_name']
                    curuser.last_name = session['me']['last_name']
                    curuser.link = session['me']['link']
                    if 'username' in session['me']:
                        curuser.username = session['me']['username']
                    curuser.updated_time = datefb
                    curuser.put()
                  
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
              
                logging.info('User added: ' + session['me']['id'])

            indexes = []
            q = db.GqlQuery("SELECT * FROM Index " +
                        "WHERE uid = :1 " +
                        "ORDER BY updated_time DESC",
                        session['me']['id'])
            
            for index in q:            
                if not index.networkhash == None and \
                   not index.value == None and \
                   not index.name in indexes:
                    indexes.append(index.name)
                    
            tests = []
            q = db.GqlQuery("SELECT * FROM Test")
            
            for test in q:
                if test.active and datetime.date.today() >= test.startdate and datetime.date.today() <= test.enddate:
                    tests.append(test)

            template_values = {
                'appId': conf.FBAPI_APP_ID,
                'token': session['access_token'],
                'app_friends': app_friends,
                'app': session['appid'],
                'conf': conf,
                'me': session['me'],
                'roles': session['roles'],
                'computedindexes': indexes,
                'numindexes': len(conf.INDEXES),
                'tests': tests,
                'isdesktop': session['isdesktop'],
                'header': '',
                'code': self.request.get('code') }

            root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
            self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
            self.response.out.write(template.render(os.path.join(root, 'pages/templates/home.html'), template_values))
            self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))
        else:
            self.response.out.write('''
            <html><head>
            <script type="text/javascript">
            <!--
            var _gaq = _gaq || [];
            _gaq.push(['_setAccount', 'UA-256445-3']);
            _gaq.push(['_trackPageview']);

            (function() {
              var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
              ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
              var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
            })();
            // -->
            </script>''')
            
            self.response.out.write('<meta HTTP-EQUIV="REFRESH" content="0; url=' +
                fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)) +
                '"></head><body></body></html>')
                              
            #self.redirect(fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)))

    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()

