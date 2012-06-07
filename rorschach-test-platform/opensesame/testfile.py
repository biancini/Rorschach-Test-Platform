import webapp2

from google.appengine.ext import db
from google.appengine.api import memcache
from utils import fbutils, conf, sessionmanager

conf = conf.Config()
cache = memcache.Client()

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        access_token = self.request.get('token', None)
        if access_token: session = sessionmanager.getsession(self, access_token=access_token, redirect_uri=fbutils.base_url(self)+'opensesame/access')
        else: session = sessionmanager.getsession(self)
            
        if session:
            testid = self.request.get('testid')
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
            
            self.response.headers['Content-Type'] = "application/x-gzip"
            self.response.headers['Content-Disposition'] = "attachment; filename=" + str(test.testfilename)
            self.response.out.write(test.testfile)
        else:
            self.response.out.write('Wrong session')
        
    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
