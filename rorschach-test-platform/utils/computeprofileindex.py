import webapp2
import logging
import simplejson as json
import datetime
import libsna, conf, fbutils, sessionmanager
import urlparse, hashlib, gc

from obj import obj_index
from google.appengine.ext import db
from google.appengine.api import taskqueue
from google.appengine.runtime import DeadlineExceededError
from myexceptions import network_big
from google.appengine.api import memcache

conf = conf.Config()
cache = memcache.Client()

def getLibSNA(self, session):
    uid = self.request.get('id', None)
    if uid == None: uid = self.request.get('uid', None)
    
    if uid: network = libsna.getusernetwork(uid)
    else: network = libsna.getusernetwork(uid)
    libSNA = libsna.SocialNetwork()
    
    lastMonth = datetime.datetime.today() - datetime.timedelta(30)
    if network.updated_time <  lastMonth or network.getnodes() == None or network.getedges() == None:
        logging.info("Reading network from Facebook.")
        nodes, edges = getNodesEdges(self, session)
        libSNA.loadGraph(nodes=nodes, edges=edges)

        h = hashlib.sha1()
        h.update("%s - %s" % (libSNA.graph.nodes(), libSNA.graph.edges()))
        
        network.networkhash = h.hexdigest()
        network.setnodes(str(nodes))
        network.setedges(str(edges))
        network.setleague(None)
        network.put()
    else:
        libSNA.loadGraph(nodes=network.getnodes(), edges=network.getedges())
    
    logging.info("nodes:%s" %libSNA.graph.number_of_nodes())
    
    datacache = {}
    datacache['networkhash'] = network.networkhash
    datacache['uid'] = uid
    libSNA.cache = datacache
        
    if network.getleague() == None:
        logging.info('Computation of network league sent to backend backend-indexes.')
        taskqueue.add(url='/networkleague', params={'id': uid,
                                                    'backend': True,
                                                    'code': self.request.get('code', None),
                                                    'access_token': session['access_token']},
                      queue_name='indexes-queue', method='POST', target='backend-indexes')
    
    return libSNA

def computeIndex(self, libSNA, indexname, backend, session, saveInDatastore=True):
    objreturn = {}
    uid = self.request.get('id', None)
    if uid == None: uid = self.request.get('uid', None)
    
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
        if curindex.name == indexname: index = curindex
    
    if index and libSNA.cache['networkhash'] == index.networkhash and not index.value == None:
        objreturn['error'] = False
        objreturn['msg'] = ('The (already) computed index for ' + indexname + ' is ' + conf.INDEX_TYPES[indexname] + '.') % index.value
        return objreturn
    
    del index
    gc.collect()
    
    try:
        description = conf.INDEXES[indexname]
        
        valid_indexes = []
        for index_name in conf.INDEXES.keys():
            valid_indexes.append(index_name)
        
        if not indexname in valid_indexes :
            objreturn['error'] = True
            objreturn['msg'] = 'The index name ' + indexname + ' is invalid.'
            objreturn['value'] = '' 
        else :
            libSNA.runMeasure(indexname, backend)
            libSNA.displayResults(indexname)
            value = libSNA.returnResults(indexname, 'value')
            nodes = libSNA.returnResults(indexname, 'nodes')
            edges = libSNA.returnResults(indexname, 'edges')

            objreturn['error'] = False
            objreturn['msg'] = ('The computed index for ' + indexname + ' is ' + conf.INDEX_TYPES[indexname] + '.') % value
            objreturn['value'] = (conf.INDEX_TYPES[indexname]) % value
            if edges != None: objreturn['edges'] = obj_index.bucketize(edges.values())
            if nodes != None: objreturn['nodes'] = obj_index.bucketize(nodes.values())
            
            if not conf.DEBUG:
                logging.info("posting to the wall")
                postResults(self, session,
                                 {'message': ('I have just computed my ' + indexname + ' sociological index, its value is ' + conf.INDEX_TYPES[indexname] + '!') % value,
                                  'caption': indexname.title() + ' is a sociological index computed on the information present in FB. ' + description + '.',
                                  'index': indexname,
                                  'name_graph': indexname.title(),
                                  'value': (conf.INDEX_TYPES[indexname]) % value})
            
            if saveInDatastore:
                index = obj_index.Index(uid = uid, name = indexname)
                index.updated_time = datetime.datetime.now()
                index.networkhash = libSNA.cache['networkhash']
            
                index.value = float(value)
                if not edges == None: index.set_edgevalues(edges)
                if not nodes == None: index.set_nodevalues(nodes)
                index.put()
                cache.delete("%s_indexes" % uid)

    except network_big.NetworkTooBigException as ex:
        logging.info('Computation of ' + indexname + ' sent to backend backend-indexes.')
        taskqueue.add(url='/computeprofileindex', params={'id': uid,
                                                          'code': self.request.get('code', None),
                                                          'index': indexname,
                                                          'backend': True,
                                                          'access_token': session['access_token']},
                      queue_name='indexes-queue', method='POST', target='backend-indexes')
        objreturn['error'] = False
        objreturn['msg'] = 'You have ' + str(ex.value) + ' contacts in your network. The index computation is quite onerous, it will be executed background. Check in few minutes to see your computed value.'
        objreturn['value'] = ''
    except DeadlineExceededError as ex:
        if not backend:
            logging.info('Computation of ' + indexname + ' sent to backend backend-indexes.')
            taskqueue.add(url='/computeprofileindex', params={'id': uid,
                                                              'code': self.request.get('code', None),
                                                              'index': indexname,
                                                              'backend': True,
                                                              'access_token': session['access_token']},
                          queue_name='indexes-queue', method='POST', target='backend-indexes')
            objreturn['error'] = False
            objreturn['msg'] = 'The computation of this index took longer than expected, it will be executed background. Check in few minutes to see your computed value.'
            objreturn['value'] = ''
    
    return objreturn

