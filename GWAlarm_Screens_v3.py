"""
Original Version of Gravitational Wave Alarm Code Created by Christian Chapman

Version 3 Edited by Paulina Ulahelova
"""

#Python version 3 required
#Kivy version 2 minimum required

import math         #provides mathematical functions
import os           #provides a portable way of using operating system dependent functionality
import threading    #allows for different programs to run concurrently and to simplify the design
import time         #for handling time related tasks
import socket       #provides access to the BSD socket interface
import requests     #allows to send HTTP requests using python
import bs4          #this is required for BeautifulSoup
from bs4 import BeautifulSoup           #BeautifulSoup is a library that makes it easy to scrape information from webpages
import datetime                         #supplies classes for manipulating date and time
import numpy as np                      #for working with numerical data
from matplotlib.image import imread     #for image loading
from matplotlib.pyplot import imsave    #for image saving
import random               #for generating random actions/numbers
import lxml                 #provides an efficient way to work with XML and HTML documents
import scipy.constants      #for physical constants
import calendar             #this allows you to work with dates and perform operations with them
import tables               #used for working with hierarchical datasets in the HDF5 format
import RPi.GPIO as GPIO     #provides a way to interact with the General Purpose Input/Output pins on the Raspberry Pi
from tables import *        #provides an interface for handling structured data in HDF5 files;* means import all



#Still need to import but does not work:

#import gcn                  #for Graph Convolutional Neural Networks

#This imports custom made libraries made by Christian
#from gcn import process_gcn
from detector_monitorv2 import statusdetect
from sync_database import sync_database


import kivy                             #used to create applications with user interfaces that involve touch,gestures etc
kivy.require("2.1.0")                   #needs to use the latest version of kivy
from kivy.config import Config          #to manage the configuration parameters of the kivy framework like graphics settings
Config.set('graphics','width','1500')    #setting the width of the graphics window in pixels
Config.set('graphics','height','800')   #--- height ----
#Now we set the default fonts for our application:
Config.set('kivy','default_font',['/home/GWalarm-v3/Desktop/GW_Alarm_Code/Fonts/OpenSans-Light.ttf','/home/GWalarm-v3/Desktop/GW_Alarm_Code/Fonts/OpenSans-Regular.ttf','/home/GWalarm-v3/Desktop/GW_Alarm_Code/Fonts/OpenSans-LightItalic.ttf','/home/GWalarm-v3/Desktop/GW_Alarm_Code/Fonts/OpenSans-Bold.ttf'])

from kivy.app import App                        #serves as the base class for kivy applications
from kivy.uix.button import Button              #will allow you to use buttons
from kivy.uix.gridlayout import GridLayout      #useful for creating structured and organised layouts in Kivy applications
from kivy.uix.image import AsyncImage           #used for loading asnd displaying images asynchronously; useful for loading images from URLs
from kivy.clock import Clock                    #used for managing timing in kivy applications without relaying on python
from kivy.uix.boxlayout import BoxLayout        #this is a layout manager; used to organize widgets in a linear (horizontal or vertical) arrangement
from kivy.uix.label import Label                #this widget is used to display text in the kivy application
from kivy.graphics import Color, Rectangle      #used to set the drawing color; and to draw a rectangle on the canvas of a kivy widget
from kivy.properties import ListProperty, ObjectProperty, StringProperty, AliasProperty, DictProperty, NumericProperty  #provides a framework for creating and managing proiperties of kivy widgets
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, NoTransition, RiseInTransition               #tools for managing multiple screens in a kivy application i.e. allows you tyo switch between screens
from kivy.uix.scrollview import ScrollView      #allows for the content to be scrolled
from kivy.uix.carousel import Carousel          #allows to create interactive slideshows or image carousels; allows you to swipe through content
#from kivy.uix.popup import Popup                #can display a temporary and modal popup window on top of existing content
from kivy.uix.recycleview import RecycleView    #widget for efficiently displaying large sets of data in a scrollable and recyclable manner
from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior     #to enhance the behaviour of buttons
from kivy.uix.modalview import ModalView                                #useful when wanting to present temporary or additional information to the user without navigating to a separate screens
from kivy.animation import Animation                                    #for creating animations; to smoothly transition the properties of widgets over time creating visual effects etc.
from kivy.uix.slider import Slider                                      #allows the user to select a value from a range by moving a slider thumb along a track
from kivy.lang.builder import Builder                                   #key component for loading kivy language files (KV files);allows to separate the design of your user interface from the python code

