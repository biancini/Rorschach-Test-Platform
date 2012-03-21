import os
import webapp2

from utils import conf, sessionmanager, fbutils
from google.appengine.ext.webapp import template

conf = conf.Config()

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        session = sessionmanager.getsession(self, redirect_uri=fbutils.base_url(self)+'opensesame/access')
        
        if session:
            SERVER_ADDRESS = ('127.0.0.1', 33333)
            
            template_values = {
                'appId': conf.FBAPI_APP_ID,
                'token': session['access_token'],
                'app': session['appid'],
                'conf': conf,
                'me': session['me'],
                'roles': session['roles'],
                'isdesktop': session['isdesktop'],
                'header': ''}
            
            root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
            self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
            
            self.response.out.write('<header class="clearfix">')
            self.response.out.write('<p id="picture" style="background-image: url(/static/images/macchie.jpg); background-size: 64px 64px"></p>')
            self.response.out.write('<h1>Rorschach Test Platform authentication</h1>')
            self.response.out.write('</header>')
            
            self.response.out.write('<section id="normalsection" class="clearfix">')
            self.response.out.write('<h3>Associate OpenSesame with Rorschach Test Platform</h3>')
            self.response.out.write('<p>In order to use the OpenSesame plugin, you need to authenticate with Facebook and give grants to the Rorschach Test Platform application.</p>')
            self.response.out.write('<p>By clicking the button below you will create a temporary access token to be used by the OpenSesame plugin.<br/>')
            self.response.out.write('The access token created with this procedure will have a lifetime of two hours (as by Facebook standards) and so after two hours it will be automatically declared invalid.</p>') 
            self.response.out.write('<form action="http://%s:%s/" method="post" name="codeSubmit" id="codeSubmit">' % SERVER_ADDRESS )
            self.response.out.write('<input type="hidden" id="code" name="code" value="' + self.request.get('code', None) + '" />')
            self.response.out.write('<input type="hidden" id="access_token" name="access_token" value="' + session['access_token'] + '" />')
            self.response.out.write('<p class="button"><a href="#" class="facebook-button" onclick="$(\'#codeSubmit\').submit();">')
            self.response.out.write('<span class="plus">Save the access token</span></a></p>')
            self.response.out.write('</section>')
            
            self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))
        else:
            self.redirect(fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)+'opensesame/access'))
        
    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