def base_url(self):
    url = urlparse.urlparse(self.request.url)
    baseurl = ''
    if url.port == None:
        baseurl = "%s://%s/" % (url.scheme, url.hostname)
    else:
        baseurl = "%s://%s:%s/" % (url.scheme, url.hostname, url.port)
    return baseurl

def getNodesEdges(self, session):
    result = fbutils.fql(
        "SELECT uid2 FROM friend WHERE uid1 = me()",
        session['access_token'])
    nodes = []
    edges = []

    #for node in result:
    #    nodes.append(node['uid2'])
    #
    #result = fbutils.fql(
    #    "SELECT uid1, uid2 FROM friend WHERE " +
    #    "uid1 IN (SELECT uid2 FROM friend WHERE uid1 = me()) AND " +
    #    "uid2 IN (SELECT uid1 FROM friend WHERE uid2 = me())",
    #    session['access_token']);
    #
    #if 'error_code' in result and result['error_code'] > 0:
    #    logging.warning("Error during Facebook call: " + result['error_msg'])
    #else:
    #    for edge in result:
    #        edges.append([edge['uid1'], edge['uid2']])
    
    for node in result:
        nodes.append(node['uid2'])
        result = fbutils.fb_call('me/mutualfriends/' + node['uid2'], {'access_token' : session['access_token']})
        
        if 'data' in result:
            for curedge in result['data']:
                edges.append([node['uid2'], curedge['id']])
        
    
    return nodes, edges

def postResults(self, session, params):
    uid = self.request.get('id', None)
    if uid == None: uid = self.request.get('uid', None)
    
    try:
        #result = fbutils.fb_call("me/feed",
        #        {'access_token' : session['access_token'],
        #         'message': params['message'],
        #         'name': 'Rorschach test platform',
        #         'caption': params['caption'],
        #         'picture': 'http://rorschach-test-platform.appspot.com/smallgraph/' + uid + '/' + params['index'],
        #         'link': 'http://apps.facebook.com/' + conf.APP_NAMESPACE + '/'},
        #         method='POST')
        #logging.info('http://rorschach-test-platform.appspot.com/smallgraph/' + uid + '/' + params['index'])
        #if not 'id' in result: logging.error("Unable to post to the user wall: " + str(result))
        
        baseurl = base_url(self)
        baseurl = baseurl.replace('backend-indexes.', '')
        result = fbutils.fb_call("me/" + conf.APP_NAMESPACE + ":compute",
                {'access_token': session['access_token'],
                 'image': baseurl + 'smallgraph/' + uid + '/' + params['index'],
                 'sociological_index': baseurl + 'index/' + uid + '/' + params['index']},
                method='POST')
        if not 'id' in result: logging.error("Unable to execute OpenGraph action compute: " + str(result))
    except:
        logging.error("Unable to post to user profile or to OpenGraph the index computation.")

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        objreturn = {}
        session = {}
        libSNA = None
        
        backend = self.request.get('backend', False)
        indexname = self.request.get('index', None)
        index_group = self.request.get('indexgroup', None)
        
        uid = self.request.get('id', None)
        if uid == None: uid = self.request.get('uid', None)
        
        if backend: session['access_token'] = self.request.get('access_token', '') 
        else: session = sessionmanager.getsession(self, access_token=self.request.get('access_token', None))
        
        if not indexname == None or not index_group == None:
            libSNA = getLibSNA(self, session)
        else:
            objreturn['error'] = False
            objreturn['msg'] = 'Wrong parameters.'
            objreturn['value'] = ''
        
        if not indexname == None:
            objreturn = computeIndex(self, libSNA, indexname, backend, session)
        elif not index_group == None:
            for index_grp in conf.INDEX_GROUPS:
                if index_group == '_all' or index_grp['name'] == index_group:
                    for indexname in index_grp['indexes']:
                        if 'indexes' in objreturn: objreturn['indexes'] = objreturn['indexes'] + ',' + indexname
                        else: objreturn['indexes'] = indexname
                        
                        #objreturn[indexname] = computeIndex(self, libSNA, indexname, backend, session)
                        logging.info('Computation of ' + indexname + ' sent to backend backend-indexes.')
                        taskqueue.add(url='/computeprofileindex', params={'id': uid,
                                                                          'code': self.request.get('code', None),
                                                                          'index': indexname,
                                                                          'backend': True,
                                                                          'access_token': session['access_token']},
                                      queue_name='indexes-queue', method='POST', target='backend-indexes')
                        
                        objreturn[indexname] = {}
                        objreturn[indexname]['error'] = False
                        objreturn[indexname]['msg'] = 'The computation of this index will be executed background. Check in few minutes to see your computed value.'
                        objreturn['value'] = ''
                
        self.response.out.write(json.dumps(objreturn))

    def get(self):
        self.renderPage()

    def post(self):
        self.renderPage()
    