#The following code checks for the functionality of the GPIO on Raspberry Pi
#If no LEDs/pins are being used, this is unnecessary
if os.uname()[4][:3] == 'arm':
    #We configure the graphics settings for the Raspberry Pi
    Config.set('graphics','borderless',1)
    Config.set('graphics','show_cursor',0)
    Config.set('graphics','allow_screensaver',0)

    #We import RPi.GPIO for GPIO functionality
    import RPi.GPIO as GPIO
    buzzPin=5
    testPin=6
    #We set up the GPIO pins
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(buzzPin,GPIO.OUT)
    GPIO.setup(testPin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
    GPIO.output(buzzPin,GPIO.LOW)

    '''With the following code we test if the hardware is present - it shows buzzer volume to user'''
    GPIO.output(buzzPin,GPIO.HIGH)
    time.sleep(0.5)
    if GPIO.input(testPin):
        #we configure the NeoPixel display if the hardware is present
        GPIO.output(buzzPin,GPIO.LOW)
        import board
        import neopixel
        neoPin = board.D12
        num_leds = 8
        pixels = neopixel.NeoPixel(neoPin,num_leds,brightness=0.5,pixel_order=neopixel.RGB,auto_write=False)
        print('Hardware has been detected. Enabling...')

    else:
        #this hanbdles the case when the hardware is not present
        GPIO.output(buzzPin,GPIO.LOW)
        print('No hardware detected - the hardware is not present.')
        GPIO.cleanup()
        pixels = None
        buzzPin= None
else:
    #handling the case when not on raspberry pi
    print('No hardware detected - not on RPi.')
    pixels = None
    buzzPin= None

#The following code relates to the initialization of text-to-speech functionality
#the following code doesnt work thus its commented out (originally commented out by Christian)
#import pyttsx3                                 #this is the text to speech library
#engine = pyttsx3.init()                               #initialize the TTS engine
#engine.setProperty('voice','english-north')    #set the voice to english north
#engine.setProperty('rate',130)                 #adjust the speech rate

from gtts import gTTS                           #this is a Google TextToSpeech module - allows you to convert text to speech using Google's TTS API

#The following is to check if the current working directory is different from the directory where the script is located
#If they are different, it changes the working directory to the directory where the script is located using os.chdir
#Reason for this is to ensure that the script is working in the correct directory (important for file and resource access)
if os.getcwd() != os.path.dirname(os.path.realpath(__file__)):
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

#Reload updated KV files without restarting the entire application
Builder.unload_file("GWalarm.kv")       #unloading previously loaded KV file
Builder.load_file('GWalarm_screens.kv') #load a new kv file

#Checking if we are in the right folder - preserves img functionality
if os.path.basename(os.getcwd()) != 'event_data':
    os.chdir('/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data')

#The following represents a structured data type fro describing GW observations
class Event(IsDescription):
    AlertType=StringCol(30)
    BBH=StringCol(30)           #binary black holes
    BNS=StringCol(30)           #binary neutron stars
    FAR = StringCol(30)
    GraceID=StringCol(30)
    Group=StringCol(30)
    HasNS=StringCol(30)
    HasRemnant=StringCol(30)
    Instruments = StringCol(30)
    MassGap=StringCol(30)
    NSBH=StringCol(30)          #neutron star black hole binary
    Terrestrial = StringCol(30)
    skymap=StringCol(30)
    DetectionTime=StringCol(30)
    UpdateTime=StringCol(30)
    MassGap=StringCol(30)
    Distance=StringCol(30)
    Revision=StringCol(30)

#Defining global variables
global flag
global main_flag
global newevent_flag
global rebuild_flag
#We initialize flags/indicators to a default state:
flag = 0
main_flag=0
newevent_flag=0
rebuild_flag=0

#HisColLabel is a widget class combining the behaviour of a toggle button, allowing it to be pressed and released while label provides the behaviour of a text label
class HisColLabel(ToggleButtonBehavior,Label):
    #the following is to store various and reference various data associated with the widget
    sorttype=ObjectProperty()
    newsort=ObjectProperty()
    names=ObjectProperty()
    specialnames=ObjectProperty()
    lookout = ObjectProperty()
    backcolors=ObjectProperty()
    primed=NumericProperty()
    imgsource=ObjectProperty()

    #this function is called when the widget is pressed
    def on_press(self):
        self.primed=1
        #assuming a parent-child relationship in a kivy layout
        for child in self.parent.children:
            if child.primed != 1:
                child.imgsource='./neutral.png'
        self.primed=0
    #this is called upon when the state of the widget changes (when its toggled):
    def on_state(self,widget,value):
        Clock.schedule_once(lambda dt:self.on_state_for_real(widget,value),0)
    #this is called after a delay:
    def on_state_for_real(self,widget,value):
        global flag
        flag = 1
        if value == 'down':
            self.newsort = self.sorttype+' Descending'
            self.imgsource='./ascending.png'

        else:
            self.newsort = self.sorttype+' Ascending'
            self.imgsource='./descending.png'
        t2 = threading.Thread(target=historyUpdatev2,args=(App.get_running_app().root.get_screen('history').ids.rv,
                                                         self.names,self.specialnames,self.lookout,
                                                         self.backcolors,self.newsort,App.get_running_app().root.get_screen('history').current_key),daemon=True)
        t2.start()


#The following is designed for displaying information related to the events
class EventInfoHeader(GridLayout):
    paramdict=ObjectProperty()
    var=NumericProperty(1)
    speak=NumericProperty(0)
    speaker_color=ObjectProperty()      #to control the color of the speaker

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.finish_init,0)     #called after a delay of 0 seconds
    #start a new thread:
    def finish_init(self,dt):
        t=threading.Thread(target=self.read_event_params)
        t.start()

    def read_event_params(self):
        global main_flag
        while main_flag == 0:
            while self.var == 0 and main_flag == 0:
                stats = []
                lookoutfor = ['BBH','BNS','NSBH','MassGap','Terrestrial']
                for name in lookoutfor:
                    if '<' in self.paramdict[name]:
                        stats.append(0)
                    else:
                        stats.append(float(self.paramdict[name].strip('%')))
                ev_type= lookoutfor[np.argmax(stats)]

                if ev_type == 'Terrestrial':
                    processType = 'False Alarm'
                elif ev_type == 'BNS':
                    processType = 'Binary Neutron Star merger'
                elif ev_type == 'BBH':
                    processType = 'Binary Black Hole merger'
                elif ev_type == 'MassGap':
                    processType = 'MassGap event'
                elif ev_type == 'NSBH':
                    processType = 'Neutron Star Black Hole merger'

                far = self.paramdict['FAR'].split()
                if len(far) != 1:
                    far[2] = "{0:.0f}".format(float(far[2]))
                    far = " ".join(far)
                else:
                    far = far[0]
                dist = float(self.paramdict['Distance'].split()[0])
   #             distly = (2/3/72000)*(1-1/(1+72000*dist/scipy.constants.c)**1.5)
                distly = dist*3.262e+6

   #             print(distly)

                insts = self.paramdict['Instruments']
                insts_out =''
                if 'V1' in insts:
                    insts_out+='Virgo, '
                if 'L1' in insts:
                    insts_out+='LIGO Livingston, '
                if 'H1' in insts:
                    insts_out+='LIGO Hanford, '
                processed = insts_out.split(',')[0:-1]
                insts_formed = ''
                for i,elem in enumerate(processed):
                    if i == len(processed)-1 and len(processed) != 1:
                        insts_formed+= ' and '+ elem
                    else:
                        insts_formed+= elem+','

                date = datetime.datetime.strptime(self.paramdict['DetectionTime'].split()[0],'%Y-%m-%d')
                ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
                dayname = calendar.day_name[date.weekday()]
                month = calendar.month_name[date.month]
                dayno = ordinal(date.day)
                DateToken = ' on ' +dayname + ' the ' + dayno + ' of ' + str(month) + ' ' + str(date.year)

                if len(self.children) == 4:
                    #This is a new event popup
                    NewOrNotToken = 'A new event has been'
                    DateToken = ''
                else:
                    NewOrNotToken = 'This event was'
                InitialToken = NewOrNotToken+ ' detected by '+insts_formed+ DateToken + ' . '
                EventTypeToken = 'The event is most likely to be a ' + processType + ', with a probability of ' + "{0:.0f}".format(float(self.paramdict[ev_type][:-1])-1) + ' percent. '
                FalseAlarmToken = 'The false alarm rate of the event is ' + far +'. '
                DistanceLookBackToken = 'It is approximately ' + oom_to_words(dist,'Megaparsecs',tts='on') + ' away, which is equivalent to a lookback time of '+ oom_to_words(distly,'years',tts='on')+'. '
                if '<' not in self.paramdict['HasRemnant']:
                    if float(self.paramdict['HasRemnant'][:-1]) > 10:
                        HasRemnantToken = 'If astrophysical, the event may have left a remnant. The probability of this is '+ str(int(float(self.paramdict['HasRemnant'][:-1])))+' percent.'
                        tokens=[InitialToken,EventTypeToken,FalseAlarmToken,DistanceLookBackToken,HasRemnantToken]
                    else:
                        tokens=[InitialToken,EventTypeToken,FalseAlarmToken,DistanceLookBackToken]
                else:
                    tokens=[InitialToken,EventTypeToken,FalseAlarmToken,DistanceLookBackToken]

                #the following is to render each part of the information as audio:
                renderthreads = []
                def render_audio(token,num):
