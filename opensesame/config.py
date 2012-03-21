import webapp2
import json

from datetime import date
from google.appengine.ext import db
from utils import fbutils, conf, sessionmanager

conf = conf.Config()

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        access_token = self.request.get('token', None)
        session = sessionmanager.getsession(self, access_token=access_token, redirect_uri=fbutils.base_url(self)+'opensesame/access')
        
        objreturn = {}
        objreturn['result'] = False
        objreturn['message'] = 'Wrong session'
        
        if session:
            roles = session['roles']
            if not 'administrator' in roles:
                objreturn['message'] = 'Wrong role, you are not administrator'
            else:
                objreturn['tests'] = []
                q = db.GqlQuery("SELECT * FROM Test")
                for test in q:
                    if test != None and test.startdate != None and test.enddate != None:
                        curTest = {}
                        curTest['testid'] = test.testid
                        curTest['name'] = test.name
                        curTest['description'] = test.description
                        curTest['startdate'] = test.startdate.strftime("%d/%m/%Y")
                        curTest['enddate'] = test.enddate.strftime("%d/%m/%Y")
                        curTest['withindates'] = test.startdate <= date.today() and test.enddate >= date.today()
                        curTest['active'] = test.active
                        
                        objreturn['tests'].append(curTest)
                
                objreturn['indexes'] = conf.INDEXES
                objreturn['result'] = True
                objreturn['message'] = ''
        
        self.response.out.write(json.dumps(objreturn))
        
    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
