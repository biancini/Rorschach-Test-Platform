import webapp2
import os
import pickle

from google.appengine.ext import db
from google.appengine.ext.webapp import template
from Cookie import SimpleCookie

from utils import conf, sessionmanager

conf = conf.Config()

def decode_data(pdump):
    """Returns a data dictionary after decoding it from "pickled+" form."""
    try:
        eP, eO = pickle.loads(pdump)
        for k, v in eP.iteritems():
            eO[k] = db.model_from_protobuf(v)
    except Exception:
        eO = {}
    return eO

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        cookie = SimpleCookie(os.environ['HTTP_COOKIE'])
        printout = ''
        self.cookie_keys = cookie.keys()
        if not self.cookie_keys:
            self.response.out.write('No session yet')
            return
        self.cookie_keys.sort()
        
        
        for k in self.cookie_keys:
            printout += '%s = %s\n' % (k, cookie[k].value)
            
        session = sessionmanager.getsession(self)
        
        template_values = {
                'appId': conf.FBAPI_APP_ID,
                'token': session['access_token'], 
                'app': session['appid'],
                'conf': conf,
                'me': session['me'],
                'cookie': printout,
                'isdesktop': session and session['isdesktop'] or False,
                'header': '',
                'code': self.request.get('code', None) }
        
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
        self.response.out.write(template.render(os.path.join(root, 'admin/templates/dumpcookie.html'), template_values))
        self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))

    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