#                    print(token)
                    tts=gTTS(token)
                    tts.save('readout'+num+'.mp3')

                for k,token in enumerate(tokens):
        #            engine.say(token)
        #            engine.runAndWait()
                    t=threading.Thread(target=render_audio,args=(token,str(k)))
                    renderthreads.append(t)
                    t.start()
                for t in renderthreads:
                    t.join()
                maximum = k
                while self.speak == 0 and main_flag == 0 and self.var == 0:
                    time.sleep(1)
                while self.speak == 1 and main_flag == 0 and self.var == 0:
                    for i in range(maximum+1):
                        if self.var == 0:
                            os.system("mpg321 --stereo readout"+str(i)+".mp3")          #the audio is played using the rendered audio using mpg321
                        else:
                            self.speak = 0
                            break
                        self.speak = 0
                    break
            time.sleep(1)
        print('Speech thread closing...')
    #the following initiates speech playback
    def read_aloud(self):
        self.speaker_color=[0.8,0.8,0.8,0.4]
        self.var=0
        self.speak=1

    #the following resets the speaker color
    def speaker_back(self):
        self.speaker_color=[0,0,0,0]

class HistoryScreenv2(Screen):
    names = ObjectProperty()
    current_key = ObjectProperty()

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        if os.path.basename(os.getcwd()) != "event_data":
            try:
                os.chdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")
            except:
                os.mkdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")
                os.chdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")

        while True:
            try:
                h5file = open_file("Event Database",mode="r",title="eventinfo")
                break
            except:
                print("file in use... trying again in 5s")
                time.sleep(5)
        try:
            h5file.root.events
        except NoSuchNodeError:
            time.sleep(5)
            pass
        #grab a table, it doesn't matter which one!
        x=0
        for table in h5file.iter_nodes(where="/events",classname="Table"):
            tables=table
            if x==0:
                break

        def receive():
            hostnames=["209.208.78.170 Atlantic_2","45.58.43.186 Atlantic_3","50.116.49.68 Linode", "68.169.57.253 eApps"]
            i=0
            import logging
            log = logging.getLogger('gcn.listener')
            handle = logging.StreamHandler()
            handle.setLevel(logging.INFO)
            log.addHandler(handle)
            log.setLevel(10)
            try:
                print('Connecting to '+hostnames[i].split()[1]+'...')
                gcn.listen(host=hostnames[i].split()[0],handler=process_gcn,log=log)
            except socket.timeout:
                print('stopped')
        t4 = threading.Thread(target=receive,daemon=True,name='gcnthread')
        t4.start()

        self.names = tables.colnames
#        num_events = len(h5file.list_nodes(where="/events",classname="Table"))
        h5file.close()
        specialnames=['GraceID','Distance','Instruments','FAR','UpdateTime']

        lookoutfor = ['BBH','BNS','NSBH','MassGap','Terrestrial']
        backcolors = [[202/255,214/255,235/255,1],[179/255,242/255,183/255,1],
                      [238/255,242/255,179/255,1],[231/255,179/255,242/255,1],
                      [242/255,179/255,179/255,1]]

        for child in self.ids.HisCols.children:
            child.names = self.names
        t2 = threading.Thread(target=historyUpdatev2,args=(self.ids.rv,self.names,specialnames,lookoutfor,backcolors,'Time Descending'),daemon=True)
        t2.start()

    #define a function for updating the database and history
    #then create a button and a popup for confirming database update
    def stupid(obj):
        def wait_and_close(pop):
            global flag
            flag = 1
            pop.content.unbind(on_press=wait_and_close)
            pop.content.text='Updating. \nPlease wait.'
            Clock.schedule_once(lambda dt:sync_database(),0)
            his = App.get_running_app().root.get_screen('history')
            histhread = threading.Thread(target=historyUpdatev2,args=(his.ids.rv,
                                                         his.names,his.specialnames,his.lookoutfor,
                                                         his.backcolors,'Time Descending'),daemon=True)
            histhread.start()
            pop.dismiss()
        content = Button(text='Update Database \n(takes time)',halign='center')
        confirm = Popup(title='Are you sure?',content=content,size_hint=(0.4,0.4))
        content.bind(on_press=lambda arg: wait_and_close(confirm))
        confirm.open()

def oom_to_words(inputval,unit,tts='off'):
    far_oom = int(math.log10(inputval))
    far_token = ''
    inputval = float("{0:.2f}".format(inputval))

    #Adjust the input value for the text-to-speech (TTS) mode
    if tts == 'on':
        if far_oom >= 3 and far_oom < 6:
            far_token = 'Thousand'
        inputval = round(inputval/10**far_oom)*10**far_oom

    #Determine the appropriate magnitude token (thousand, million, etc..)
    if far_oom >= 6 and far_oom < 9:
        far_token = 'Million'
    elif far_oom >= 9 and far_oom < 12:
        far_token = 'Billion'
    elif far_oom >= 12 and far_oom < 15:
        far_token='Trillion'
    elif far_oom >= 15 and far_oom < 18:
        far_token ='Quadrillion'
    elif far_oom >= 18 and far_oom < 21:
        far_token = 'Quintillion'
    elif far_oom >= 21 and far_oom < 24:
        far_token = 'Sextillion'
    elif far_oom >= 24:
        far_token = 'Septillion'
    far_token+= ' '+unit
    far_rem_oom = far_oom % 3
    far_div_oom = far_oom - far_rem_oom
#    print(inputval/(10**far_div_oom) + far_token)
    #construct the return string based on whether tts mode is on or off
    if tts=='on':
        return_string = str(int(float("{0:.2f}".format(inputval/(10**far_div_oom))))) +' '+ far_token
    else:
        return_string = str(float("{0:.2f}".format(inputval/(10**far_div_oom)))) +' '+ far_token
    return return_string

def process_FAR(FAR,tts='off'):
    #ensure FAR is treated as a float
    if type(FAR) is not float:
        FAR = float(FAR)
    #calculate events per year and the reciprocal (one in how many years)
    per_yr = FAR*scipy.constants.year
    #if per_yr <= 1:
    oneinyr = 1/per_yr
    #else:
    #    oneinyr = per_yr

#format and return the result
    val = 'One every ' + oom_to_words(oneinyr,'years',tts)
    return val


