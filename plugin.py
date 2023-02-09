'''
obp plotter v3 plugin
plugin for AvNav
'''

import time
import os
import threading
import sys
dn=os.path.dirname(__file__)
sys.path.append(dn)
import pwm
hasPackages=True
try:
  import smbus
  import RPi.GPIO as gpio
except:
  hasPackages=False

# brightness receiver address (i2c)
address = None #0xnn

#frequency for pwm in Hz
frequency = 1000



class Plugin(object):
  CONFIG=[
    {
      'name':'volume',
      'description':'speaker volume for our alarm sounds (0...255)',
      'default':128,
      'type': 'NUMBER',
      'rangeOrList': [0,255]
    }
  ]
  @classmethod
  def pluginInfo(cls):  
    """
    the description for the module
    @return: a dict with the content described below
            parts:
               * description (mandatory)
               * data: list of keys to be stored (optional)
                 * path - the key - see AVNApi.addData, all pathes starting with "gps." will be sent to the GUI
                 * description
    """
    return {
      'description': 'plugin for obp plotter v3 brightness control'
    }

  STEPS=[
    1,3,5,7,10,
    15,20,25,30,35,
    40,50,60,70,80,90,99
  ]
  INITIAL_STEP=11 #index in steps
  def __init__(self,api):
    """
        initialize a plugins
        do any checks here and throw an exception on error
        do not yet start any threads!
        @param api: the api to communicate with avnav
        @type  api: AVNApi
    """
    self.api = api
    self.api.registerEditableParameters(
      self.CONFIG ,
      self.updateParam)
    self.api.registerRestart(self.stop)
    self.configSequence=0
    self.keyMap={}
    self.allowRepeat=False
    self.channel=0
    self.currentStep=self.INITIAL_STEP
    self.pwm=pwm.PWMControl(frequency)
    self.brightness=0
    self.lock=threading.Lock()
    self.error=None

  def updateParam(self,newParam):
    self.api.saveConfigValues(newParam)
    if hasattr(self.api,'registerCommand'):
      volume=self.api.getConfigValue('volume','128')
      self.api.registerCommand('sound','sound.sh',parameters=[volume])
 

  def stop(self):
    pass

  def updateIndex(self,change=0):
    self.currentStep+=change
    if self.currentStep < 0:
      self.currentStep=0
    if self.currentStep >= len(self.STEPS):
      self.currentStep= len(self.STEPS)-1
    return self.STEPS[self.currentStep]

  def getCurrentDuty(self):
    '''
    get step without changing value
    '''
    idx=self.currentStep
    if idx < 0:
      idx=0
    if idx >= len(self.STEPS):
      idx=len(self.STEPS)-1
    return self.STEPS[idx]    


  def update(self,change=0):
    with self.lock:
      duty=self.updateIndex(change)
      try:
        self.pwm.update(duty)
        self.api.setStatus('NMEA','brightness %d, step %d, duty %d'%(self.brightness,self.currentStep,duty))
        self.error=None
      except Exception as e:
        self.api.setStatus('ERROR',str(e))  
        self.error=str(e)
        raise


  def run(self):
    """
    the run method
    this will be called after successfully instantiating an instance
    this method will be called in a separate Thread
    @return:
    """
    seq=0
    if not hasPackages:
      raise Exception("missing packages for i2c")
    if hasattr(self.api,'registerCommand'):
      volume=self.api.getConfigValue('volume','128')
      self.api.registerCommand('sound','sound.sh',parameters=[volume])
      self.api.registerCommand('dimm','dimm.sh',client='all')
    else:
      self.error="unable to register dimm command, avnav too old"  
    self.api.registerRequestHandler(self.handleApiRequest)
    self.api.registerSettingsFile('localFirefox','localFirefox.json')
    self.api.registerLayout('localFirefox','localLayout.json')
    if self.error is not None:
      self.api.setStatus('ERROR',self.error)
    else:  
      self.api.setStatus('NMEA','running')  
    i2c = smbus.SMBus(1)
    currentMode=gpio.getmode()
    if currentMode is None:
      gpio.setmode(gpio.BOARD)
    self.api.log("gpio mode=%d",gpio.getmode())
    while not self.api.shouldStopMainThread():
      try:
        if not self.pwm.prepared:
          try:
            self.update()
          except:
            pass  
        if address is not None:
          self.brightness=i2c.read_byte(address)
        time.sleep(1)
      except Exception as e:
        self.api.setStatus("ERROR","%s"%str(e))
        time.sleep(1)


  def handleApiRequest(self,url,handler,args):
    """
    handler for API requests send from the JS
    @param url: the url after the plugin base
    @param handler: the HTTP request handler
                    https://docs.python.org/2/library/basehttpserver.html#BaseHTTPServer.BaseHTTPRequestHandler
    @param args: dictionary of query arguments
    @return:
    """
    OK={'status':'OK'}
    try:
      if url == 'query':
        return {'status':'OK','brightness':self.brightness,'step':self.currentStep,'duty':self.getCurrentDuty(),'error':self.error}
      if url == 'plus':
        self.update(1)
        return OK
      if url == 'minus':
        self.update(-1)
        return OK  
    except Exception as e:
      return {'status':str(e)}    


