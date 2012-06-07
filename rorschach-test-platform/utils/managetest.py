from __future__ import with_statement
import logging
from obj import obj_test

from google.appengine.ext.webapp import blobstore_handlers

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    #from __future__ import with_statement
    #from google.appengine.api import files# Create the file
    #
    #file_name = files.blobstore.create(mime_type='application/octet-stream')
    #with files.open(file_name, 'a') as f:
    #    f.write('data')
    #
    #files.finalize(file_name)
    #blob_key = files.blobstore.get_blob_key(file_name)
    
    def post(self):
        #try:
        if True:
            code = self.request.get('code', None)
            testname = self.request.get('testname', None)
            
            testdata = { 'testkey' : 'testvalue' }

            test = obj_test.Test(name=testname)
            test.setObjTest(str(testdata))
            test.active = False
            test.put()

            logging.info("Uploaded a new psychological test: " + testname)
            self.redirect('/admin?code=' + code)

        #except:
        #    self.redirect('/admin?code=' + code)