class KeyLabel(ToggleButtonBehavior,GridLayout):
    primed=NumericProperty()
    #invoke the method when the KeyLabel is pressed
    def on_press(self):
        self.primed=1
        #iterate over parent's children to reset the background color of other keylabels
        for child in self.parent.children:
            if 'KeyLabel' in str(child):
                if child.primed != 1:
                    child.back_color=[0.9,0.9,0.9,1]

    #this method is invoked when the state (down or up) of the keylabel changes
    def on_state(self,widget,value):
        #schedule the execution with delay of 0 seconds
        Clock.schedule_once(lambda dt: self.on_state_for_real(widget,value),0)

    def on_state_for_real(self,widget,value):
        #retrieve the history screen of the running kivy app
        his = App.get_running_app().root.get_screen('history')

        def up(self):
            #reset background color
            self.back_color=[0.9,0.9,0.9,1]
            if self.primed == 0:
                return
            global flag
            flag = 1

            histhread = threading.Thread(target=historyUpdatev2,args=(his.ids.rv,
                                                         his.names,his.specialnames,his.lookoutfor,
                                                         his.backcolors,his.current_sort),daemon=True)
            histhread.start()
            #update the current_key attribute
            App.get_running_app().root.get_screen('history').current_key = 'None'
            self.primed=0

        #nested function to handle actions when the state is down
        def down(self):
            #adjust background color
            self.back_color=[195/255,209/255,219/255,1]
            #set a global flag and start a thread for history update
            global flag
            flag = 1
            histhread = threading.Thread(target=historyUpdatev2,args=(his.ids.rv,
                                                         his.names,his.specialnames,his.lookoutfor,
                                                         his.backcolors,his.current_sort,self.key),daemon=True)

            histhread.start()
            #update the current_key attribute again
            App.get_running_app().root.get_screen('history').current_key = self.key
            self.primed=0
        #if the state is down schedule the execution of down with a delay of 0 seconds
        if value == 'down':
            Clock.schedule_once(lambda dt: down(self),0)
        else:
            #if the state is up
            Clock.schedule_once(lambda dt: up(self),0)

def historyUpdatev2(rv,names,specialnames,lookoutfor,backcolors,sorttype='Time Descending',keytype = 'None'):
    print('Begin History update')
    '''An important function that is responsible for populating and repopulating the history screen.'''

    global flag
    global main_flag
    #reset stop flag
    main_flag=0
    #check if the current working directory is event_data, if not change it
    if os.path.basename(os.getcwd()) != "event_data":
        try:
            os.chdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")
        except:
            os.mkdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")
            os.chdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")

    #initial check to ensure file exists with necessary groupings
    while True:
        try:
            h5file = open_file("Event Database",mode="r",title="eventinfo")
            break
        except:
            print("file in use... trying again in 5s")
            time.sleep(5)
    #check if the events node exists in the HDF5 file
    try:
        h5file.root.events
    except NoSuchNodeError:
        time.sleep(5)
        pass
    h5file.close()

    #initial stat
    stats = os.stat("./Event Database")
    lastaccess= stats.st_mtime
    first = 1
    while True:
        stats = os.stat("./Event Database")
        access = stats.st_mtime
        if access != lastaccess or first == 1:
            lastaccess=access

            while True:
                try:
                    h5file = open_file("Event Database",mode="r",title="eventinfo")
                    break
                except:
                    print("file in use... trying again in 5s")
                    time.sleep(5)

            #get all tables from the events node
            tables = [table for table in h5file.iter_nodes(where="/events",classname="Table")]
            sort_vars = []

            #extract graceID from the data if available
            widgetids = []
            if rv.data:
                nomlist = rv.data[0]['namelist']
                idindex = nomlist.index('GraceID')
                widgetids= [elem['row'][idindex] for elem in rv.data]

            '''Iterate through all events, re-drawing row-by-row the history viewer'''
            def update_sort_type():
                App.get_running_app().root.get_screen('history').current_sort=sorttype
            Clock.schedule_once(lambda dt: update_sort_type())

            #soret the tables based on the specified sorting type
            for table in tables:
                if 'EventSimulation' in table.name:
                    continue
                try:
                    row=table[-1]
                except:
                    print('Empty table error for event:',table.name+'. Rebuilding the file. This may take a while...')
                    h5file.close()
                    global rebuild_flag
                    rebuild_flag = 1
                    pop = RebuildPop()
                    pop.open()
                    sync_database()
                    rebuild_flag = 0
                    return

                if 'Time' in sorttype:
                    sort_vars.append(row['UpdateTime'].decode().split()[0])
                elif 'Distance' in sorttype:
                    sort_vars.append(float(row['Distance'].decode().split()[0]))
                elif 'GraceID' in sorttype:
                    string = str(row['GraceID'].decode())
                    sort_vars.append(int(re.sub("[a-zA-Z]","",string)))
                elif 'FAR' in sorttype:
                    sort_vars.append(float(row['FAR'].decode()))#.split()[2]))
                elif 'Instruments' in sorttype:
                    sort_vars.append(row['Instruments'].decode())
            if sort_vars != []:
                if 'Descending' in sorttype:
                    try:
                        tables = [x for _,x in reversed(sorted(zip(sort_vars,tables)),key=len[0])]
                    except TypeError:
                        tables2=[]
                        sort_indexes = reversed(np.argsort(np.array(sort_vars)))
                        for index in sort_indexes:
                            tables2.append(tables[index])
                        tables=tables2
                elif 'Ascending' in sorttype:
                    try:
                        tables = [x for _,x in (sorted(zip(sort_vars,tables)))]
                    except TypeError:
                        tables2=[]
                        sort_indexes = (np.argsort(np.array(sort_vars)))
                        for index in sort_indexes:
                            tables2.append(tables[index])
                        tables=tables2
            new_data = []
            for i,table in enumerate(tables):
                if 'EventSimulation' in table.name:
                    continue

                to_add_to_data={}
                row = table[-1]

                stats = []
                for name in lookoutfor:
                    stats.append(float(row[name].decode().strip('%')))

                if keytype != 'None':
                    if keytype not in lookoutfor[np.argmax(stats)]:
                        continue
                orderedrow = []
                to_add_to_data['namelist']=names
                to_add_to_data['name']=row['GraceID'].decode()
                for key in names:
                    if key == 'FAR':
                        val = process_FAR(float(row[key].decode()))
                        orderedrow.append(val)
                    elif key in lookoutfor:
                        if float(row[key].decode()[:-1]) < 0.1:
                            orderedrow.append('<0.1%')
                        else:
                            orderedrow.append(row[key].decode())
                    else:
                        orderedrow.append(row[key].decode())
                to_add_to_data['row'] = orderedrow
                if row['GraceID'].decode() not in widgetids:
                    if first == 0:
                        if row['Revision'].decode() == '1':
                            '''NEW EVENT!!!'''
                            global newevent_flag
                            if newevent_flag == 0:
                                newevent_flag=1

                for j in range(len(specialnames)):
                    string=row[specialnames[j]]
                    if 'Distance' in specialnames[j]:
                        to_add_to_data['text'+str(j)] = ' '.join(string.decode().replace('+-',u'\xb1').split()[:-1])
                    elif 'FAR' in specialnames[j]:
                        to_add_to_data['text'+str(j)] = ' '.join(process_FAR(float(string.decode())).split()[2:])
                    elif 'Update' in specialnames[j]:
                        to_add_to_data['text'+str(j)] = string.decode().split('at')[0].rstrip()
                        to_add_to_data['text'+str(j+1)]=string.decode().split('at')[1].rstrip()
                    else:
                        to_add_to_data['text'+str(j)] = string.decode()
                to_add_to_data['bgcol'] = backcolors[np.argmax(stats)]
                new_data.append(to_add_to_data)

                if i == 0 and sorttype == 'Time Descending':
                    rv.winner = lookoutfor[np.argmax(stats)]
                    print(rv.winner)
            rv.data = new_data

            print('Event History Updated...')


            def update_notif(val):
                if pixels and val not in App.get_running_app().root.get_screen('main').notif_light_current:
                    type_notif(val)
                App.get_running_app().root.get_screen('main').notif_light_current=val

            Clock.schedule_once(lambda dt:update_notif(rv.winner),0)


            h5file.close()
            #reset the flag
            first = 0

        waittime = 5
        i=0
        while i < waittime:
            if flag ==1:
                print('History Thread restarting...')
                flag=0
                return
            if main_flag ==1:
                print('history thread closing...')
                return
            i+=0.2
            time.sleep(0.2)

