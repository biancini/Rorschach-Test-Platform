import webapp2
import numpy as np

from google.appengine.api import urlfetch
from google.appengine.ext import db
from utils import conf
from google.appengine.api import memcache

conf = conf.Config()
cache = memcache.Client()

def smallgraph_image(nodevalues, edgevalues):
    if nodevalues != None:
        imagegraph  = 'https://chart.googleapis.com/chart?cht=s&chs=100x100&chm=o,,0,5,5&chd=t:'
        str1 = ''
        str2 = ''
        
        logvalues = []
        for bucket,value in nodevalues:
            if value > 0:
                logvalues.append(value)
        
        minvalue = min(logvalues)
        maxvalue = max(logvalues)
        values = []
        #10 - 27028
        
        for bucket,value in nodevalues:
            val = float(value)
            if val > 0:
                val = (np.log(val)-np.log(minvalue))/(np.log(maxvalue)-np.log(minvalue))
                values.append(val)
                str1 += str(bucket) + ','
        
        maxvalue = max(values)
        for val in values:
            str2 += str((val/maxvalue)*100) + ','
        
        imagegraph += str1[0:-1] + '|' + str2[0:-1]
            
    elif edgevalues != None:
        imagegraph  = 'https://chart.googleapis.com/chart?cht=s&chs=100x100&chm=o,,0,5,5&chd=t:'
        str1 = ''
        str2 = ''
        
        logvalues = []
        for bucket,value in edgevalues:
            if value > 0:
                logvalues.append(value)
        
        minvalue = min(logvalues)
        maxvalue = max(logvalues)
        values = []
        #10 - 27028
        
        for bucket,value in edgevalues:
            val = float(value)
            if val > 0:
                val = (np.log(val)-np.log(minvalue))/(np.log(maxvalue)-np.log(minvalue))
                values.append(val)
                str1 += str(bucket) + ','
        
        maxvalue = max(values)
        for val in values:
            str2 += str((val/maxvalue)*100) + ','
        
        imagegraph += str1[0:-1] + '|' + str2[0:-1]
    else:
        imagegraph = 'http://rorschach-test-platform.appspot.com/static/images/macchie.jpg'
        
    return imagegraph

class MainPage(webapp2.RequestHandler):
    def setcentiles(self, values):
        if values == None: return None
        
        for i in range(0, len(values)):
            values[i][0] = i+1
            
        return values
        
    def renderPage(self, uid, indexname):
        index = None
        
        nodevalues = None
        edgevalues = None
        
        indexes = cache.get("%s_indexes" % uid)
        if indexes == None:
            indexes = {}
            q = db.GqlQuery("SELECT * FROM Index " +
                            "WHERE uid = :1 " +
                            "ORDER BY updated_time DESC",
                            uid)
        
            for index in q:            
                if not index.networkhash == None and \
                not index.value == None and \
                not index.name in indexes.keys():
                    indexes[index.name] = index
                    
            cache.add("%s_indexes" % uid, indexes, 60*60)
        
        index = None
        for curindex in indexes.values():
            if curindex.name == indexname:
                index = curindex

        if index:
            nodevalues = self.setcentiles(index.get_nodevalues())
            edgevalues = self.setcentiles(index.get_edgevalues())

        
        imagegraph = smallgraph_image(nodevalues, edgevalues)
        result = urlfetch.fetch(imagegraph, deadline=10)
        
        self.response.headers['Content-Type'] = "image/png"
        self.response.out.write(result.content)

    def get(self, uid, index):
        self.renderPage(uid, index)

    def post(self, uid, index):
        self.renderPage(uid, index)
