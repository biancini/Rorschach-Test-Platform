import webapp2
import os.path
import logging
import datetime
from obj import obj_test

from utils import fbutils, conf, sessionmanager
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache

conf = conf.Config()
cache = memcache.Client()

class ActiveHandler(webapp2.RequestHandler):
    def get(self):
        session = sessionmanager.getsession(self)
        
        if session:
            roles = session['roles']
            if not 'administrator' in roles:
                self.response.out.write("You are not an administrator for this site. Access denied.")
                return
        
            code = self.request.get('code', None)
            testid = self.request.get('testid', None)
            active = self.request.get('active', False) == "true"
            
            tests = cache.get("tests")
            if tests:
                test = None
                for curtest in tests:
                    if curtest.testid == testid:
                        test = curtest
                
            else:
                tests = cache.get("tests")
                if tests:
                    test = None
                    for curtest in tests:
                        if curtest.testid == testid:
                            test = curtest
                    
                else:
                    q = db.GqlQuery("SELECT * FROM Test WHERE testid = :1", testid)
                    test = q.fetch(1)
    
                    if len(test) > 0: test = test[0]
                    else: test = None
            
            if test:
                test.active = active
                test.put()
                cache.delete("tests")
                
                if (active): logging.info("Activated the psychological test: " + testid)
                else: logging.info("Deactivated the psychological test: " + testid)
                
            self.redirect('/admin?code=' + code)

class DelHandler(webapp2.RequestHandler):
    def get(self):
        session = sessionmanager.getsession(self)
        
        if session:
            roles = session['roles']
            if not 'administrator' in roles:
                self.response.out.write("You are not an administrator for this site. Access denied.")
                return
        
            code = self.request.get('code', None)
            testid = self.request.get('testid', None)
            
            tests = cache.get("tests")
            if tests:
                test = None
                for curtest in tests:
                    if curtest.testid == testid:
                        test = curtest
                
            else:
                q = db.GqlQuery("SELECT * FROM Test WHERE testid = :1", testid)
                test = q.fetch(1)

                if len(test) > 0: test = test[0]
                else: test = None
            
            if test:
                if test.owner != session['me']['id']:
                    self.response.out.write("You are not the test owner of this test. Access denied.")
                    return
                
                test.delete()
                logging.info("Deleted the psychological test: " + testid)
                
            self.redirect('/admin?code=' + code)
        
class PostHandler(webapp2.RequestHandler):    
    def post(self):
        session = sessionmanager.getsession(self)
        
        if session:
            roles = session['roles']
            if not 'administrator' in roles:
                self.response.out.write("You are not an administrator for this site. Access denied.")
                return
        
            code = self.request.get('code', None)
            testid = self.request.get('testid', None)
            
            testname = self.request.get('testname', None)
            description = self.request.get('testdescription', None)
            startdate = self.request.get('teststartdate', None)
            enddate = self.request.get('testenddate', None)
            try:
                testfilename = self.request.POST['testfile'].filename
                testfile = self.request.get('testfile', None)
            except:
                testfilename = None
                testfile = None

            if testid == None:
                testid = str(datetime.datetime.now()) + " " + session['me']['id']
                test = obj_test.Test(testid=testid, name=testname)
            else:
                tests = cache.get("tests")
                if tests:
                    test = None
                    for curtest in tests:
                        if curtest.testid == testid:
                            test = curtest
                    
                else:
                    q = db.GqlQuery("SELECT * FROM Test WHERE testid = :1", testid)
                    test = q.fetch(1)
    
                    if len(test) > 0: test = test[0]
                    else: test = None

                if not test:
                    testid = str(datetime.datetime.now()) + " " + session['me']['id']
                    test = obj_test.Test(testid=testid, name=testname)
                else:
                    test = test[0]
                    if test.owner != session['me']['id']:
                        self.response.out.write("You are not the test owner of this test. Access denied.")
                        return

            test.owner = session['me']['id']
            test.description = description
            day, month, year = startdate.split("/")
            test.startdate = datetime.date(int(year), int(month), int(day))
            day, month, year = enddate.split("/")
            test.enddate = datetime.date(int(year), int(month), int(day))
            test.active = False
            if testfile != None:
                test.testfilename = testfilename
                test.testfile = db.Blob(testfile)
            test.put()
            cache.delete("tests")

            logging.info("Uploaded a new psychological test: " + testid)
            #self.redirect('/admin/edittest?testid=' + testid + '&code=' + code)
            self.redirect('/admin?code=' + code)

def renderPage(self, mode='new'):
        session = sessionmanager.getsession(self)
        
        if session:
            roles = session['roles']
        
            if not 'administrator' in roles:
                self.response.out.write("You are not an administrator for this site. Access denied.")
                return
            
            code = self.request.get('code', None)
            upload_url = '/admin/savetest?code=' + code
            
            test = None
            
            if mode == 'edit':
                testid = self.request.get('testid', None)
                q = db.GqlQuery("SELECT * FROM Test WHERE testid = :1", testid)
                tests = q.fetch(1)
                
                if len(tests) > 0:
                    test = tests[0]
            
            template_values = {
                'appId': conf.FBAPI_APP_ID,
                'token': session['access_token'], 
                'app': session['appid'],
                'conf': conf,
                'me': session['me'],
                'roles': roles,
                'test': test,
                'upload_url': upload_url,
                'isdesktop': session['isdesktop'],
                'header': 'viewcreatetest',
                'code': code }

            root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
            self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
            self.response.out.write(template.render(os.path.join(root, 'admin/templates/viewcreatetest.html'), template_values))
            self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))
        else:
            self.redirect(fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)))
            
class MainNewPage(webapp2.RequestHandler):
    def get(self):
        renderPage(self, 'new')

    def post(self):
        renderPage(self, 'new')

class MainEditPage(webapp2.RequestHandler):
    def get(self):
        renderPage(self, 'edit')

    def post(self):
        renderPage(self, 'edit')