############################################################################################line 706
########needs comments!!!!!!!!!!!!

class SkyPop(Screen):
    imgsource=StringProperty()

class DevPop(Screen):
    pass

class InfoPop(Screen):
    namelist=ObjectProperty()
    row=ObjectProperty()

    def update_skymap(self):
        self.manager.get_screen('sky').imgsource=self.rowdict['skymap']
        self.manager.current = 'sky'
    def gloss_open(self):
        descdict = {'GraceID': 'Identifier in GraceDB',
            'Instruments': 'List of instruments used in analysis to identify this event',
            'FAR': 'False alarm rate for GW candidates with this strength or greater',
            'Group': 'Data analysis working group',
            'BNS': 'Probability that the source is a binary neutron star merger (both objects lighter than 3 solar masses)',
            'NSBH': 'Probability that the source is a neutron star-black hole merger (primary heavier than 5 solar masses, secondary lighter than 3 solar masses)',
            'BBH': 'Probability that the source is a binary black hole merger (both objects heavier than 5 solar masses)',
            'Terrestrial': 'Probability that the source is terrestrial (i.e., a background noise fluctuation or a glitch)',
            'HasNS': 'Source classification: binary neutron star (BNS), neutron star-black hole (NSBH), binary black hole (BBH), MassGap, or terrestrial (noise)',
            'HasRemnant': 'Probability that at least one object in the binary has a mass that is less than 3 solar masses',
            'Distance':'Posterior mean distance to the event (with standard deviation) in MPc',
            'DetectionTime':'The mean date & time at which the event was first detected',
            'UpdateTime': "The date & time of the most recent update to this event's parameters",
            'MassGap':"Compact binary systems with at least one compact object whose mass is in the hypothetical 'mass gap' between neutron stars and black holes, defined here as 3-5 solar masses.",
            'Revision':"The number of revisions (updates) made to this event's parameters"}
        content = GridLayout(rows=2)
        _glossary = Glossary(size_hint_y=0.9)
        descdata=[]
        sortedkeys=[]
        for key in descdict:
            sortedkeys.append(key)
        sortedkeys.sort()
        for key in sortedkeys:
            descdata.append({'nom':key,'desc':descdict[key]})
        _glossary.data = descdata
        content.add_widget(_glossary)
        but = Button(text='Done',size_hint_y=0.1)
        content.add_widget(but)
        pop = Popup(title='Glossary',content=content,size_hint=(0.25,1),pos_hint={'x':0,'y':0})
        but.bind(on_press=pop.dismiss)
        pop.open()
    def on_pre_enter(self):
        self.var = 0
        self.speak =0

    def on_leave(self):
        if len(App.get_running_app().root.get_screen('historypop').ids.header.children) == 4:
            App.get_running_app().root.get_screen('historypop').ids.header.remove_widget(App.get_running_app().root.get_screen('historypop').ids.header.children[0])
            App.get_running_app().root.get_screen('historypop').ids.header.do_layout()
        self.var = 1
        App.get_running_app().root.transition = SlideTransition()

class GlossDefLabel(Label):
    nom=ObjectProperty()
    desc=ObjectProperty()

class Glossary(RecycleView):
    pass

class EventContainer(ButtonBehavior,GridLayout):
    name=ObjectProperty()
    namelist=ListProperty(['test1','test2'])
    row = ListProperty(['test1','test2'])
    pop = ObjectProperty()
    img= StringProperty()
    text0=StringProperty('tobereplaced')
    text1=StringProperty('tobereplaced')
    text2=StringProperty('tobereplaced')
    text3=StringProperty('tobereplaced')
    text4=StringProperty('tobereplaced')
    text5=StringProperty('tobereplaced')

    def details(self):
        App.get_running_app().root.get_screen('historypop').namelist = self.namelist
        App.get_running_app().root.get_screen('historypop').row = self.row
#            pop.background_color=self.bgcol
#            pop.background_color[3] = 1
        App.get_running_app().root.transition = SlideTransition(direction='right')
        App.get_running_app().root.current='historypop'
        App.get_running_app().root.transition = NoTransition()

def statusupdate(obj):
    global main_flag
    main_flag=0

    if pixels:
        def color_all(color):
            for i in range(2,6):
                pixels[i] = color
            pixels.show()
            time.sleep(1)

        startup_cycle = ((255,0,0),(0,255,0),(0,0,255))
        for col in startup_cycle:
            color_all(col)

        print('Detector status LED init complete...')
    while True:
        data,stats,names = statusdetect()

        for i,elem in enumerate(data):
            setattr(obj,'det'+str(i+1)+'props',elem)

        '''LED CONTROL'''
        if pixels:
            #order = ['GEO 600','LIGO Livingston','LIGO Hanford','Virgo']    # prototype version LED configuration
            order = ['Virgo','LIGO Hanford','LIGO Livingston','GEO 600']
            statindexes = [names.index(item) for item in order]
            stats = [x for _,x in sorted(zip(statindexes,stats))]

            for i,stat in enumerate(stats):
                if stat == 0:
                    #red
                    pixels[i+2] = (255,0,0)
                if stat == 1:
                    #orange
                    pixels[i+2] = (228,119,10)
                if stat == 2:
                    #green
                    pixels[i+2] = (17,221,17)
                if stat == 3:
                    #yellow
                    pixels[i+2] = (0,0,0)
            pixels.show()

        waittime = 30
        i = 0
        while i < waittime:
            if main_flag == 1:
                print('Status Thread closing...')
                return
            i+=1
            time.sleep(1)

