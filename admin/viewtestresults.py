import webapp2
import os.path

from obj import obj_testresults
from utils import fbutils, conf, sessionmanager
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache

conf = conf.Config()
cache = memcache.Client()

def renderPage(self):
    session = sessionmanager.getsession(self)
    
    if session:
        roles = session['roles']
    
        if not 'administrator' in roles:
            self.response.out.write("You are not an administrator for this site. Access denied.")
            return
        
        code = self.request.get('code', None)
        upload_url = '/admin/savetest?code=' + code
        
        testid = self.request.get('testid', None)
        tests = cache.get("tests")
        if tests:
            test = None
            for curtest in tests:
                if curtest.testid == testid: test = curtest
            
        else:
            q = db.GqlQuery("SELECT * FROM Test WHERE testid = :1", testid)
            test = q.fetch(1)

            if len(test) > 0: test = test[0]
            else: test = None
        
        testresults = []
        q = db.GqlQuery("SELECT * FROM TestResults WHERE testid = :1", testid)
        for result in q: testresults.append(result)
        
        template_values = {
            'appId': conf.FBAPI_APP_ID,
            'token': session['access_token'], 
            'app': session['appid'],
            'conf': conf,
            'me': session['me'],
            'roles': roles,
            'test': test,
            'testresults': testresults,
            'upload_url': upload_url,
            'isdesktop': session['isdesktop'],
            'header': '',
            'code': code }
        
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
        self.response.out.write(template.render(os.path.join(root, 'admin/templates/viewtestresults.html'), template_values))
        self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))
    else:
        self.redirect(fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)))
            
class MainPage(webapp2.RequestHandler):
    def get(self):
        renderPage(self)

    def post(self):
        renderPage(self)