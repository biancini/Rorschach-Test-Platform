import simplejson as json
import urllib, urlparse, base64
import conf

from google.appengine.api import urlfetch

conf = conf.Config()

def base_url(self):
    url = urlparse.urlparse(self.request.url)
    baseurl = ''
    if url.port == None:
        baseurl = "%s://%s/" % (url.scheme, url.hostname)
    else:
        baseurl = "%s://%s:%s/" % (url.scheme, url.hostname, url.port)
    return baseurl


def oauth_login_url(self, preserve_path=True, next_url=None):
    fb_login_uri = ("https://www.facebook.com/dialog/oauth"
                    "?client_id=%s&redirect_uri=%s" %
                    (conf.FBAPI_APP_ID, next_url))

    if conf.FBAPI_SCOPE:
        fb_login_uri += "&scope=%s" % ",".join(conf.FBAPI_SCOPE)
        
    return fb_login_uri


def simple_dict_serialisation(params):
    return "&".join(map(lambda k: "%s=%s" % (k, params[k]), params.keys()))


def base64_url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip('=')


def fbapi_get_string(path, domain=u'graph', params=None, access_token=None,
                     encode_func=urllib.urlencode):
    """Make an API call"""
    if not params:
        params = {}
    params[u'method'] = u'GET'
    if access_token:
        params[u'access_token'] = access_token

    for k, v in params.iteritems():
        if hasattr(v, 'encode'):
            params[k] = v.encode('utf-8')

    url = u'https://' + domain + u'.facebook.com' + path
    params_encoded = encode_func(params)
    url = url + params_encoded
    result = urlfetch.fetch(url).content
    return result


def fbapi_auth(self, code, redirect_uri=None):
    params = {'client_id': conf.FBAPI_APP_ID,
              'redirect_uri': redirect_uri or base_url(self),
              'client_secret': conf.FBAPI_APP_SECRET,
              'code': code}
    result = fbapi_get_string(path=u"/oauth/access_token?", params=params,
                              encode_func=simple_dict_serialisation)
    
    #logging.info("Result for call to retrieve Access Token " + str(result))
    pairs = result.split("&", 1)
    result_dict = {}
    for pair in pairs:
        (key, value) = pair.split("=")
        result_dict[key] = value

    return (result_dict["access_token"], result_dict["expires"])


def fbapi_get_application_access_token(self, redirect_uri=None):
    token = fbapi_get_string(
        path=u"/oauth/access_token?",
        params=dict(grant_type=u'client_credentials',
                    client_id=conf.FBAPI_APP_ID,
                    redirect_uri=redirect_uri or base_url(self),
                    client_secret=conf.FBAPI_APP_SECRET),
        domain=u'graph')

    token = token.split('=')[-1]
    return token


def fql(fql, token, args=None):
    if not args:
        args = {}

    args["query"], args["format"], args["access_token"] = fql, "json", token
    return json.loads(
        urlfetch.fetch("https://api.facebook.com/method/fql.query?" +
                        urllib.urlencode(args)).content)

def fb_call(call, args=None, method='GET'):
    if method != 'GET' and method != 'POST': method='GET'
    
    if method == 'GET':
        load = json.loads(urlfetch.fetch("https://graph.facebook.com/" + call +
                                         '?' + urllib.urlencode(args)).content)
    else:
        load = urlfetch.fetch(url ="https://graph.facebook.com/" + call,
                              payload=urllib.urlencode(args),
                              method=urlfetch.POST).content
                          
    return load 

def is_friend(access_token, uid, frienduid):
    if uid == frienduid: return True

    result = fb_call(uid + "/friends/" + frienduid,
                     {'access_token' : access_token},
                     method='GET')

    if not 'data' in result or len(result['data']) == 0: return False
    else: return True
    
def get_user_roles(app_token, userid):
    response = fbapi_get_string(
        path=u"/" + conf.FBAPI_APP_ID + u"/roles?",
        access_token=app_token)

    data = json.loads(response)['data']
    roles = []

    for role in data :
        if role['user'] == userid :
            roles.append(role['role'])

    return roles
