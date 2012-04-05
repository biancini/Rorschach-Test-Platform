import webapp2
import os.path, re

from utils import fbutils, conf, sessionmanager
from google.appengine.ext import db
from google.appengine.ext.webapp import template

conf = conf.Config()

numeric_test = re.compile("^\d+$")
def getattribute(value, arg):
    """Gets an attribute of an object dynamically from a string name"""

    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, 'has_key') and value.has_key(arg):
        return value[arg]
    elif numeric_test.match(str(arg)) and len(value) > int(arg):
        return value[int(arg)]
    else:
        return None
    
def hasattribute(value, arg):
    return hasattr(value, str(arg))

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        session = sessionmanager.getsession(self)
        
        if session:
            indexes = {}
            q = db.GqlQuery("SELECT * FROM Index " +
                        "WHERE uid = :1 " +
                        "ORDER BY updated_time DESC",
                        session['me']['id'])
            for index in q:            
                if not index.networkhash == None and \
                   not index.value == None:
                    indexes[index.name] = (conf.INDEX_TYPES[index.name]) % index.value
                    
            computed_groups = {}
            for group in conf.INDEX_GROUPS:
                comp = 0
                for index in group['indexes']:
                    if index in indexes:
                        comp += 1
                computed_groups[group['name']] = comp
            
            template_values = {
                'appId': conf.FBAPI_APP_ID,
                'token': session['access_token'], 
                'app': session['appid'],
                'conf': conf,
                'me': session['me'],
                'roles': session['roles'],
                'computedindexes': indexes,
                'numindexes': len(conf.INDEXES),
                'index_groups': conf.INDEX_GROUPS,
                'computed_groups': computed_groups, 
                'index_names': conf.INDEXES,
                'isdesktop': session['isdesktop'],
                'header': '',
                'code': self.request.get('code', None) }
            
            root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
            self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
            self.response.out.write(template.render(os.path.join(root, 'pages/templates/profile.html'), template_values))
            self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))
        else:
            self.redirect(fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)))

    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
