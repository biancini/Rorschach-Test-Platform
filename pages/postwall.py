import webapp2
import json
import logging
import string

from utils import conf, fbutils, sessionmanager

conf = conf.Config()

class MainPage(webapp2.RequestHandler):
    def renderPage(self):
        session = sessionmanager.getsession(self)
        msgtype = self.request.get('msgtype', None)
        
        
        if msgtype == 'index':
            indexname = self.request.get('indexname', None)
            value = self.request.get('value', None)
            
            if indexname == None or value == None:
                self.response.out.write("Error, wrong parameters.")
                logging.error("Unable to post to suer wall: wrong parameters.")
                return
            
            result = fbutils.fb_call("me/feed",
                                     {'access_token' : session['access_token'],
                                      'message': 'I have just computed my ' + indexname + ' sociological index, its value is ' + value,
                                      'name': 'Rorschach test platform',
                                      'caption': indexname.title() + ' is a sociological index computed on the information present in FB. ' + conf.INDEXES[indexname] + '.',
                                      'picture': fbutils.base_url(self) + 'smallgraph/' + session['me']['id'] + '/' + indexname,
                                      'link': conf.base_url(self) + 'index/' + session['me']['id'] + '/' + indexname},
                                     method='POST')
            
            if not 'id' in result: logging.error("Unable to post to the user wall: " + str(result))
            
        elif msgtype == 'network':
            nodes = self.request.get('nodes', None)
            edges = self.request.get('edges', None)
            
            league = self.request.get('league', 'None').decode('utf-8')
            league = string.replace(league, '&#39;', '\'')
            league = eval(league)
            
            i = 1
            message  = 'My Facebook network has ' + nodes + ' contacts and ' + edges + ' connections amongst them!\n'
            message += 'In my network the more influential contacts are:\n'
            for curuser in league:
                message += str(i) + '. ' + curuser[1] + '\n'
                i += 1
            
            result = fbutils.fb_call("me/feed",
                                     {'access_token' : session['access_token'],
                                      'message': message,
                                      'name': 'My network elite group',
                                      'caption': 'The elite group has been computed by Rorschach test platform with the information from your network of contatcs. For all your contacts information about their centrality has been computed using SNA. These information are about the role of influence and the number of connection of a friend within your network. Scoring these results, it has been possible to produce the list of the top influencers of your friends.',
                                      'link': conf.base_url(self) + 'network/' + session['me']['id']},
                                     method='POST')
            
            if not 'id' in result: logging.error("Unable to post to the user wall: " + str(result))
            
        else:
            logging.error("Wrong msgtype parameter to postwall: " + str(msgtype))
            
        self.response.out.write(json.dumps(result))

    def post(self):
        self.renderPage()
