import webapp2

from google.appengine.ext import db
from utils import fbutils, conf, sessionmanager
from obj import obj_testresults

conf = conf.Config()

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        access_token = self.request.get('token', None)
        if access_token: session = sessionmanager.getsession(self, access_token=access_token, redirect_uri=fbutils.base_url(self)+'opensesame/access')
        else: session = sessionmanager.getsession(self)
            
        if session:
            testid = self.request.get('testid')
            q = db.GqlQuery("SELECT * FROM Test WHERE testid = :1", testid)
            
            tests = q.fetch(1)
            if len(tests) <= 0:
                self.response.out.write('Wrong test id')
                return
            
            q = db.GqlQuery("SELECT * FROM TestResults WHERE testid = :1", testid)
            results = q.fetch(1)
            if len(results) > 0: result = results[0]
            else: result = obj_testresults.TestResults(testid=testid)
            
            self.response.out.write('OK ' + result.stroutput())
        else:
            self.response.out.write('Wrong session')
        
    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
