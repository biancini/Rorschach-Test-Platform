from utils import conf
import os
import datetime

from gaesessions import SessionMiddleware
from google.appengine.ext.webapp import template

# suggestion: generate your own random key using os.urandom(64)
# WARNING: Make sure you run os.urandom(64) OFFLINE and copy/paste the output to
# this file.  If you use os.urandom() to *dynamically* generate your key at
# runtime then any existing sessions will become junk every time you start,
# deploy, or update your app!
conf = conf.Config()

#apptrace_URL_PATTERNS  = ['^/index/(.+)']
#apptrace_TRACE_MODULES = ['obj/obj_index.py', 'utils/computeprofileindex.py', 'pages/sociologicalindex.py']

def webapp_add_wsgi_middleware(app):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'utils.settings'
    template.register_template_library('templatetags.formats')
    template.register_template_library('templatetags.dictionary')
    
    #from apptrace.middleware import apptrace_middleware
    #app = apptrace_middleware(app)
    app = SessionMiddleware(app, cookie_key=conf.COOKIE_KEY, lifetime=datetime.timedelta(1), no_datastore=True)
    return app