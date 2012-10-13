import webapp2

from pages import home, robots, profile, sociologicalindex, network
from pages import pagetab, smallgraph, postwall
from admin import admin, viewcreatetest, viewtestresults, vieweditnetwork, vieweditindex, downloadnetwork, downloadindex
from utils import conf, storenetwork, computeprofileindex, networkleague, printnetwork
from opensesame import access, config, indexes, testfile

conf = conf.Config()

routes = []

# Adding routes for pages rendering screens to the user
routes.append(('/', home.MainPage));
routes.append(('/robots.txt', robots.MainPage))
routes.append(('/profile', profile.MainPage))
routes.append(('/profile/(\w+)', profile.MainPage))
routes.append(('/pagetab', pagetab.MainPage))
routes.append(('/index/(\w+)/(\w+)', sociologicalindex.MainPage))
routes.append(('/network/(\w+)', network.MainPage))
routes.append(('/smallgraph/(\w+)/(\w+)', smallgraph.MainPage))

# Adding routes for admin pages rendering screens to test administrators
routes.append(('/admin', admin.MainPage))
routes.append(('/admin/newtest', viewcreatetest.MainNewPage))
routes.append(('/admin/edittest', viewcreatetest.MainEditPage))
routes.append(('/admin/savetest', viewcreatetest.PostHandler))
routes.append(('/admin/deltest', viewcreatetest.DelHandler))
routes.append(('/admin/activatetest', viewcreatetest.ActiveHandler))
routes.append(('/admin/viewnetwork', vieweditnetwork.MainViewPage))
routes.append(('/admin/savenetwork', vieweditnetwork.MainViewPage))
routes.append(('/admin/viewindex', vieweditindex.MainViewPage))
routes.append(('/admin/saveindex', vieweditindex.MainViewPage))
routes.append(('/admin/networks.(\w+)', downloadnetwork.MainPage))
routes.append(('/admin/indexes.(\w+)', downloadindex.MainPage))
routes.append(('/admin/testresults', viewtestresults.MainPage))

# Adding routes for OpenSesame plugin
routes.append(('/opensesame/access', access.MainPage))
routes.append(('/opensesame/config', config.MainPage))
routes.append(('/opensesame/indexes', indexes.MainPage))
routes.append(('/opensesame/testfile', testfile.MainPage))

# Adding routes for technical pages for perform operations
routes.append(('/storenetwork', storenetwork.MainPage))
routes.append(('/computeprofileindex', computeprofileindex.MainPage))
routes.append(('/networkleague', networkleague.MainPage))
routes.append(('/network.(\w+)', printnetwork.MainPage))
routes.append(('/postwall', postwall.MainPage))

app = webapp2.WSGIApplication(routes, debug=conf.DEBUG)
