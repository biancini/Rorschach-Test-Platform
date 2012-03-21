import webapp2
import os

from google.appengine.ext.webapp import template
from utils import conf

conf = conf.Config()

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        template_values = { 'conf': conf }
        
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        self.response.out.write(template.render(os.path.join(root, 'pages/templates/pagetab.html'), template_values))

    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
