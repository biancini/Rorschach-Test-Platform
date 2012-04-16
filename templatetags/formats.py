from google.appengine.ext.webapp import template
from utils import conf

register = template.create_template_register()

def floatf(v, decimals):
    if v == None: v = 0.0    
    return ('%0.' + decimals + 'f') % float(v)

def fstrreplace(v, p):
    if v == None: None
    f, r = p.split('|')
    return str(v).replace(f, r)

def fortmatindex(v, name):
    if name in conf.Config().INDEX_TYPES: formatted = conf.Config().INDEX_TYPES[name] % v
    else: formatted = floatf(v, 2)
    
    return formatted

register.filter('formatstrreplace', fstrreplace)
register.filter('formatfloat', floatf)
register.filter('fortmatindex', fortmatindex)