#################################################THE broken non existent URL link
#############need to find a existent page to replace
def plotupdate(obj):
    global main_flag
    main_flag=0
    while True:
        print('Plot updating...')

        if os.path.basename(os.getcwd()) != 'event_data':
            try:
                os.chdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")
            except:
                os.mkdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")
                os.chdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")
        #formulate the url to get today's
        date = datetime.datetime.today()
        sort_date = [str(date.year),str(date.month).zfill(2),str(date.day).zfill(2)]
        datestring = sort_date[0]+sort_date[1]+sort_date[2]
        url = "https://www.gw-openscience.org/detector_status/day/"+datestring+"/"
        url2 = "https://www.gw-openscience.org/detector_status/day/"+datestring+"/instrument_performance/analysis_time/"
        #grab the soup and parse for links + descripts
        date = datetime.datetime.today()
        try:
            sort_date = [str(date.year),str(date.month).zfill(2),str(date.day).zfill(2)]
            datestring = sort_date[0]+sort_date[1]+sort_date[2]
            url = "https://www.gw-openscience.org/detector_status/day/"+datestring+"/"
            url2 = "https://www.gw-openscience.org/detector_status/day/"+datestring+"/instrument_performance/analysis_time/"
            try:
                resp=requests.get(url)
            except:
                print ('ERROR: Issues requesting website:  ' + url + '\n')
                resp=''
                pass
            if hasattr(resp, 'text'):
                r = resp.text
            else:
                r = resp
            while True:
                if 'Not Found' in str(r):
                    date = date - datetime.timedelta(days=1)
                    sort_date = [str(date.year),str(date.month).zfill(2),str(date.day).zfill(2)]
                    datestring = sort_date[0]+sort_date[1]+sort_date[2]
                    url = "https://www.gw-openscience.org/detector_status/day/"+datestring+"/"
                    url2 = "https://www.gw-openscience.org/detector_status/day/"+datestring+"/instrument_performance/analysis_time/"


                '''check the first link to make sure it actually loads - problem occurs at midnight GMT'''
                try:
                    resp=requests.get(url)
                except:
                    print ('ERROR: Issues requesting website:  ' + url + '\n')
                    resp=''
                    pass
                if hasattr(resp, 'text'):
                    r = resp.text
                else:
                    r = resp
                soup=BeautifulSoup(r,"lxml")

                try:
                    for link in soup.find_all("a"):
                        linkstr = str(link.get("href"))
                        if 'png' in linkstr:
                            filepath = 'Detector_Plot_0.png'
                            source='https://www.gw-openscience.org'+linkstr
                            os.system("curl --silent -0 "+ source+ ' > ' + filepath)
                            img = imread("./"+filepath)
                            break
                    break
                except:
                    r+='Not Found'
                    continue
            soup=BeautifulSoup(r,"lxml")
            try:
                resp2 = requests.get(url2)
            except:
                print ('ERROR: Issues requesting website:  ' + url2 + '\n')
                resp2=''
                pass
            if hasattr(resp, 'text'):
                r2 = resp2.text
            else:
                r2 = resp2
            soup2 = BeautifulSoup(r2,"lxml")
        except:
            print("URL Error: URL to the Range plots is broken : check online")
        descripts=[]
        paths=[]
        i=0
        for link in soup.find_all("a"):
            linkstr = str(link.get("href"))
            if 'png' in linkstr:
                filepath = 'Detector_Plot_'+str(i)+'.png'
                source='https://www.gw-openscience.org'+linkstr
                os.system("curl --silent -0 "+ source+ ' > ' + filepath)
                descripts.append(str(link.get("title")))
                paths.append(filepath)
                i+=1
        for link in soup2.find_all("a"):
            linkstr=str(link)
            if 'png' and 'COINC' in linkstr:
                filepath = 'Detector_Plot_'+str(i)+'.png'
                descripts.append(str(link['title']))
                source= 'https://www.gw-openscience.org'+str(link.get("href"))
                os.system("curl --silent -0 "+ source+ ' > ' + filepath)
                paths.append(filepath)

                img = imread("./"+filepath)
                cropimg = img[50:550,100:1200,:]
                imsave("./Detector_Plot_3.png",cropimg,format='png')
                i+=1
                break

        obj.imgsources = paths
        obj.descs = descripts

        #Reload the images
        for child in obj.ids:
            if 'img' in str(child):
                getattr(obj.ids,child).ids.image.reload()

        #Reload the duty cycle image
        for child in App.get_running_app().root.get_screen('status').ids:
            if 'img' in str(child):
                getattr(App.get_running_app().root.get_screen('status').ids,child).reload()

        waittime=900
        i=0
        while i < waittime:
            if main_flag == 1:
                print('Plot Thread closing...')
                return
            i+=5
            time.sleep(5)


def type_notif(e_type,flasher='off'):
    def color(event_type):
        if event_type == 'Terrestrial':
            pixels[6] = (255,80,70)
        elif event_type == 'NSBH':
            pixels[6] = (255,255,25)
        elif event_type == 'BBH':
            pixels[6] = (122,180,255)
        elif event_type == 'MassGap':
            pixels[6] = (245,66,230)
        elif event_type == 'BNS':
            pixels[6] = (102,255,112)
        pixels.show()
    if flasher == 'on':
        duration=10
        step=0.5
        j = 0
        while j < duration:
            color(e_type)
            time.sleep(step)
            pixels[6]=(0,0,0)
            pixels.show()
            time.sleep(step)
            j+=step
        color(e_type)
    else:
        color(e_type)

