import webapp2

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = "text/plain"
        self.response.out.write('User-agent: *\n')
        self.response.out.write('Disallow:')
