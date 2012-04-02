import webapp2
import os, sys
import gaesessions
import pickle

from google.appengine.ext import db
from google.appengine.ext.webapp import template
from Cookie import SimpleCookie
from base64 import b64decode

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

def printdict(dictin, indent=0):
    strprint = '{\n'
    indentstr = ''
    for i in range(0, indent+1): indentstr += '  '
    
    for k, v in dictin.iteritems():
        strprint += indentstr + '\'' + str(k) + '\': '
        if type(v).__name__=='dict':
            strprint += printdict(v, indent+1) + '\n'
        elif type(v).__name__=='str' or type(v).__name__=='unicode':
            strprint += '\'' + v + '\'\n'
        else:
            #logging.info(type(v).__name__)
            strprint += str(v) + ',\n'
    
    indentstr = ''        
    for i in range(0, indent): indentstr += '  '        
    strprint = strprint[:-2] + '\n' + indentstr + '}'
    return strprint 

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        cookie = SimpleCookie(os.environ['HTTP_COOKIE'])
        printout = ''
        self.cookie_keys = cookie.keys()
        if not self.cookie_keys:
            self.response.out.write('No session yet')
            return
        self.cookie_keys.sort()
        data = ''.join(cookie[k].value for k in self.cookie_keys)
        printout += data + '\n\n\n'
        
        i = gaesessions.SIG_LEN + gaesessions.SID_LEN
        sig, b64pdump = data[:gaesessions.SIG_LEN], data[i:]
        printout += 'sig = ' + sig + '\n'
        b64pdump += "=" * ((4 - len(b64pdump) % 4) % 4)
        printout += 'len = ' + str(len(b64pdump)) + '\n'
        printout += 'padding = ' + str(((4 - len(b64pdump) % 4) % 4)) + '\n\n'
        
        try:
            pdump = b64decode(b64pdump)
            
            if pdump:
                printout += printdict(decode_data(pdump))
            else:
                printout += 'data is in memcache/db: load it on-demand'
        except:
            lens = len(b64pdump)
            lenx = lens - (lens % 4 if lens % 4 else 4)
            try:
                printout += b64decode(b64pdump[:lenx])
            except:
                printout += str(sys.exc_info())
        
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
