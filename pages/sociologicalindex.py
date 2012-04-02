import webapp2
import os
import json
import numpy as np

from google.appengine.ext import db
from google.appengine.ext.webapp import template
from utils import fbutils, conf, sessionmanager

conf = conf.Config()

class MainPage(webapp2.RequestHandler):
    def setcentiles(self, values):
        if values == None: return None
        
        for i in range(0, len(values)):
            values[i][0] = i+1
            
        return values
    
    def getgaussian(self, values):
        if values == None: return None
        
        moltiplicand = 0
        zeroes = 0
        vals = []
        for value in values:
            if value[1] == 0: zeroes += 1
            else: moltiplicand += value[1]
            
            for i in range(value[1]):
                vals.append(value[0])
        
        moltiplicand = moltiplicand + zeroes * moltiplicand / (len(values) - zeroes)
        sigma = np.std(vals)
        mu = np.mean(vals)
        
        valgauss = []
        for j in range(len(values)):
            newgauss = 1/(sigma * np.sqrt(2 * np.pi)) * np.exp(- (values[j][0] - mu)**2 / (2 * sigma**2))
            newgauss *= moltiplicand
            valgauss.append(newgauss)
        
        rowData = []    
        for j in range(len(values)):
            rowData.append([str(j+1), values[j][1], valgauss[j]])
    
        return rowData
    
    def mergevalues(self, values1, values2):
        values = []
        
        for i in range(0, len(values1)):
            values.append([i+1, values1[i][1], values2[i][1]])
            
        return values
    
    def mergevaluesG(self, values1, values2):
        values = []
        
        for i in range(0, len(values1)):
            values.append([str(i+1), values1[i][1], values1[i][2], values2[i][1], values2[i][2]])
            
        return values
    
    def postPage(self, uid, indexname):
        frienduid = self.request.get('frienduid', None)
        
        myvalues = self.request.get('myvalues', None)
        if myvalues != None: myvalues = eval(myvalues)
        myvaluesG = self.request.get('myvaluesG', None)
        if myvaluesG != None: myvaluesG = eval(myvaluesG)
        
        session = sessionmanager.getsession(self)
        try:
            if session['me']['id'] != uid:
                session.terminate()
                session = None
        except:
            session.terminate()
            session = None
            
        action = self.request.get('action', None)
        if session and action == 'getFriendValues':
            objreturn = {}
            q = db.GqlQuery("SELECT * FROM Index " +
                        "WHERE uid = :1 AND name = :2 " +
                        "ORDER BY updated_time DESC",
                        frienduid,
                        indexname)
            indexes = q.fetch(1)

            if not len(indexes) == 0:
                index = indexes[0]
            
                objreturn['value'] = index.value
                newvalues = self.setcentiles(index.get_nodevalues())
                if newvalues != None: objreturn['nodevalues'] = str(self.mergevalues(myvalues, newvalues))
                else: objreturn['nodevalues'] = str(newvalues)
                newgaussian = self.getgaussian(newvalues)
                if newgaussian != None: objreturn['nodegaussian'] = str(self.mergevaluesG(myvaluesG, newgaussian))
                else: objreturn['nodegaussian'] = str(newgaussian)
                
                newvalues = self.setcentiles(index.get_edgevalues())
                if newvalues != None: objreturn['edgevalues'] = str(self.mergevalues(myvalues, newvalues))
                else: objreturn['edgevalues'] = str(newvalues)
                newgaussian = self.getgaussian(newvalues)
                if newgaussian != None: objreturn['edgegaussian'] = str(self.mergevaluesG(myvaluesG, newgaussian))
                else: objreturn['edgegaussian'] = str(newgaussian)
            else:
                objreturn['value'] = None
            
                
            self.response.out.write(json.dumps(objreturn))
        else:
            self.response.out.write("Error, session invalid or invalid action.")
        
    def renderPage(self, uid, indexname):
        code = self.request.get('code', None)
        index = None
        
        value = None
        nodevalues = None
        edgevalues = None
        nodegaussian = None
        edgegaussian = None
        
        session = sessionmanager.getsession(self)
        try:
            if session['me']['id'] != uid: code = None
        except: code = None
                        
        q = db.GqlQuery("SELECT * FROM Index " +
                        "WHERE uid = :1 AND name = :2 " +
                        "ORDER BY updated_time DESC",
                        uid,
                        indexname)
        indexes = q.fetch(1)

        if not len(indexes) == 0:
            index = indexes[0]
            
            value = index.value
            nodevalues = self.setcentiles(index.get_nodevalues())
            edgevalues = self.setcentiles(index.get_edgevalues())
            nodegaussian = self.getgaussian(nodevalues)
            edgegaussian = self.getgaussian(edgevalues)
            
        if session == None:
            app_friends = None
        else:
            app_friends = fbutils.fql("SELECT uid, name, is_app_user " +
                                      "FROM user " +
                                      "WHERE uid IN (SELECT uid2 FROM friend WHERE uid1 = me()) AND is_app_user = 1 " +
                                      "ORDER BY name", session['access_token'])
        
        template_values = {
            'conf': conf,
            'indexname': indexname,
            'description': conf.INDEXES[indexname],
            'uid': uid,
            'index': index,
            'nodevalues': nodevalues,
            'edgevalues': edgevalues,
            'nodegaussian': nodegaussian,
            'edgegaussian': edgegaussian,
            'value': value,
            'friends': app_friends,
            'isdesktop': session and session['isdesktop'] or False,
            'header': 'sociologicalindex',
            'code': code }
        
        root = os.path.normpath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        self.response.out.write(template.render(os.path.join(root, 'templates/_header.html'), template_values))
        self.response.out.write(template.render(os.path.join(root, 'pages/templates/sociologicalindex.html'), template_values))
        self.response.out.write(template.render(os.path.join(root, 'templates/_footer.html'), template_values))

    def get(self, uid, index):
        self.renderPage(uid, index)

    def post(self, uid, index):
        self.postPage(uid, index)
