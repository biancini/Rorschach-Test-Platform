import zlib
from google.appengine.ext import db
from utils import conf
from numpy import inf

conf = conf.Config()

def bucketize(values, numbuckets=100):
    buckets = [0]*numbuckets
    minvalue = float(min(values))
    maxvalue = float(max(values))
    bucket_width = (maxvalue - minvalue) / (numbuckets - 1)

    for value in values:
        bucketid = int((value - minvalue) / (bucket_width or 1))
        buckets[max(min(bucketid, numbuckets-1),0)] += 1
    
    retbucket = []
    for i in range(0, numbuckets):
        retbucket.append([minvalue+(bucket_width*i), buckets[i]])
    
    return retbucket

class Index(db.Model):
    """Models a FB index for the user"""
    uid = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    updated_time = db.DateTimeProperty(auto_now_add=True)
    
    networkhash = db.StringProperty()
    value = db.FloatProperty()
    nodevalues = db.BlobProperty()
    edgevalues = db.BlobProperty()
    
    def set_nodevalues(self, value):
        if not value == None:
            value = bucketize(value.values())
            compressed = zlib.compress(str(value))
            self.nodevalues = db.Blob(compressed)
        else:
            self.nodevalues = None
    
    def set_edgevalues(self, value):
        if not value == None:
            value = bucketize(value.values())
            compressed = zlib.compress(str(value))
            self.edgevalues = db.Blob(compressed)
        else:
            self.edgevalues = None
    
    def get_nodevalues(self):
        compressed = self.nodevalues
        if compressed == None: return None
        value = zlib.decompress(compressed)
        return eval(value)
    
    def get_edgevalues(self):
        compressed = self.edgevalues
        if compressed == None: return None
        value = zlib.decompress(compressed)
        return eval(value)

    def stroutput(self):
        str_ret  = 'Index element with:\n'
        
        str_ret += 'uid = ' + (self.uid or '<null>') + '\n'
        str_ret += 'name = ' + (self.name or '<null>') + '\n'
        str_ret += 'updated_time = ' + str(self.updated_time or '<null>') + '\n'
        
        str_ret += 'networkhash = ' + (self.networkhash or '<null>') + '\n'
        str_ret += 'value = ' + str(self.value or '<null>') + '\n'
        str_ret += 'nodevalues = ' + str(self.get_nodevalues() or '<null>') + '\n'
        str_ret += 'edgevalues = ' + str(self.get_edgevalues() or '<null>') + '\n'
        
        return str_ret
