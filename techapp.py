import webapp2

from utils import conf
from cron import cronscript
from admin import tech, dumpcookie, vieweditnetwork, vieweditindex

conf = conf.Config()

routes = []

# Adding routes for pages rendering screens to the user
routes.append(('/tech', tech.MainPage))
routes.append(('/tech/dumpcookie', dumpcookie.MainPage))

# Adding routes for technical pages for perform operations
routes.append(('/tech/cron/(.+)', cronscript.MainPage))

# Adding routes for admin pages
routes.append(('/tech/viewnetwork', vieweditnetwork.MainEditPage))
routes.append(('/tech/savenetwork', vieweditnetwork.PostHandler))
routes.append(('/tech/viewindex', vieweditindex.MainEditPage))
routes.append(('/tech/saveindex', vieweditindex.PostHandler))

app = webapp2.WSGIApplication(routes, debug=conf.DEBUG)
