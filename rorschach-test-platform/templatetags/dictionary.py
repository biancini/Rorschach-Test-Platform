import logging
from google.appengine.ext.webapp import template

register = template.create_template_register()

def key(d, key_name):
    try:
        value = d[key_name]
    except KeyError:
        value = None
        
    return value

def join(l, delimeter='/'):
    if l == None: return None
    else: return delimeter.join(l)

register.filter('keyfromdict', key)
register.filter('joinlist', join)