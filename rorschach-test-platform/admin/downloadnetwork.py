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
    tot_num_nodes = 0
    tot_num_edges = 0
    tot_num_leagues = 0
    for network in q:
        tot_num_nodes += len(network.getnodes() or [])
        tot_num_edges += len(network.getedges() or [])
        tot_num_leagues += len(network.getleague() or [])
        
    # Worksheet for first page
    worksheet = gspreadsheet.GetWorksheetsFeed(spreadsheet_id, wksht_id=worksheet_id)
    worksheet.col_count.text = '2'
    worksheet.row_count.text = '5'
    gspreadsheet.UpdateWorksheet(worksheet)
    
    # Create the worksheet for edge list 
    worksheet = gspreadsheet.AddWorksheet("Nodes List", 1 + tot_num_nodes, 4, spreadsheet_id)
    worksheet = gspreadsheet.UpdateWorksheet(worksheet)
    nodes_worksheet_id = worksheet.id.text.rsplit('/',1)[1]
    
    # Create the worksheet for edge list 
    worksheet = gspreadsheet.AddWorksheet("Edges List", 1 + tot_num_edges, 5, spreadsheet_id)
    worksheet = gspreadsheet.UpdateWorksheet(worksheet)
    edges_worksheet_id = worksheet.id.text.rsplit('/',1)[1]
    
    # Create the worksheet for networks league
    worksheet = gspreadsheet.AddWorksheet("Networks League", 1 + tot_num_leagues, 8, spreadsheet_id)
    worksheet = gspreadsheet.UpdateWorksheet(worksheet)
    leagues_worksheet_id = worksheet.id.text.rsplit('/',1)[1]
    
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
    
    for cellval in ["Title", "Rorschach Test Platform: networks download",
                    "Creation Time", str(datetime.datetime.today()),
                    "Networks number", str(q.count())]:
        cells.entry[cellnum].cell.inputValue = cellval
        batchRequest.AddUpdate(cells.entry[cellnum])
        cellnum += 1

    gspreadsheet.ExecuteBatch(batchRequest, cells.GetBatchLink().href)

    # Write the header row for nodes list
    batchRequest = gdata.spreadsheet.SpreadsheetsCellsFeed()

    query = gdata.spreadsheet.service.CellQuery()
    query['min-col'] = '1'
    query['max-col'] = '4'
    query['min-row'] = '1'
    query['max-row'] = '1'
    query['return-empty'] = 'true'
    cells = gspreadsheet.GetCellsFeed(spreadsheet_id, wksht_id=nodes_worksheet_id, query=query)

    cellnum = 0
    
    for cellval in ["User ID", "Updated Time", "Network Hash", "Node ID"]:
        cells.entry[cellnum].cell.inputValue = cellval
        batchRequest.AddUpdate(cells.entry[cellnum])
        cellnum += 1

    gspreadsheet.ExecuteBatch(batchRequest, cells.GetBatchLink().href)
    
    # Write the header row for edges list
    batchRequest = gdata.spreadsheet.SpreadsheetsCellsFeed()

    query = gdata.spreadsheet.service.CellQuery()
    query['min-col'] = '1'
    query['max-col'] = '5'
    query['min-row'] = '1'
    query['max-row'] = '1'
    query['return-empty'] = 'true'
    cells = gspreadsheet.GetCellsFeed(spreadsheet_id, wksht_id=edges_worksheet_id, query=query)

    cellnum = 0
    
    for cellval in ["User ID", "Updated Time", "Network Hash", "From Node ID", "To Node ID"]:
        cells.entry[cellnum].cell.inputValue = cellval
        batchRequest.AddUpdate(cells.entry[cellnum])
        cellnum += 1

    gspreadsheet.ExecuteBatch(batchRequest, cells.GetBatchLink().href)
    
    # Write the header row for networks league
    batchRequest = gdata.spreadsheet.SpreadsheetsCellsFeed()

    query = gdata.spreadsheet.service.CellQuery()
    query['min-col'] = '1'
    query['max-col'] = '8'
    query['min-row'] = '1'
    query['max-row'] = '1'
    query['return-empty'] = 'true'
    cells = gspreadsheet.GetCellsFeed(spreadsheet_id, wksht_id=leagues_worksheet_id, query=query)

    cellnum = 0
    
    for cellval in ["User ID", "Updated Time", "Network Hash", "Friend ID", "Friend Name", "Friend Degree", "Friend Closeness", "Friend Betweenness"]:
        cells.entry[cellnum].cell.inputValue = cellval
        batchRequest.AddUpdate(cells.entry[cellnum])
        cellnum += 1

    gspreadsheet.ExecuteBatch(batchRequest, cells.GetBatchLink().href)
    
    logging.info('Headers written for all worksheets in spreadsheet')
    
    return nodes_worksheet_id, edges_worksheet_id, leagues_worksheet_id

