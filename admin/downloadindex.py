import webapp2
import datetime
import logging
import pickle
import base64

import gdata.apps.service
import gdata.docs.service
import gdata.spreadsheet.service

from utils import fbutils, conf, sessionmanager
from google.appengine.ext import db
from google.appengine.api import taskqueue

conf = conf.Config()

supported_extensions = [ 'xml', 'csv', 'xls' ]
supported_extensions_login = [ 'docs' ]

def get_spreadsheet_by_name(gspreadsheet, file_name):
    query = gdata.spreadsheet.service.DocumentQuery()
    query['title'] = file_name
    query['title-exact'] = 'true'
    feed = gspreadsheet.GetSpreadsheetsFeed(query=query)
    spreadsheet_id = feed.entry[0].id.text.rsplit('/',1)[1]
    feed = gspreadsheet.GetWorksheetsFeed(spreadsheet_id)
    worksheet_id = feed.entry[0].id.text.rsplit('/',1)[1]
    
    return spreadsheet_id, worksheet_id

def create_spreadsheet(access_token, file_name):
    gdocs = gdata.docs.service.DocsService(source=conf.GOOGLE_APP_NAME)
    gdocs.SetOAuthToken(access_token)
    
    archive_name = "Rorschach Test Platform"
    archive = None
    
    query =  gdata.docs.service.DocumentQuery(categories=['folder'], params={'showfolders': 'true'})
    resources = gdocs.Query(query.ToUri())
    for entry in resources.entry:
        if entry.title.text == archive_name: archive = entry
    if not archive: archive = gdocs.CreateFolder(title=archive_name)
    
    new_entry = gdata.GDataEntry()
    new_entry.title = gdata.atom.Title(text=file_name)
    category = gdocs._MakeKindCategory(gdata.docs.service.SPREADSHEET_LABEL)
    new_entry.category.append(category)
    created_entry = gdocs.Post(new_entry, '/feeds/documents/private/full/')
    gdocs.MoveIntoFolder(created_entry, archive)
    logging.info('Spreadsheet created online at: %s.' % created_entry.GetAlternateLink().href)
    
    return created_entry.GetAlternateLink().href

def initialize_spreadsheet(gspreadsheet, spreadsheet_id, worksheet_id, q):
    tot_num_rows = 0
    for index in q:
        tot_num_rows += len(index.get_nodevalues() or [])
        tot_num_rows += len(index.get_edgevalues() or [])
    
    # Worksheet for first page
    worksheet = gspreadsheet.GetWorksheetsFeed(spreadsheet_id, wksht_id=worksheet_id)
    worksheet.col_count.text = '2'
    worksheet.row_count.text = '5'
    gspreadsheet.UpdateWorksheet(worksheet)
    
    # Create the worksheet for edge list 
    worksheet = gspreadsheet.AddWorksheet("Index Data", 1 + tot_num_rows, 9, spreadsheet_id)
    worksheet = gspreadsheet.UpdateWorksheet(worksheet)
    index_worksheet_id = worksheet.id.text.rsplit('/',1)[1]
        
    logging.info('Worksheets created in spreadsheet')
    
    # Write the header for first page
    batchRequest = gdata.spreadsheet.SpreadsheetsCellsFeed()

    query = gdata.spreadsheet.service.CellQuery()
    query['min-col'] = '1'
    query['max-col'] = '2'
    query['min-row'] = '2'
    query['max-row'] = '4'
    query['return-empty'] = 'true'
    cells = gspreadsheet.GetCellsFeed(spreadsheet_id, wksht_id=worksheet_id, query=query)

    cellnum = 0
    
    for cellval in ["Title", "Rorschach Test Platform: indexes download",
                    "Creation Time", str(datetime.datetime.today()),
                    "Indexes number", str(q.count())]:
        cells.entry[cellnum].cell.inputValue = cellval
        batchRequest.AddUpdate(cells.entry[cellnum])
        cellnum += 1

    gspreadsheet.ExecuteBatch(batchRequest, cells.GetBatchLink().href)

    # Write the header row
    batchRequest = gdata.spreadsheet.SpreadsheetsCellsFeed()

    query = gdata.spreadsheet.service.CellQuery()
    query['min-col'] = '1'
    query['max-col'] = '9'
    query['min-row'] = '1'
    query['max-row'] = '1'
    query['return-empty'] = 'true'
    cells = gspreadsheet.GetCellsFeed(spreadsheet_id, wksht_id=index_worksheet_id, query=query)
    
    logging.info('Headers written for all worksheets in spreadsheet')
    
    cellnum = 0
    for cellval in ["User ID", "Name", "Updated Time", "Network Hash", "Index Value", "Node Bucket", "Node Value", "Edge Bucket", "Edge Value"]:
        cells.entry[cellnum].cell.inputValue = cellval
        batchRequest.AddUpdate(cells.entry[cellnum])
        cellnum += 1

    gspreadsheet.ExecuteBatch(batchRequest, cells.GetBatchLink().href)
    
    return index_worksheet_id
    
