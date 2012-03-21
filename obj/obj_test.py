from utils import conf
from google.appengine.ext import db

conf = conf.Config()

class Test(db.Model):
    """Models a psychological test"""
    testid = db.StringProperty(required=True)
    name = db.StringProperty(required=True)
    owner = db.StringProperty()
    description = db.StringProperty()
    startdate = db.DateProperty()
    enddate = db.DateProperty()
    active = db.BooleanProperty(default=False)
    testfilename = db.StringProperty()
    testfile = db.BlobProperty()
    
    def stroutput(self):
        return "Test element with:\n \
                testid = " + (self.testid or '<null>') + "\n \
                name = " + (self.name or '<null>') + "\n \
                owner = " + (self.owner or '<null>') + "\n \
                description = " + (self.description or '<null>') + "\n \
                startdate = " + str(self.startdate or '<null>') + "\n \
                enddate = " + str(self.enddate or '<null>') + "\n \
                active = " + str(self.active or '<null>') + "\n \
                testfilename = " + str(self.testfilename or '<null>') + "\
                testfile = " + (self.testfile and 'File of ' + self.testfile.__sizeof__() + 'bytes.'  or '<null>') + "\n"
