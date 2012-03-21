from google.appengine.ext.webapp import template

register = template.create_template_register()

def floatf(v, decimals):
    if v == None: v = 0.0    
    return ('%0.' + decimals + 'f') % float(v)

def fstrreplace(v, p):
    if v == None: None
    f, r = p.split('|')
    return str(v).replace(f, r)

register.filter('formatstrreplace', fstrreplace)
register.filter('formatfloat', floatf)