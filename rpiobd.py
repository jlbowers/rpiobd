#!/usr/bin/env python
############################################################################
#
# rpiobd.py
#
# Copyright 2004 Donour Sizemore (donour@uchicago.edu)
# Copyright 2009 Secons Ltd. (www.obdtester.com)
# Copyright 2016 Nicholas Bowers (njbowers2001@gmail.com)
#
# This file is part of RpiOBD.
#
# RpiOBD is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# RpiOBD is based on pyOBD, developed by Secons Ltd.
#
# pyOBD is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# pyOBD is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyOBD; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
############################################################################
import time
import kivy
import obd
import threading

from gps import *
from os.path import expanduser
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.actionbar import ActionBar, ActionButton, ActionPrevious
from kivy.properties import  ObjectProperty
from kivy.uix.widget import Widget
from kivy.logger import Logger
from kivy.properties import NumericProperty, StringProperty, BooleanProperty,\
    ListProperty
from kivy.animation import Animation

OBD_connection = None
gpsd = None
driving_log = None


class ObdPoller():
    def __init__(self):
        global OBD_connection
	RootApp.root.ids.notifications.text += 'Connecting to OBD\n'
        obd.logger.setLevel(obd.logging.DEBUG)
        OBD_connection = obd.Async(RootApp.COMPORT)
	OBD_connection.watch(obd.commands.RPM)


class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd #bring it in scope
        gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
        self.current_value = None
        self.running = True #setting the thread running to true
 
    def run(self):
        global gpsd
        while self.running:
            gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer


def update_measurements(dt):
    global gpsd
    global OBD_connection
    global driving_log
    RootApp.root.ids.lat_label.text = 'Longitude\n'+str(gpsd.fix.latitude)
    RootApp.root.ids.lon_label.text = 'Latitude\n'+str(gpsd.fix.longitude)
    RootApp.root.ids.gps_speed_label.text = 'GPS Speed (m/s)\n'+str(gpsd.fix.speed)
    RootApp.root.ids.obd1_label.text = 'RPM\n'+str(OBD_connection.query(obd.commands.RPM))
    RootApp.root.ids.obd2_label.text = 'Throttle Pos %\n'+str(OBD_connection.query(obd.commands.THROTTLE_POS))
    RootApp.root.ids.obd3_label.text = 'Speed (kph)\n'+str(OBD_connection.query(obd.commands.SPEED))
    driving_log.write(str(gpsd.fix.time)+','+str(gpsd.fix.latitude)+','+str(gpsd.fix.longitude)+','+str(gpsd.fix.speed)+',')
    driving_log.write(str(OBD_connection.query(obd.commands.RPM))+',')
    driving_log.write(str(OBD_connection.query(obd.commands.THROTTLE_POS))+',')
    driving_log.write(str(OBD_connection.query(obd.commands.SPEED))+'\n')


class pyOBDGame (FloatLayout):
    pass

class SplashPanel (BoxLayout):
    pass
    notifications = StringProperty()
    def add_notification (self,notification):
	self.notifications += notification
	self.notifications += '\n'

class AppActionBar(ActionBar):
    pass

class ActionMenu(ActionPrevious):
    pass

class ActionQuit(ActionButton):
    pass
    def menu(self):
        print 'App quit'
	RootApp.root.ids.notifications.text += 'Quitting\n'

	time.sleep(3)
        RootApp.stop()

class MainPanel(BoxLayout):
    pass

class AppButton(Button):
    nome_bottone = ObjectProperty(None)
    def app_pushed(self):
        print self.text, 'button', self.nome_bottone.state

class rpiOBDApp(App):

    trace_ouput = StringProperty()
    show_trace = BooleanProperty(False)
    gpsp = None

    def build_config(self, config):
        config.setdefaults('pyOBD', {
            'COMPORT': '/dev/ttyACM0',
            'RECONNATTEMPTS': '10',
	    'SERTIMEOUT':'4'
        })

    def on_start(self):

	global OBD_connection
        global RootApp
	global driving_log
        RootApp = self

        obd.logger.setLevel(obd.logging.DEBUG)
	Logger.info("pyOBDApp: Here we go")
        trace_output = "Here we go!"
#	config = self.config

	default_config_file = self.get_application_config()	
	trace_output = 'pyOBDAPP: Config=%s' % (default_config_file)
	Logger.info(trace_output)

        self.COMPORT=self.config.get("pyOBD","COMPORT")
        self.RECONNATTEMPTS=self.config.getint("pyOBD","RECONNATTEMPTS")
        self.SERTIMEOUT=self.config.getint("pyOBD","SERTIMEOUT")

        trace_output = 'pyOBDAPP: COMPORT=%s, RECONNATTEMPTS=%d, SERTIMEOUT=%d' % (
                          self.COMPORT,
                          self.RECONNATTEMPTS,
			  self.SERTIMEOUT)
        Logger.info(trace_output)

        OBD_connection = obd.Async(portstr=RootApp.COMPORT,fast=False)
        if OBD_connection.is_connected():
	    # turn down the logging 
            obd.logger.setLevel(obd.logging.WARNING)
            if OBD_connection.supports(obd.commands.RPM):
	        OBD_connection.watch(obd.commands.RPM)
            if OBD_connection.supports(obd.commands.THROTTLE_POS):
	        OBD_connection.watch(obd.commands.THROTTLE_POS)
            if OBD_connection.supports(obd.commands.SPEED):
	        OBD_connection.watch(obd.commands.SPEED)
	    OBD_connection.start()

#        obdp = ObdPoller()
#  	 Clock.schedule_once(connect_OBD,3)
	self.gpsp = GpsPoller()
	self.gpsp.start()
#	Clock.schedule_once(connect_GPS,3)

	self.root.current='mainscreen'	

	log_fname = expanduser('~')+'/Documents/driving_log.csv'
	driving_log = open(log_fname,'w')
        driving_log.write('Time (UTC),Longitude,Latitude,GPS Speed (m/s),RPM,Throttle Pos %,Speed(kph)\n')

	Clock.schedule_interval(update_measurements,1.0)


    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def on_stop(self):
	global OBD_connection
	global driving_log
	driving_log.close()
	self.gpsp.running = False
	self.gpsp.join()
        if OBD_connection.is_connected():
	    OBD_connection.stop()
	exit()

    def menu(self):
	pass


    def toggle_trace_output(self):
        self.show_trace = not self.show_trace
        if self.show_trace:
            height = self.root.height * .3
        else:
            height = 0

        Animation(height=height, d=.3, t='out_quart').start(
                self.root.ids.sv)

        if not self.show_trace:
            self.root.ids.trace_output.focus = False
            return
        self.root.ids.sv.scroll_y = 1

if __name__ == '__main__':
    rpiOBDApp().run()
