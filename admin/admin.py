import webapp2
import os.path
from datetime import date

from utils import fbutils, conf, sessionmanager
from google.appengine.ext.webapp import template
from google.appengine.ext import db

conf = conf.Config()

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        session = sessionmanager.getsession(self)
        
        if session:
            roles = session['roles']
            if not 'administrator' in roles:
                self.response.out.write("You are not an administrator for this site. Access denied.")
                return
        
            withindates = {}
            tests = []
            q = db.GqlQuery("SELECT * FROM Test")
            for test in q:
                if test != None and test.startdate != None and test.enddate != None:
                    if test.startdate <= date.today() and test.enddate >= date.today():
                        withindates[test.name] = True

                tests.append(test)
            
            template_values = {
                'appId': conf.FBAPI_APP_ID,
                'token': session['access_token'], 
                'app': session['appid'],
                'conf': conf,
                'me': session['me'],
                'roles': roles,
                'tests': tests,
                'withindates': withindates,
                'isdesktop': session['isdesktop'],
                'header': '',
                'code': self.request.get('code', None) }
            
            root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
            self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
            self.response.out.write(template.render(os.path.join(root, 'admin/templates/admin.html'), template_values))
            self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))
        else:
            self.redirect(fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)))

    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
