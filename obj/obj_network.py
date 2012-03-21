import zlib
from google.appengine.ext import db
from utils import conf
from numpy import inf

conf = conf.Config()

class Network(db.Model):
    """Models a FB network for the user"""
    uid = db.StringProperty(required=True)
    updated_time = db.DateTimeProperty(auto_now_add=True)
    networkhash = db.StringProperty()
    
    nodes = db.BlobProperty()
    edges = db.BlobProperty()
    league = db.BlobProperty()
    
    def setnodes(self, value):
        if not value == None:
            compressed = zlib.compress(value)
            self.nodes = db.Blob(compressed)
        else:
            self.nodes = None
        
    def setedges(self, value):
        if not value == None:
            compressed = zlib.compress(value)
            self.edges = db.Blob(compressed)
        else:
            self.edges = None
    
    def setleague(self, value):
        if not value == None:
            compressed = zlib.compress(value)
            self.league = db.Blob(compressed)
        else:
            self.league = None
    
    def getnodes(self):
        if self.nodes == None: return None
        compressed = self.nodes
        value = zlib.decompress(compressed)
        return eval(value) 
    
    def getedges(self):
        if self.edges == None: return None
        compressed = self.edges
        value = zlib.decompress(compressed)
        return eval(value)
    
    def getleague(self):
        if self.league == None: return None
        compressed = self.league
        value = zlib.decompress(compressed)
        return eval(value)

    def stroutput(self):
        str_ret  = 'Network element with:\n'
        
        str_ret += 'uid = ' + (self.uid or '<null>') + '\n'
        str_ret += 'networkhash = ' + (self.networkhash or '<null>') + '\n'
        str_ret += 'updated_time = ' + str(self.updated_time or '<null>') + '\n'
        
        str_ret += 'nodes = ' + str(self.getnodes() or '<null>') + '\n'
        str_ret += 'edges = ' + str(self.getedges() or '<null>') + '\n'
        str_ret += 'league = ' + str(self.getleague() or '<null>') + '\n'
        
        return str_ret