def populate_spreadsheet(gspreadsheet, spreadsheet_id, worksheet_id, q):
    rownum = 2
    for index in q:
        cellnum = 0
        query = gdata.spreadsheet.service.CellQuery()
        query['min-col'] = '1'
        query['max-col'] = '9'
        query['min-row'] = str(rownum)
        query['return-empty'] = 'true'
        
        if len((index.get_nodevalues() or [])) == 0 and len((index.get_edgevalues() or [])) == 0:
            query['max-row'] = str(rownum)
            
            batchRequest = gdata.spreadsheet.SpreadsheetsCellsFeed()
            cells = gspreadsheet.GetCellsFeed(spreadsheet_id, wksht_id=worksheet_id, query=query)
            
            for cellval in [str(index.uid), index.name, str(index.updated_time), index.networkhash,  str(index.value)]:
                cells.entry[cellnum].cell.inputValue = cellval
                batchRequest.AddUpdate(cells.entry[cellnum])
                cellnum += 1
            cellnum += 4
            rownum += 1
            
        if len((index.get_nodevalues() or [])) > 0:
            query['max-row'] = str(rownum + len((index.get_nodevalues() or [])) - 1)
            
            batchRequest = gdata.spreadsheet.SpreadsheetsCellsFeed()
            cells = gspreadsheet.GetCellsFeed(spreadsheet_id, wksht_id=worksheet_id, query=query)
            
            for nodevalue in (index.get_nodevalues() or []):
                for cellval in [str(index.uid), index.name, str(index.updated_time), index.networkhash,  str(index.value)]:
                    cells.entry[cellnum].cell.inputValue = cellval
                    batchRequest.AddUpdate(cells.entry[cellnum])
                    cellnum += 1
                
                for cellval in [str(nodevalue[0]), str(nodevalue[1])]:
                    cells.entry[cellnum].cell.inputValue = cellval
                    batchRequest.AddUpdate(cells.entry[cellnum])
                    cellnum += 1
                    
                cellnum += 2
                rownum += 1
                
                gspreadsheet.ExecuteBatch(batchRequest, cells.GetBatchLink().href)
                logging.info('Wrote index node values: %s rows' % (rownum - 2))
            
        if len((index.get_edgevalues() or [])) > 0:
            query['max-row'] = str(rownum + len((index.get_edgevalues() or [])) - 1)
            
            batchRequest = gdata.spreadsheet.SpreadsheetsCellsFeed()
            cells = gspreadsheet.GetCellsFeed(spreadsheet_id, wksht_id=worksheet_id, query=query)
            
            for edgevalue in (index.get_edgevalues() or []):
                for cellval in [str(index.uid), index.name, str(index.updated_time), index.networkhash,  str(index.value)]:
                    cells.entry[cellnum].cell.inputValue = cellval
                    batchRequest.AddUpdate(cells.entry[cellnum])
                    cellnum += 1
                
                cellnum += 2    
                
                for cellval in [str(edgevalue[0]), str(edgevalue[1])]:
                    cells.entry[cellnum].cell.inputValue = cellval
                    batchRequest.AddUpdate(cells.entry[cellnum])
                    cellnum += 1
                    
                rownum += 1
                
                gspreadsheet.ExecuteBatch(batchRequest, cells.GetBatchLink().href)
                logging.info('Wrote index edge values: %s rows' % (rownum - 2))