def populate_spreadsheet(gspreadsheet, spreadsheet_id, nodes_worksheet_id, edges_worksheet_id, leagues_worksheet_id, q):
    nodes_rownum = 2
    edges_rownum = 2
    leagues_rownum = 2
    
    for network in q:
        # Write nodes
        query = gdata.spreadsheet.service.CellQuery()
        query['min-col'] = '1'
        query['max-col'] = '4'
        query['return-empty'] = 'true'
        
        startnode = 0
        chunk_size = 400
        while startnode < len(network.getnodes() or []):
            nodes_cellnum = 0
            query['min-row'] = str(nodes_rownum)
            query['max-row'] = str(nodes_rownum + len((network.getnodes()[startnode:startnode + chunk_size] or [])) - 1)
            
            batchRequest = gdata.spreadsheet.SpreadsheetsCellsFeed()
            cells = gspreadsheet.GetCellsFeed(spreadsheet_id, wksht_id=nodes_worksheet_id, query=query)
            
            for nodevalue in (network.getnodes()[startnode:startnode + chunk_size] or []):
                for cellval in [str(network.uid), str(network.updated_time), network.networkhash, str(nodevalue)]:
                    cells.entry[nodes_cellnum].cell.inputValue = cellval
                    batchRequest.AddUpdate(cells.entry[nodes_cellnum])
                    nodes_cellnum += 1
                
                nodes_rownum += 1
            
            gspreadsheet.ExecuteBatch(batchRequest, cells.GetBatchLink().href)
            logging.info('Wrote bunch of nodes: %s rows' % (nodes_rownum - 2))
            startnode += chunk_size
        
        logging.info('Wrote all nodes: %s rows' % (nodes_rownum - 2))
        
        # Write edges
        query = gdata.spreadsheet.service.CellQuery()
        query['min-col'] = '1'
        query['max-col'] = '5'
        query['return-empty'] = 'true'
        
        startedge = 0
        chunk_size = 200
        while startedge < len (network.getedges() or []):
            edges_cellnum = 0
            query['min-row'] = str(edges_rownum)
            query['max-row'] = str(edges_rownum + len(network.getedges()[startedge:startedge + chunk_size]) - 1)
            
            batchRequest = gdata.spreadsheet.SpreadsheetsCellsFeed()
            cells = gspreadsheet.GetCellsFeed(spreadsheet_id, wksht_id=edges_worksheet_id, query=query)
            for edgevalue in (network.getedges()[startedge:startedge + chunk_size] or []):
                for cellval in [str(network.uid), str(network.updated_time), network.networkhash, str(edgevalue[0]), str(edgevalue[1])]:
                    cells.entry[edges_cellnum].cell.inputValue = cellval
                    batchRequest.AddUpdate(cells.entry[edges_cellnum])
                    edges_cellnum += 1
                
                edges_rownum += 1
            
            gspreadsheet.ExecuteBatch(batchRequest, cells.GetBatchLink().href)
            logging.info('Wrote bunch of edges: %s rows' % (edges_rownum - 2))
            startedge += chunk_size
        
        logging.info('Wrote all edges: %s rows' % (edges_rownum - 2))
        
        # Write network leagues
        if len((network.getleague() or [])) > 0:
            leagues_cellnum = 0
            query = gdata.spreadsheet.service.CellQuery()
            query['min-col'] = '1'
            query['max-col'] = '8'
            query['min-row'] = str(leagues_rownum)
            query['max-row'] = str(leagues_rownum + len((network.getleague() or [])) - 1)
            query['return-empty'] = 'true'
            
            batchRequest = gdata.spreadsheet.SpreadsheetsCellsFeed()
            cells = gspreadsheet.GetCellsFeed(spreadsheet_id, wksht_id=leagues_worksheet_id, query=query)
            
            for table in (network.getleague() or []):
                for cellval in [str(network.uid), str(network.updated_time), network.networkhash, str(table[0]), str(table[1]), str(table[2]), str(table[3]), str(table[4])]:
                    cells.entry[leagues_cellnum].cell.inputValue = cellval
                    batchRequest.AddUpdate(cells.entry[leagues_cellnum])
                    leagues_cellnum += 1
                    
                leagues_rownum += 1
                
            gspreadsheet.ExecuteBatch(batchRequest, cells.GetBatchLink().href)
        logging.info('Wrote all leagues: %s rows' % (leagues_rownum - 2))

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
            
            if backend:
                file_name = self.request.get('file_name', False)
                access_token = pickle.loads(base64.b64decode(self.request.get('google_access_token', '')))
                
                serviceG = gdata.apps.service.AppsService(source=conf.GOOGLE_APP_NAME)
                serviceG.SetOAuthInputParameters(signature_method=gdata.auth.OAuthSignatureMethod.HMAC_SHA1,
                                                consumer_key=conf.GOOGLE_CONSUMER_KEY,
                                                consumer_secret=conf.GOOGLE_CONSUMER_SECRET)
                
                serviceG.current_token = access_token
                serviceG.SetOAuthToken(access_token)
                
                q = db.GqlQuery("SELECT * FROM Network")
                gspreadsheet = gdata.spreadsheet.service.SpreadsheetsService()
                gspreadsheet.SetOAuthToken(access_token)
                
                spreadsheet_id, worksheet_id = get_spreadsheet_by_name(gspreadsheet, file_name)
                nodes_worksheet_id, edges_worksheet_id, leagues_worksheet_id = initialize_spreadsheet(gspreadsheet, spreadsheet_id, worksheet_id, q)
                populate_spreadsheet(gspreadsheet, spreadsheet_id, nodes_worksheet_id, edges_worksheet_id, leagues_worksheet_id, q)
            else:
                scopes = ['https://docs.google.com/feeds/', 'https://spreadsheets.google.com/feeds/']
                oauth_callback = fbutils.base_url(self) + mode + '/networks.docs?code=' + self.request.get('code')
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
                    
                    file_name = 'Network informations (%s)' % datetime.datetime.today()
                    spreadsheet_url = create_spreadsheet(access_token, file_name)
                    
                    taskqueue.add(url='/' + mode + '/networks.docs',
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
        q = db.GqlQuery("SELECT * FROM Network")
        
        if extension == 'xml':
            self.response.headers['Content-Type'] = "text/xml"
            self.response.out.write('<networks count="%s">' % q.count())
            
            for network in q:
                self.response.out.write('  <network uid="%s" updated_time="%s" netowrkhash="%s">\n' % (network.uid, network.updated_time, network.networkhash))
                self.response.out.write('    <nodes count="%s">\n' % len(network.getnodes() or []))
                for node in (network.getnodes() or []):
                    self.response.out.write('      <node id="%s" />\n' % node)
                self.response.out.write('    </nodes>\n')
                self.response.out.write('    <edges count="%s">\n' % len(network.getedges() or []))
                for fromnode, tonode in (network.getedges() or []):
                    self.response.out.write('      <edge fromNodeId="%s" toNodeId="%s" />\n' % (fromnode, tonode))
                self.response.out.write('    </edges>\n')
                self.response.out.write('    <league count="%s">\n' % len(network.getleague() or []))
                for table in (network.getleague() or []):
                    self.response.out.write('      <friend uid="%s" name="%s" degree="%s" closeness="%s" betweenness="%s"/>\n' % (table[0], table[1], table[2], table[3], table[4]))
                self.response.out.write('    </league>\n')
                self.response.out.write('  </network>\n\n')
                                        
            self.response.out.write('</networks>')
                
        if extension == 'csv':
            self.response.headers['Content-Type'] = "text/csv"
            self.response.out.write('uid,updated_time,networkhash,nodeid,fromnodeid,tonodeid,uid,name,degree,closeness,betweenness\n')
            
            for network in q:
                if len((network.getnodes() or [])) == 0 and len((network.getedges() or [])) == 0 and len((network.getleague() or [])) == 0:
                    self.response.out.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (network.uid, network.updated_time, network.networkhash, '', '', '', '', '', '', '', '')) 
                for nodevalue in (network.getnodes() or []):
                    self.response.out.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (network.uid, network.updated_time, network.networkhash, nodevalue, '', '', '', '', '', '', ''))
                for edgevalue in (network.getedges() or []):
                    self.response.out.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (network.uid, network.updated_time, network.networkhash, '', edgevalue[0], edgevalue[1], '', '', '', '', ''))
                for table in (network.getleague() or []):    
                    self.response.out.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (network.uid, network.updated_time, network.networkhash, '', '', '', table[0], table[1], table[2], table[3], table[4]))
            
        if extension == 'xls':
            self.response.headers['Content-Type'] = "application/vnd.ms-excel"
            self.response.out.write('uid\tupdated_time\tnetworkhash\tnodeid\tfromnodeid\ttonodeid\tuid,name\tdegree\tcloseness\tbetweenness\r\n')
            
            for network in q:
                if len((network.getnodes() or [])) == 0 and len((network.getedges() or [])) == 0 and len((network.getleague() or [])) == 0:
                    self.response.out.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\r\n' % (network.uid, network.updated_time, network.networkhash, '', '', '', '', '', '', '', '')) 
                for nodevalue in (network.getnodes() or []):
                    self.response.out.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\r\n' % (network.uid, network.updated_time, network.networkhash, nodevalue, '', '', '', '', '', '', ''))
                for edgevalue in (network.getedges() or []):
                    self.response.out.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\r\n' % (network.uid, network.updated_time, network.networkhash, '', edgevalue[0], edgevalue[1], '', '', '', '', ''))
                for table in (network.getleague() or []):    
                    self.response.out.write('%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\r\n' % (network.uid, network.updated_time, network.networkhash, '', '', '', table[0], table[1], table[2], table[3], table[4]))
    else:
        self.response.out.write('Wrong format requested.')
            
class MainPage(webapp2.RequestHandler):
    def get(self, extension):
        if extension in supported_extensions_login: renderPageLogin(self, extension, 'admin')
        else: renderPage(self, extension, 'admin')

    def post(self, extension):
        if extension in supported_extensions_login: renderPageLogin(self, extension, 'admin')
        else: renderPage(self, extension, 'admin')