def buzz(times,step):
    i=0
    while i < times:
        GPIO.output(buzzPin,GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(buzzPin,GPIO.LOW)
        time.sleep(0.05)
        GPIO.output(buzzPin,GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(buzzPin,GPIO.LOW)
        time.sleep(0.05)
        GPIO.output(buzzPin,GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(buzzPin,GPIO.LOW)
        time.sleep(0.05)
        GPIO.output(buzzPin,GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(buzzPin,GPIO.LOW)
        i+=1
        time.sleep(step)


class VolSlider(BoxLayout):
    def changevol(self,value):
        val = self.ids.slider.value
        if pixels:
            os.system("amixer set PCM "+str(val)+"%")


class MainScreenv2(Screen):
    notif_light_var=NumericProperty(0)
    notif_light_current = StringProperty()

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        event_waiting_thread = threading.Thread(target=self.event_waiting)
        event_waiting_thread.start()

    def simulate(self):
        global newevent_flag
        if newevent_flag == 0:
            #don't start if it's not safe

            def process():
                payload=open("EventDemonstration.xml",'rb').read()
                string='Thisisaneventsim'
                root=lxml.etree.fromstring(payload)
                payload+=string.encode()
                process_gcn(payload,root)
                global newevent_flag
                newevent_flag=1
                while newevent_flag == 1:
                    time.sleep(0.5)
                self.ids.eventsendbutton.text='Generate\ntest event'


            t = threading.Thread(target=process)
            t.start()
            self.manager.transition=NoTransition()
            self.manager.current='main'
            Clock.schedule_once(lambda dt: t.join(),0)
        else:
            content = Label(text='The event is coming, be patient!')
            popu = Popup(title="It's on the way...",content=content)
            popu.open()
            Clock.schedule_interval(lambda dt: popu.dismiss(),5)

    def event_waiting(self):
        '''New event popup handler'''
        global newevent_flag
        global main_flag
        newevent_flag=0
        main_flag=0

        while True:
            while True:
                #check for the flag once per minute (same rate the file is polled)
                if newevent_flag == 1:
                    #skip a level up to execute the rest of the loop, then back to waiting.
                    print('New event has been detected!!')
                    break
                if main_flag == 1:
                    print('Event listener #2 closing...')
                    #return takes you right out of the function
                    return
                time.sleep(5)

            #Close all active popups - prevents crashes if left unattended for a while.
            if 'historypop' in App.get_running_app().root.current:
                App.get_running_app().root.transition = NoTransition()
                App.get_running_app().root.get_screen('historypop').ids.but1.trigger_action(duration=0)
                App.get_running_app().root.transition = SlideTransition()

            #Read in the new event
            if os.path.basename(os.getcwd()) != "event_data":
                try:
                    os.chdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")
                except:
                    os.mkdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")
                    os.chdir("/home/GWalarm-v3/Desktop/GW_Alarm_Code/event_data")
            while True:
                try:
                    h5file = open_file("Event Database",mode="a",title="eventinfo")
                    break
                except:
                    print("file in use... trying again in 5s")
                    time.sleep(5)
            try:
                h5file.root.events
            except NoSuchNodeError:
                time.sleep(5)
                pass

            tabs=[tab.name for tab in h5file.list_nodes("/events")]
            if 'EventSimulation' not in tabs:
                eventid = list(reversed(sorted(tabs)))[0]
            else:
                eventid = 'EventSimulation'
            for tab in h5file.list_nodes("/events"):
                if tab.name == eventid:
                    new_event_table=tab
            namelist = new_event_table.colnames
            new_event_row = new_event_table[-1]
            orderedrow = []
            for key in namelist:
                if key == 'FAR':
                    v=process_FAR(new_event_row[key].decode())
                    orderedrow.append(v)
                else:
                    orderedrow.append(new_event_row[key].decode())
#            name_row_dict = dict(zip(namelist,orderedrow))

            stats = []
            lookoutfor = ['BBH','BNS','NSBH','MassGap','Terrestrial']
            for name in lookoutfor:
                stats.append(float(new_event_row[name].decode().strip('%')))
            winner = lookoutfor[np.argmax(stats)]
            if pixels:
                t = threading.Thread(target=type_notif,args=(winner,'on'))
                t.start()

            if  eventid == 'EventSimulation':
                h5file.remove_node("/events",'EventSimulation')
            h5file.close()

            newevent_flag=0

            App.get_running_app().root.get_screen('historypop').namelist = namelist
            App.get_running_app().root.get_screen('historypop').row = orderedrow
            extralabel = Label(text='[b]NEW EVENT[/b]',markup=True,font_size=20,halign='left',color=[0,0,0,1],size_hint_x=0.2)
            App.get_running_app().root.get_screen('historypop').ids.header.add_widget(extralabel)

            '''Now that we're ready, sound the alarms'''
            if buzzPin is not None:
                buzzthread = threading.Thread(target=buzz,args=(3,1))
                buzzthread.start()
            if pixels:
                notifthread = threading.Thread(target=self.notifier)
                notifthread.start()

            App.get_running_app().root.current = 'historypop'
            App.get_running_app().root.get_screen('historypop').ids.header.speak = 1

    def notifier(self):
        self.notif_light_var=1
        rand1 = round(random.random()*255)
        rand2 = round(random.random()*255)
        rand3 = round(random.random()*255)

        while self.notif_light_var==1:
            pixels[7] = (rand1,rand2,rand3)
            pixels.show()
            time.sleep(0.005)
            rand1+=3
            rand2+=2
            rand3+=1
            if rand1 > 255:
                rand1-=255
            if rand2 > 255:
                rand2 -= 255
            if rand3 > 255:
                rand3 -= 255

        pixels[7] = (0,0,0)
        pixels.show()

    def notif_off(self):
        self.notif_light_var = 0
#        print(self.notif_light_current)
        if pixels:
            type_notif(self.notif_light_current)

    def read_event_params(self,paramdict,ev_type):
        if ev_type == 'Terrestrial':
            processType = 'False Alarm'
        elif ev_type == 'BNS':
            processType = 'Binary Neutron Star merger'
        elif ev_type == 'BBH':
            processType = 'Binary Black Hole merger'
        elif ev_type == 'MassGap':
            processType = 'MassGap event'
        elif ev_type == 'NSBH':
            processType = 'Neutron Star Black Hole merger'

        far = float(paramdict['FAR'])

        dist = float(paramdict['Distance'].split()[0])
        distly = dist*3.262e+6

        insts = paramdict['Instruments']
        insts_out =''
        if 'V1' in insts:
            insts_out+='Virgo, '
        if 'L1' in insts:
            insts_out+='LIGO Livingston, '
        if 'H1' in insts:
            insts_out+='LIGO Hanford, '
        processed = insts_out.split(',')[0:-1]
        insts_formed = ''
        for i,elem in enumerate(processed):
            if i == len(processed)-1 and len(processed) != 1:
                insts_formed+= ' and '+ elem
            else:
                insts_formed+= elem

        InitialToken = 'A new event has been detected by '+insts_formed+' . '
        EventTypeToken = 'The event is most likely to be a ' + processType + ', with a probability of ' + "{0:.0f}".format(float(paramdict[ev_type][:-1])-1) + ' percent. '
        FalseAlarmToken = 'The false alarm rate of the event is ' + process_FAR(far,tts='on') +'. '
        DistanceLookBackToken = 'It is approximately ' + oom_to_words(dist,'Megaparsecs',tts='on') + ' away, which is equivalent to a lookback time of '+ oom_to_words(distly,'years',tts='on')+'. '

        if '<' not in paramdict['HasRemnant'][:-1]:
            if float(paramdict['HasRemnant'][:-1]) > 10:
                HasRemnantToken = 'If astrophysical, the event may also have left a remnant. The probability of this is '+ str(int(float(paramdict['HasRemnant'][:-1])))+' percent.'
                tokens=[InitialToken,EventTypeToken,FalseAlarmToken,DistanceLookBackToken,HasRemnantToken]
        else:
            tokens=[InitialToken,EventTypeToken,FalseAlarmToken,DistanceLookBackToken]
        renderthreads = []
        def render_audio(token,num):
#            print(token)
            tts=gTTS(token)
            tts.save('readout'+num+'.mp3')

        for k,token in enumerate(tokens):
#            engine.say(token)
#            engine.runAndWait()
            t=threading.Thread(target=render_audio,args=(token,str(k)))
            renderthreads.append(t)
            t.start()
        for t in renderthreads:
            t.join()
        maximum = k
        for i in range(maximum+1):
            os.system("mpg321 --stereo readout"+str(i)+".mp3")

class RebuildPop(ModalView):
    def waiting(self):
        global rebuild_flag
        print('opened')
        while rebuild_flag == 1:
            print('waiting')
            time.sleep(1)
        print('done')
        self.dismiss()
    def opened(self):
        rebuild_thread = threading.Thread(target=self.waiting)
        rebuild_thread.start()




######line 1275

class StatusScreenv2(Screen):
    det1props = ListProperty()
    det2props = ListProperty()
    det3props = ListProperty()
    det4props = ListProperty()
    det5props = ListProperty()
    bios=ListProperty()
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.bios=(['LIGO Livingston is one of two ground-based GW detectors, of 2nd generation, built in the USA. The observatory uses state-of-ther-art technology to achieve the most precise measurement of displacement. It can detect a change in the 4 km mirror spacing of less than a ten-thousandth the diameter of a proton. \nForming a pair seperated by over 3000km, LIGO Hanford and Livingston observed gravitational waves for the first time in history on 14 September 2015.',
                       'LIGO Hanford is the 2nd ground-based GW detectors, of 2nd generation, built in the USA (together with LIGO Livingston). Ground-based interferometric detectors use light interference to measure changes in the distance between mirrors that are kms appart. Gravitational waves stretch and shrink each arm of the interferometer alternatively changing the distance between mirrors. The longer the arms (distance between mirrors) the bigger the effect caused by gravitational waves.',
                       'GEO600 is a gravitational wave detector located in Hanover, Germany (designed and operated with the UK). Although of smaller arm length (600m folded arms), the detector has comparable sensitive to Virgo above 2kHz. However at lower frequencies (~100Hz region) its sensitivity is 2 orders of magnitude lower than 2nd generation detectors. GEO 600 has been a vital proof of concept for many advanced technologies and features that are common to 2nd generation detectors.',
                       "The Virgo interferometer is Europe's largest to date, with 3km long arms. It is located near Pisa, Italy. It is a 2nd generation detector, of similar sensitivity to LIGO detectors. The more sensitive GW detectors become, the further they can see gravitational waves, which then increases the number of potential sources and the probability of a detection.\n Virgo and LIGO detectors contributed to the 1st gravitational wave detection of the merger of two neutron stars in  17 August 2017. The first ever detection with electromagnetic counterparts.",
                       "The Kamioka Gravitational Wave Detector (KAGRA) will be the world's first underground gravitational wave observatory. It is constructed in the Kamioka mine, Japan. This detector will utilise cryogenic cooling to reduce the temperature of the mirrors and so minimize thermal noise in the measuring process. It will be operational towards the end of 2019 although far from its design sensitivity and soon after will join the 3rd Observing run with the rest of the network of detectors."])
        t = threading.Thread(target=statusupdate,args=(self,),daemon=True)
        t.start()

    def retract(self,presser):
        for child in self.children[0].children:
            if child.pos[1] < 240:
                anim = Animation(x=child.pos[0],y=child.pos[1]-240-child.height,duration=0.5)
                anim.start(child)
            elif child.pos[1] > 240:
                anim=Animation(x=child.pos[0],y=240+child.pos[1]+child.height,duration=0.5)
                anim.start(child)

        App.get_running_app().root.transition=NoTransition()
        def change(presser):
            App.get_running_app().root.current='statinfo'
            propers = presser.prop
            if propers[2] == 'N/A' or propers[2] == '':
                propers[2] = ''
            elif propers[2][1:4] != 'for':
                propers[2] = ' for ' + propers[2]
            App.get_running_app().root.current_screen.detlist = propers
            App.get_running_app().root.current_screen.bio = presser.bio
        Clock.schedule_once(lambda dt: change(presser),0.5)

class PlotsScreen(Screen):
    imgsources = ListProperty()
    descs = ListProperty()

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        t3 = threading.Thread(target=plotupdate,args=(self,),daemon=True)
        t3.start()
    def update_buttons(self,index):
        getattr(self.ids,'pbut'+str(index+1)).trigger_action(duration=0)
class StatBio(Screen):
    detlist=ListProperty()
    bio=ObjectProperty()
    def change(obj):
        App.get_running_app().root.transition=NoTransition()
        App.get_running_app().root.current = 'status'
        for child in App.get_running_app().root.current_screen.children[0].children:
            if child.pos[1] < 240:
                anim = Animation(x=child.pos[0],y=240+child.pos[1]+child.height)
                anim.start(child)
            elif child.pos[1] > 240:
                anim=Animation(x=child.pos[0],y=child.pos[1]-240-child.height)
                anim.start(child)
        App.get_running_app().root.transition=SlideTransition()


class MyApp(App):
    def build_config(self,config):
        config.setdefaults('Section',{'PeriodicBackup':'0'})
    def on_start(self):
        global flag
        global main_flag
        global newevent_flag
        flag = 0
        main_flag=0
        newevent_flag=0

    def build(self):
        config = self.config
        now = time.time()
        last_backup =float(config.get('Section','PeriodicBackup'))
        print('It has been '+ str((now - last_backup)/86400) + ' days since the last backup')

        if os.path.basename(os.getcwd()) != "event_data":
            dir_to_search = "event_data"
        else:
            dir_to_search=None
        if 'Event Database' not in os.listdir(dir_to_search):
            print('Event file not found.')
            file_presence = 0
        else:
            file_presence = 1

        if now-last_backup > 86400 or file_presence == 0:
            print('Performing Periodic Event Sync. Please be patient - this may take a while...')
            sync_database()
            config.set('Section','PeriodicBackup',now)
            config.write()
            print('Initial Event Sync Complete...')
        else:
            print('Event Sync not required...')

        sm = ScreenManager()
        sm.add_widget(MainScreenv2(name='main'))
        sm.add_widget(HistoryScreenv2(name='history'))
        sm.add_widget(StatusScreenv2(name='status'))
        sm.add_widget(PlotsScreen(name='plots'))
        sm.add_widget(StatBio(name='statinfo'))
        sm.add_widget(InfoPop(name='historypop'))
        sm.add_widget(SkyPop(name='sky'))
        sm.add_widget(DevPop(name='dev'))

        print('Initialised application...')
        return sm

if __name__ == '__main__':
    MyApp().run()
    main_flag = 1
    Builder.unload_file("GWalarm.kv")
    if pixels:
        GPIO.cleanup()
    time.sleep(5)
    print('KeyboardInterrupt to close listener...')
    raise KeyboardInterrupt










