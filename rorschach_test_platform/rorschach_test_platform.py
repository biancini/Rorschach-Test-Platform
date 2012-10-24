""" 
This file is part of OpenSesame.
This file implements the Rorschach Test Platform plugin module which 
integrates with the Facebook application available at
https://rorschach-test-platform.appspot.com
to download sociological indexes computed for test subjects and computed
on their contact network using SNA techniques.

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

__author__ = 'andrea.biancini@gmail.com (Andrea Biancini)'
__version__ = '0.8'

from libopensesame import item, generic_response, exceptions
from libqtopensesame import qtplugin
from PyQt4 import QtCore, QtGui

import openexp.canvas
import os, imp
import urllib2

import pygame 
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN

class rorschach_test_platform(item.item, generic_response.generic_response): 
    """ 
    Implements the plug-in 
    """ 

    def __init__(self, name, experiment, string = None): 
        """ 
        Constructor 
        """
        
        self.baseurl = "https://rorschach-test-platform.appspot.com"
        #self.baseurl = "http://fuzzy.local:8080"
        #self.baseurl = "http://logic.local:8080"
        
        filepath = os.path.dirname( __file__ ) + '/facebook.py'
        self.facebook_mod = imp.load_source('facebook', filepath)
        self.facebook_mod.BASE_URL = self.baseurl
        
        filepath = os.path.dirname( __file__ ) + '/localjson.py'
        self.json_mod = imp.load_source('localjson', filepath)
             
        # First we set the plug-ins properties 
        self.item_type = "rorschach_test_platform"
        self.description = "Integrates with Rorschach Test Platform on Facebook"
        self.fullscreen = "yes"
                 
        # The parent handles the rest of the construction 
        item.item.__init__(self, name, experiment, string)
        
    def prepare(self):
        """ 
        Initialize the Rorschach Test Platform application on Facebook for the user 
        """ 
        item.item.prepare(self)
        
        if not self.has('indexes'):
            print "The Rorschach Test Plugin is not configured properly."
            return False
        
        validConfig = False
        while validConfig == False:
            #code = self.facebook_mod.getCode()
            access_token = self.facebook_mod.getAccessToken()
        
            if access_token:
                res = urllib2.urlopen(self.baseurl + '/opensesame/config?token=' + access_token)
                result = self.json_mod.read(res.read())
            else: result = []
            
            if not 'result' in result or result['result'] == False:
                print "Not a valid config, the user has not logged in to Rorschach Test Platform."
                #QtGui.QMessageBox.about(self.experiment.surface, "Rorschach Test Platform",
                #                        "Not a valid config, you have not logged in to Rorschach Test Platform.\n"
                #                        "Verify in your browser you have access to Rorschach Test Pltaform and download the access key.")
                
                self.facebook_mod.loginFB()
                validConfig = False
            else:
                asstest = filter(lambda tmptest: tmptest['name'] == self.get('associated_test'), result['tests'])
                if not len(asstest) > 0:
                    print "The test '%s' is not a valid test in Rorschach Test Platform." % self.get('associated_test') 
                    return False
                if not asstest[0]['active']:
                    print "The test '%s' is not active." % self.get('associated_test')
                    return False
                if not asstest[0]['withindates']:
                    print "The test '%s' has a start date and end date not including today." % self.get('associated_test')
                    return False
                
                validConfig = True
        
        print("Not all indexes downloaded from FB. Downloading missing indexes...")
        self.facebook_mod.getIndexesFB(self.indexes)
        self.computed_indexes = self.facebook_mod.getComputedIndexes()
        
        self.c = openexp.canvas.canvas(self.experiment, self.get("background"), self.get("foreground"))
        print "Initialized the Rorschach Test Platform plugin, test: %s." % self.get('associated_test')        
        return True
    
    def run(self):
        """ 
        Handles the actual test phase 
        """ 
        # Log the onset time of the item 
        self.set_item_onset()
        
        t = pygame.time.get_ticks() 
        start_t = t
        self.experiment.start_response_interval = self.get("time_%s" % self.name)
        
        indexes = ''
        for index in self.computed_indexes.keys():
            indexes += "%s: %s\n" % (index, self.computed_indexes[index])
        content = "The indexes downloaded from Rorschach Test Platform are:\n\n%s\n[Press any key to continue]" % indexes
        line_nr = -len(content.split('\n')) / 2
        for line in content.split('\n'):
            self.c.textline(line, line_nr)
            line_nr += 1
        
        if self.duration != 'hidden':
            self.c.show()
            
            # Loop until a key is pressed 
            go = True 
            while go:
                pygame.time.wait(50 - pygame.time.get_ticks() + t) 
                t = pygame.time.get_ticks() 
    
                if type(self.duration) == int:             
                    # Wait for a specified duration 
                    if t - start_t >= self.duration: 
                        go = False 
                
                # Catch escape presses 
                for event in pygame.event.get():         
                    if event.type == KEYDOWN:                     
                        if event.key == pygame.K_ESCAPE: 
                            raise exceptions.runtime_error("The escape key was pressed.") 
                        if self.duration == "keypress":     
                            go = False 
                             
                    if event.type == MOUSEBUTTONDOWN and self.duration == "mouseclick": 
                        go = False 
        
        for index in self.computed_indexes:
            self.experiment.set("index_" + index, self.experiment.usanitize(self.experiment.sanitize(str(self.computed_indexes[index]))))
        self.experiment.set("response", self.experiment.usanitize(self.experiment.sanitize(str(self.computed_indexes))))
        self.experiment.end_response_interval = self.get("time_%s" % self.name)
        self.response_bookkeeping()
        
        # Report success
        return True
    
class qtrorschach_test_platform(rorschach_test_platform, qtplugin.qtplugin): 
    """ 
    Handles the GUI aspects of the plug-in. 
    """ 

    def __init__(self, name, experiment, string = None):
        """ 
        Constructor. This function doesn't do anything specific 
        to this plugin. It simply calls its parents.
        """ 
        self.duration = "keypress"
        
        # Pass the word on to the parents         
        rorschach_test_platform.__init__(self, name, experiment, string)         
        qtplugin.qtplugin.__init__(self, __file__)    
        
    def init_edit_widget(self): 
        """ 
        This function creates the controls for the edit  widget. 
        """
        self.lock = True 
        qtplugin.qtplugin.init_edit_widget(self, False)
        
        self.durationtext = self.add_line_edit_control("duration", "Duration", tooltip = "Expecting a value in milliseconds, 'keypress', 'mouseclick' or 'hidden'.") 
        
        label = QtGui.QLabel("Attention, you must have added Rorschach Test Platform to your Facebook account and you must be logged in Facebook.\nTo obtain a valid access token click the button below.")
        self.add_control("", label, "", "")
        
        button = QtGui.QPushButton(self.experiment.icon("browse"), "Get access token from Rorschach Test Platform")
        button.setIconSize(QtCore.QSize(16, 16))
        button.clicked.connect(self.click_func)
        self.add_control("Login with FB", button, "Get access token from Rorschach Test Platform", "")
        
        label = QtGui.QLabel("If the controls here below are not populated correctly is probably due to the fact that you have not logged in Facebook.")
        self.add_control("", label, "", "")
        
        tooltip = "Available tests on Rorschach Test Platform" 
        self.testlist = self.add_combobox_control(None, "Available tests", [], tooltip = tooltip)
        
        self.indexlist = QtGui.QListView()
        self.add_control("Indexes needed", self.indexlist, "Specify the indexes needed for the test purpose.", "")
        
        self.edit_vbox.addStretch()         
        self.lock = False
        
        self.populate_info()
        
    def populate_info(self):
        code = self.facebook_mod.getCode()
        access_token = self.facebook_mod.getAccessToken()
        
        if code and access_token:
            try:
                res = urllib2.urlopen(self.baseurl + '/opensesame/config?token=' + access_token)
                result = self.json_mod.read(res.read())
                
                if self.has('duration'): self.durationtext.setText(self.get('duration'))
                
                if 'tests' in result:
                    self.testlist.addItem('')
                    for curtest in result['tests']:
                        if 'name' in curtest and self.testlist.findText(curtest['name']) == -1:
                            self.testlist.addItem(curtest['name'])
                            
                    if self.has('associated_test'):
                        self.testlist.setCurrentIndex(self.testlist.findText(self.experiment.unsanitize(self.get('associated_test'))))
                    
                if 'indexes' in result:
                    self.indexes_check = []
                    model = QtGui.QStandardItemModel()
                    
                    indexes = self.has('indexes') and self.get('indexes') or [] 
                    
                    for curindex in result['indexes'].keys():
                        item = QtGui.QStandardItem(curindex)
                        if str(item.text()) is indexes: item.setCheckState(QtCore.Qt.Checked)
                        else: item.setCheckState(QtCore.Qt.Unchecked)
                        item.setCheckable(True)
                        self.indexes_check.append(item)
                        model.appendRow(item)
                    
                    model.itemChanged.connect(self.apply_edit_changes)
                    self.indexlist.setModel(model)
            except:
                print "Unable to download configurations from Rorschach Test Platform Facebook application."
                pass
    
    def click_func(self, e):
        """Login on Rorschach Test Platform Facebook application"""
        self.facebook_mod.loginFB()
        self.populate_info()
        
    def apply_edit_changes(self):
        """Apply the controls"""
        if qtplugin.qtplugin.apply_edit_changes(self, False) == False or self.lock:
            return False
        
        if self.testlist.count() > 1:
            self.set('associated_test', str(self.experiment.usanitize(unicode(self.testlist.currentText()))))
        
        indexes = []
        if self.has('indexes_check'):
            for item in self.indexes_check:
                if item.checkState() == QtCore.Qt.Checked:
                    indexes.append(str(item.text()))
                    
            self.set("indexes", indexes)
            
        self.experiment.main_window.refresh(self.name)
        return True

    def edit_widget(self):
        """Update the controls"""
        self.lock = True
        
        if self.has('associated_test'):
            self.testlist.setCurrentIndex(self.testlist.findText(self.experiment.unsanitize(str(self.get('associated_test')))))
        
        if self.has('indexes'):
            if self.has('indexes_check'):
                for item in self.indexes_check:
                    if str(item.text()) in self.get('indexes'):
                        item.setCheckState(QtCore.Qt.Checked)
        
        qtplugin.qtplugin.edit_widget(self)
        self.lock = False
        
        return self._edit_widget