def renderPageLogin(self, extension, mode='admin'):
    backend = self.request.get('backend', False)
    session = {}
    
    if backend: session['access_token'] = self.request.get('access_token', '') 
    else:
        session = sessionmanager.getsession(self)
        if session:
            roles = session['roles']
    
            if mode == 'admin' and not 'administrator' in roles:
                self.response.out.write("You are not an administrator for this site. Access denied.")
                return
            elif not 'technician' in roles:
                self.response.out.write("You are not a technician for this site. Access denied.")
                return
        else:
            self.redirect(fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)))
        
    if extension in supported_extensions_login:
        if extension == 'docs':
            global serviceG
            global secret
            
            backend = self.request.get('backend', False)
            
            if backend:
                file_name = self.request.get('file_name', False)
                access_token = pickle.loads(base64.b64decode(self.request.get('google_access_token', '')))
                
                serviceG = gdata.apps.service.AppsService(source=conf.GOOGLE_APP_NAME)
                serviceG.SetOAuthInputParameters(signature_method=gdata.auth.OAuthSignatureMethod.HMAC_SHA1,
                                                consumer_key=conf.GOOGLE_CONSUMER_KEY,
                                                consumer_secret=conf.GOOGLE_CONSUMER_SECRET)
                
                serviceG.current_token = access_token
                serviceG.SetOAuthToken(access_token)
                
                q = db.GqlQuery("SELECT * FROM Index")
                gspreadsheet = gdata.spreadsheet.service.SpreadsheetsService()
                gspreadsheet.SetOAuthToken(access_token)
                
                spreadsheet_id, worksheet_id = get_spreadsheet_by_name(gspreadsheet, file_name)
                index_worksheet_id = initialize_spreadsheet(gspreadsheet, spreadsheet_id, worksheet_id, q)
                populate_spreadsheet(gspreadsheet, spreadsheet_id, index_worksheet_id, q)
            else:
                scopes = ['https://docs.google.com/feeds/', 'https://spreadsheets.google.com/feeds/']
                oauth_callback = fbutils.base_url(self) + mode + '/indexes.docs?code=' + self.request.get('code')
                autheticated = self.request.get('oauth_token', None)
    
                if not autheticated:
                    serviceG = gdata.apps.service.AppsService(source=conf.GOOGLE_APP_NAME)
                    serviceG.SetOAuthInputParameters(signature_method=gdata.auth.OAuthSignatureMethod.HMAC_SHA1,
                                                    consumer_key=conf.GOOGLE_CONSUMER_KEY,
                                                    consumer_secret=conf.GOOGLE_CONSUMER_SECRET)

                    request_token = serviceG.FetchOAuthRequestToken(scopes=scopes, oauth_callback=oauth_callback)
                    secret = request_token.secret
                    serviceG.SetOAuthToken(request_token)

                    google_auth_page_url = serviceG.GenerateOAuthAuthorizationURL()
                    self.redirect(google_auth_page_url) 
                else:
                    oauth_token = gdata.auth.OAuthTokenFromUrl(self.request.uri)
                    if oauth_token:
                        oauth_token.secret = secret
                        oauth_token.oauth_input_params = serviceG.GetOAuthInputParameters()
                        serviceG.SetOAuthToken(oauth_token)
                        
                        oauth_verifier = self.request.get('oauth_verifier', default_value='')
                        access_token = serviceG.UpgradeToOAuthAccessToken(oauth_verifier=oauth_verifier)
                        
                        if access_token:
                            serviceG.current_token = access_token
                            serviceG.SetOAuthToken(access_token)
                        else:
                            self.response.out.write("Error performing the OAuth authentication.")
                            return
                    else:
                        self.response.out.write("Error performing the OAuth authentication.")
                        return
                    
                    file_name = 'Computed indexes (%s)' % datetime.datetime.today()
                    spreadsheet_url = create_spreadsheet(access_token, file_name)
                    
                    taskqueue.add(url='/' + mode + '/indexes.docs',
                                  params={'code': self.request.get('code', None),
                                          'google_access_token': base64.b64encode(pickle.dumps(access_token)),
                                          'file_name': file_name,
                                          'backend': True,
                                          'access_token': session['access_token']},
                                  queue_name='gdocs-queue', method='POST', target='backend-indexes')
                    
                    self.redirect(spreadsheet_url)

