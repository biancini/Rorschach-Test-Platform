import webapp2
import cleanup_sessions, update_tree_values

class MainPage(webapp2.RequestHandler):
    def renderPage(self, scriptname):
        eval(scriptname + '.run()')
        self.response.out.write("end")

    def get(self, scriptname):
        self.renderPage(scriptname)

    def post(self, scriptname):
        self.renderPage(scriptname)
