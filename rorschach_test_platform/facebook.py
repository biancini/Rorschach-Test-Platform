""" 
This file is part of OpenSesame.
This file interacts with the Facebook application available at
https://rorschach-test-platform.appspot.com
using the client's web browser.

OpenSesame is free software: you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published by 
the Free Software Foundation, either version 3 of the License, or 
(at your option) any later version. 

OpenSesame is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
GNU General Public License for more details. 
 
You should have received a copy of the GNU General Public License 
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>. 
"""

import os, sys
import urllib2, urllib, urlparse
import BaseHTTPServer
import webbrowser

__author__ = 'andrea.biancini@gmail.com (Andrea Biancini)'
__version__ = '0.8'

CODE = None
ACCESS_TOKEN = None
LOCAL_FILE = os.path.dirname( __file__ ) + '/.fb_access_token'
SERVER_ADDRESS = ('127.0.0.1', 33333)
BASE_URL = ""
INDEX_LIST = []
INDEX_COMP = {}

def get_url(path, args=None):
    args = args or {}
    if 'access_token' in args or 'client_secret' in args: endpoint = 'https://graph.facebook.com'
    else: endpoint = 'http://graph.facebook.com'
    return endpoint+path+'?'+urllib.urlencode(args)

def get(path, args=None):
    return urllib2.urlopen(get_url(path, args=args)).read()

class IndexesRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
        global BASE_URL
        global INDEX_LIST
        global INDEX_COMP
        
        self.send_response(200)
        self.end_headers()
        varlen = int(self.headers['Content-Length'])
        postvars = urlparse.parse_qs(self.rfile.read(varlen))
        
        INDEX_COMP = {}
        for index in INDEX_LIST:
            indexvalue = postvars[index][0]
            if indexvalue != "<null>":
                INDEX_COMP[index] = indexvalue

        self.wfile.write('<html><head>')
        self.wfile.write('<link href="' + BASE_URL + '/static/styles/reset.css" media="screen" rel="stylesheet" />')
        self.wfile.write('<link href="' + BASE_URL + '/static/styles/base.css" media="screen and (min-device-width: 500px)" rel="stylesheet" />')
        self.wfile.write('<link href="' + BASE_URL + '/static/styles/mobile.css" media="screen and (max-device-width: 499px)" rel="stylesheet"  />')
        self.wfile.write('<link href="' + BASE_URL + '/static/styles/index.css" media="screen" rel="stylesheet" />')
        self.wfile.write('<link href="' + BASE_URL + '/static/styles/form.css" media="screen" rel="stylesheet"  />')
        self.wfile.write('</head><body>')
        self.wfile.write('<header class="clearfix">')
        self.wfile.write('<p id="picture" style="background-image: url(' + BASE_URL + '/static/images/macchie.jpg); background-size: 64px 64px"></p>')
        self.wfile.write('<h1>Rorschach Test Platform index download</h1>')
        self.wfile.write('</header>')
        self.wfile.write('<section id="normalsection" class="clearfix">')
        self.wfile.write('<h3>Index values download in OpenSesame test</h3>')
        self.wfile.write('<p>You have successfully downloaded the following index values:</p>')
        for index in INDEX_COMP.keys():
            self.wfile.write('&nbsp;&nbsp;- ' + index + ': ' + INDEX_COMP[index] + '<br/>') 
        self.wfile.write('<br/>') 
        self.wfile.write('<p>You can close this window now.</p>')
        self.wfile.write('</section>')
        self.wfile.write('<section id="copyright"><p>Rorschach Test Platform - developed by <a href="http://www.facebook.com/biancio" alt="Andrea Biancini">Andrea Biancini</a></p>')
        self.wfile.write('<div class="fb-like" data-href="http://apps.facebook.com/rorschach_test_platf" data-send="false" data-width="450" data-show-faces="false" data-font="tahoma"></div></section>')
        self.wfile.write('<div id="fb-root"></div>')
        self.wfile.write('<script type="text/javascript">')
        self.wfile.write('<!--')
        self.wfile.write('(function(d, s, id) {')
        self.wfile.write('var js, fjs = d.getElementsByTagName(s)[0];')
        self.wfile.write('if (d.getElementById(id)) return;')
        self.wfile.write('js = d.createElement(s); js.id = id;')
        self.wfile.write('js.src = "//connect.facebook.net/en_GB/all.js#xfbml=1&appId=223295151080625";')
        self.wfile.write('fjs.parentNode.insertBefore(js, fjs);')
        self.wfile.write('}(document, "script", "facebook-jssdk"));')
        self.wfile.write('// -->')
        self.wfile.write('</script>')
        self.wfile.write('</body></html>')

    def do_GET(self):
        global BASE_URL
        global ACCESS_TOKEN
        global INDEX_LIST
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        self.wfile.write('<html><body>')
        self.wfile.write('<iframe id="myframe" src="' + BASE_URL + '/opensesame/indexes?reqired_indexes=' + str(INDEX_LIST) + '&token=' + ACCESS_TOKEN + '" style="width: 90%; height: 90%; border: 0"></iframe>')
        self.wfile.write('</body></html>')

class LoginRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
        global BASE_URL
        global CODE
        global ACCESS_TOKEN
        
        self.send_response(200)
        self.end_headers()
        varlen = int(self.headers['Content-Length'])
        postvars = urlparse.parse_qs(self.rfile.read(varlen))
        
        CODE = postvars['code'][0]
        ACCESS_TOKEN = postvars['access_token'][0]
        
        print "2 %s %s" % (CODE, ACCESS_TOKEN)
        
        if CODE is None or CODE == '':
            self.wfile.write('<html><body>')
            self.wfile.write('<h1>Rorschach Test Platform authentication</h1>')
            self.wfile.write('<p>Sorry, authentication failed.</p>') 
            self.wfile.write('</body></html>')
            sys.exit(1)

        open(LOCAL_FILE,'w').write(CODE + '\n' + ACCESS_TOKEN)
        self.wfile.write('<html><head>')
        self.wfile.write('<link href="' + BASE_URL + '/static/styles/reset.css" media="screen" rel="stylesheet" />')
        self.wfile.write('<link href="' + BASE_URL + '/static/styles/base.css" media="screen and (min-device-width: 500px)" rel="stylesheet" />')
        self.wfile.write('</head><body>')
        self.wfile.write('<header class="clearfix">')
        self.wfile.write('<p id="picture" style="background-image: url(' + BASE_URL + '/static/images/macchie.jpg); background-size: 64px 64px"></p>')
        self.wfile.write('<h1>Rorschach Test Platform authentication</h1>')
        self.wfile.write('</header>')
        self.wfile.write('<section id="normalsection" class="clearfix">')
        self.wfile.write('<h3>Authentication with Facebook application</h3>')
        self.wfile.write('<p>You have successfully logged in to facebook.<br /><br />You can close this window now.</p>')
        self.wfile.write('</section>')
        self.wfile.write('<section id="copyright"><p>Rorschach Test Platform - developed by <a href="http://www.facebook.com/biancio" alt="Andrea Biancini">Andrea Biancini</a></p>')
        self.wfile.write('<div class="fb-like" data-href="http://apps.facebook.com/rorschach_test_platf" data-send="false" data-width="450" data-show-faces="false" data-font="tahoma"></div></section>')
        self.wfile.write('<div id="fb-root"></div>')
        self.wfile.write('<script type="text/javascript">')
        self.wfile.write('<!--')
        self.wfile.write('(function(d, s, id) {')
        self.wfile.write('var js, fjs = d.getElementsByTagName(s)[0];')
        self.wfile.write('if (d.getElementById(id)) return;')
        self.wfile.write('js = d.createElement(s); js.id = id;')
        self.wfile.write('js.src = "//connect.facebook.net/en_GB/all.js#xfbml=1&appId=223295151080625";')
        self.wfile.write('fjs.parentNode.insertBefore(js, fjs);')
        self.wfile.write('}(document, "script", "facebook-jssdk"));')
        self.wfile.write('// -->')
        self.wfile.write('</script>')
        self.wfile.write('</body></html>')

    def do_GET(self):
        global BASE_URL
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        self.wfile.write('<html><body>')
        self.wfile.write('<iframe id="myframe" src="' + BASE_URL + '/opensesame/access" style="width: 90%; height: 90%; border: 0"></iframe>')
        self.wfile.write('</body></html>')

def getComputedIndexes():
    global INDEX_COMP
    
    return INDEX_COMP

def getCode():
    global CODE
    global ACCESS_TOKEN
    if CODE: return CODE
    
    if os.path.exists(LOCAL_FILE):
        (CODE, ACCESS_TOKEN) = open(LOCAL_FILE).read().split('\n')
        return CODE
    else:
        return None
    
def getAccessToken():
    global CODE
    global ACCESS_TOKEN
    if ACCESS_TOKEN: return ACCESS_TOKEN
    
    if os.path.exists(LOCAL_FILE):
        (CODE, ACCESS_TOKEN) = open(LOCAL_FILE).read().split('\n')[:2]
        return ACCESS_TOKEN
    else:
        return None

def loginFB():
    global CODE
    global ACCESS_TOKEN
    global SERVER_ADDRESS
    
    print "Logging you in to Facebook..."
    CODE = None
    ACCESS_TOKEN = None
    httpd = BaseHTTPServer.HTTPServer(SERVER_ADDRESS, LoginRequestHandler)
    webbrowser.open('http://%s:%s' % SERVER_ADDRESS)
    
    print "%s %s" % (CODE, ACCESS_TOKEN)
    while CODE is None and ACCESS_TOKEN is None:
        try: httpd.handle_request()
        except : pass
    
def getIndexesFB(indexlist):
    global INDEX_LIST
    global INDEX_COMP
     
    print "Getting the user indexes from Facebook..."
    INDEX_LIST = eval(indexlist)
    httpd = BaseHTTPServer.HTTPServer(SERVER_ADDRESS, IndexesRequestHandler)
    webbrowser.open('http://%s:%s' % SERVER_ADDRESS)
    
    terminate = False
    while not terminate:
        try: httpd.handle_request()
        except: pass
        
        terminate = True
        for index in INDEX_LIST:
            terminate = terminate and (index in INDEX_COMP.keys())