import logging
import re

from utils import fbutils, conf
from gaesessions import get_current_session

conf = conf.Config()
RE_MOBILE = re.compile(r"(iphone|ipod|blackberry|android|palm|windows\s+ce)", re.I)

def get_user_agent(request):
    # Some mobile browsers put the User-Agent in a HTTP-X header
    headers = dict((k.upper(), v) for k,v in request.headers.iteritems())
    
    return headers.get('HTTP_X_OPERAMINI_PHONE_UA') or \
        headers.get('HTTP_X_SKYFIRE_PHONE') or \
        headers.get('HTTP_USER_AGENT', '') or \
        headers.get('USER_AGENT', '') or \
        headers.get('USER-AGENT', '')
        
def isDesktop(request):
    return not bool(RE_MOBILE.search(get_user_agent(request)))

def getsession(self, access_token=None, redirect_uri=None):
    session = get_current_session()
    
    #try:
    try:
        if not access_token: access_token = fbutils.fbapi_auth(self, self.request.get('code'), redirect_uri)[0]
        fbutils.fb_call('me', args={'access_token': access_token})
    except:
        session.terminate()
        return None
    
    try:
        if not session.is_active():
            conf.BASE_URL = fbutils.base_url(self)
            session.regenerate_id()
            session.start()
            logging.info("Created a new session " + str(session))
            
            me = fbutils.fb_call('me', args={'access_token': access_token})
            if 'error' in me: raise Exception(me['error'['message']])
            appid = fbutils.fb_call(conf.FBAPI_APP_ID, args={'access_token': access_token})
            if 'error' in appid: raise Exception(appid['error'['message']])
            app_token = fbutils.fbapi_get_application_access_token(self, redirect_uri)
            if 'error' in app_token: raise Exception(app_token['error'['message']])
            roles = fbutils.get_user_roles(app_token, me['id'])
            if 'error' in roles: raise Exception(roles['error'['message']])
            
            session['access_token'] = access_token
            session['me'] = me
            session['appid'] = appid
            session['app_token'] = app_token
            session['isdesktop'] = isDesktop(self.request)
            
            session['roles'] = ['user']
            if 'administrators' in (roles or []) or 'insights' in (roles or []):
                session['roles'].append('administrator')
            if 'administrators' in (roles or []):
                session['roles'].append('technician')    
            
            session.save()
    except:
        session.terminate()
        return None
    
    return session