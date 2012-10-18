from google.appengine.ext import db

class User(db.Model):
    """Models a user to the application"""
    uid = db.StringProperty(required=True)
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    link = db.StringProperty()
    username = db.StringProperty()
    updated_time = db.DateTimeProperty(auto_now_add=True)
    admin = db.BooleanProperty(default=False)
    tech = db.BooleanProperty(default=False)
    
    def stroutput(self):
        return "User element with:\n \
                uid = " + (self.uid or '<null>') + "\n \
                first_name = " + (self.first_name or '<null>') + "\n \
                last_name = " + (self.last_name or '<null>') + "\n \
                link = " + (self.link or '<null>') + "\n \
                username = " + (self.username or '<null>') + "\n \
                updated_time = " + str(self.updated_time or '<null>') + "\n \
                admin = " + str(self.admin) + "\n \
                tech = " + str(self.tech) + "\n"