def renderPage(self, extension, mode='admin'):
    backend = self.request.get('backend', False)
    session = {}
    
    if backend: session['access_token'] = self.request.get('access_token', '') 
    else:
        session = sessionmanager.getsession(self)
        if session:
            roles = session['roles']
    
            if mode == 'admin' and not 'administrator' in roles:
                self.response.out.write("You are not an administrator for this site. Access denied.")
                return
            elif not 'technician' in roles:
                self.response.out.write("You are not a technician for this site. Access denied.")
                return
        else:
            self.redirect(fbutils.oauth_login_url(self=self, next_url=fbutils.base_url(self)))
        
    if extension in supported_extensions:
        q = db.GqlQuery("SELECT * FROM Index")
        
        if extension == 'xml':
            self.response.headers['Content-Type'] = "text/xml"
            self.response.out.write('<indexes count="%s">\n' % q.count())
            
            for index in q:
                self.response.out.write('  <index uid="%s" name="%s" updated_time="%s" networkhash="%s">\n' % (index.uid, index.name, index.updated_time, index.networkhash))
                self.response.out.write('    <value value="%s" />' % index.value)
                self.response.out.write('    <nodevalues count="%s">\n' % len(index.get_nodevalues() or []))
                for nodevalue in (index.get_nodevalues() or []):
                    self.response.out.write('      <nodevalue bucket="%s" numnodes="%s" />\n' % (nodevalue[0], nodevalue[1]))
                self.response.out.write('    </nodevalues>\n')
                self.response.out.write('    <edgevalues count="%s">\n' % len(index.get_edgevalues() or []))
                for edgevalue in (index.get_edgevalues() or []):
                    self.response.out.write('      <edgevalue bucket="%s" numnodes="%s" />\n' % (edgevalue[0], edgevalue[1]))
                self.response.out.write('    </edgevalues>\n')
                self.response.out.write('  </index>\n\n')
                
            self.response.out.write('</indexes>')
                
        if extension == 'csv':
            self.response.headers['Content-Type'] = "text/csv"
            self.response.out.write('uid,name,updated_time,networkhash,value,nodebucket,nodevalue,edgebucket,edgevalue\n')
            
            for index in q:
                if len((index.get_nodevalues() or [])) == 0 and len((index.get_edgevalues() or [])) == 0:
                    self.response.out.write('%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (index.uid, index.name, index.updated_time, index.networkhash, index.value, '', '', '', '')) 
                for nodevalue in (index.get_nodevalues() or []):
                    self.response.out.write('%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (index.uid, index.name, index.updated_time, index.networkhash, index.value, nodevalue[0], nodevalue[1], '', ''))
                for edgevalue in (index.get_edgevalues() or []):
                    self.response.out.write('%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (index.uid, index.name, index.updated_time, index.networkhash, index.value, '', '', edgevalue[0], edgevalue[1]))
            
        if extension == 'xls':
            self.response.headers['Content-Type'] = "application/vnd.ms-excel"
            self.response.out.write('uid\tname\tupdated_time\tnetworkhash\tvalue\tnodebucket\tnodevalue\tedgebucket\tedgevalue\r\n')
            
            for index in q:
                if len((index.get_nodevalues() or [])) == 0 and len((index.get_edgevalues() or [])) == 0:
                    self.response.out.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\r\n' % (index.uid, index.name, index.updated_time, index.networkhash, index.value, '', '', '', '')) 
                for nodevalue in (index.get_nodevalues() or []):
                    self.response.out.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\r\n' % (index.uid, index.name, index.updated_time, index.networkhash, index.value, nodevalue[0], nodevalue[0], '', ''))
                for edgevalue in (index.get_edgevalues() or []):
                    self.response.out.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\r\n' % (index.uid, index.name, index.updated_time, index.networkhash, index.value, '', '', edgevalue[0], edgevalue[1]))
    else:
        self.response.out.write('Wrong format requested.')
            
class MainPage(webapp2.RequestHandler):
    def get(self, extension):
        if extension in supported_extensions_login: renderPageLogin(self, extension, 'admin')
        else: renderPage(self, extension, 'admin')

    def post(self, extension):
        if extension in supported_extensions_login: renderPageLogin(self, extension, 'admin')
        else: renderPage(self, extension, 'admin')
        