import pickle
import StringIO

from utils import conf
from google.appengine.ext import db

conf = conf.Config()

class TestResults(db.Model):
    """Models a psychological test result"""
    testid = db.StringProperty(required=True)
    keys = db.StringListProperty()
    values = db.BlobProperty()
    
    def loadvalues(self, subject, valfile):
        if not self.keys: return
        
        vals = self.getvalues()
        if not vals: vals = {}
        if not str(subject) in vals.keys(): vals[str(subject)] = []
        
        dictvals = {}
        readbuffer = StringIO.StringIO(valfile)
        row1 = readbuffer.read().split(',')
        row2 = readbuffer.read().split(',')
        for i in range(0, len(row1)):
            dictvals[row1[i]] = row2[i]
        
        for key in self.keys:
            if key in dictvals: vals[str(subject)].append(dictvals[key])
            else: vals[str(subject)].append('undefined')
                
        self.setvalues(vals)

    def setvalues(self, values):
        self.values =  db.Blob(pickle.dumps(values))
        
    def getvalues(self):
        if not self.values: return None
        return pickle.loads(self.values)
    
    def stroutput(self):
        return "Test results with:\n \
                testid = " + (self.testid or '<null>') + "\n \
                keys = " + (self.keys or '<null>') + "\n \
                values = " + (self.getvalues or '<null>') + "\n"