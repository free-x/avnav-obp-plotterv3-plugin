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
address = 0x23

#frequency for pwm in Hz
frequency = 1000

DIMM_GPIO=26 #if 1 we are in dimm mode and set duty time to 0


class Plugin(object):
  CONFIG=[
    {
      'name':'volume',
      'description':'speaker volume for our alarm sounds (0...255)',
      'default':128,
      'type': 'NUMBER',
      'rangeOrList': [0,255]
    },
    {
      'name':'adaptiveBrightness',
      'description':'adapt screen brightness to environmental brightness',
      'default': False,
      'type':'BOOLEAN'
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
    0.1,0.2,0.4,0.7,1,3,5,7,10,
    15,20,25,30,35,
    40,50,60,70,80,90,99
  ]
  INITIAL_STEP=14 #index in steps

  BRIGHTNESS_AV_FACTOR=0.2 #movin average factor for brightness

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
    self.pwm=pwm.PWMControl(frequency,dimmGpio=DIMM_GPIO)
    self.brightness=0
    self.lock=threading.Lock()
    self.error=None
    self.soundVolume=128
    self.brightnessError=None
    
  def updateParam(self,newParam):
    self.api.saveConfigValues(newParam)
    if hasattr(self.api,'registerCommand'):
      volume=self.api.getConfigValue('volume','128')
      self.updateVolume(volume)
 
  def updateVolume(self,newVolume):
    self.soundVolume=newVolume
    self.api.registerCommand('sound','sound.sh',parameters=[str(newVolume)])

  def changeVolume(self,delta=0):
    with self.lock:
      change=delta*8
      current=int(self.soundVolume)
      newVolume=current+change if current < 255 else 256 + change
      if newVolume < 0:
        newVolume=0
      if newVolume > 255:
        newVolume=255
      self.updateVolume(newVolume)

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
        normal=self.pwm.update(duty)
        if normal:
          self.api.setStatus('NMEA','brightness %d, step %d, duty %d'%(self.brightness,self.currentStep,duty))
        else:
          self.api.setStatus('NMEA','dimm active, brightness %d'%(self.brightness))  
        self.error=None
      except Exception as e:
        self.api.setStatus('ERROR',str(e))  
        self.error=str(e)
        raise

  def readBrightness(self,i2c,address):
    data = i2c.read_i2c_block_data(address,0x10)
    if len(data) != 2:
      raise Exception("invalid data len %d"%len(data))
    return (data[1] + (256 * data[0]))

  def adaptiveBrightness(self,userDuty):
    active=self.api.getConfigValue('adaptiveBrightness','False')
    if not type(active) is bool:
      active=str(active).lower() == 'true'
    if not active:
      return userDuty
    if self.brightnessError is not None:
      return userDuty
    minBrightness=10
    maxBrightness=5000
    currentBrightness=self.brightness
    if currentBrightness < minBrightness:
      currentBrightness=minBrightness
    if currentBrightness > maxBrightness:
      currentBrightness=maxBrightness
    value=100.0 - float(currentBrightness-minBrightness)/float(maxBrightness-minBrightness)*100.0
    value=int(value)
    self.api.debug("computed duty %d from brightness %f",value,currentBrightness)
    return value

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
    self.soundVolume=self.api.getConfigValue('volume',128)
    if hasattr(self.api,'registerCommand'):
      self.api.registerCommand('sound','sound.sh',parameters=[str(self.soundVolume)])
      self.api.registerCommand('dimm','dimm.sh',client='all')
    else:
      self.error="unable to register dimm command, avnav too old"  
    self.api.registerRequestHandler(self.handleApiRequest)
    self.api.registerSettingsFile('localFirefox','localFirefox.json')
    self.api.registerLayout('localFirefox','localLayout.json')
    self.api.registerUserApp(self.api.getBaseUrl()+'/gui.html','dimm.svg')
    if self.error is not None:
      self.api.setStatus('ERROR',self.error)
    else:  
      self.api.setStatus('NMEA','running')  
    i2c = smbus.SMBus(1)
    currentMode=gpio.getmode()
    if currentMode is None:
      gpio.setmode(gpio.BOARD)
    self.api.log("gpio mode=%d",gpio.getmode())
    if address is not None:
      try:
        i2c.write_byte(address,0x10)
      except Exception as e:
        self.brightnessError=str(e)
        self.api.error("Unable to trigger brightness read: %s",str(e))
    while not self.api.shouldStopMainThread():
      try:
        if not self.pwm.prepared:
          try:
            self.update()
          except:
            pass
        changed=self.pwm.checkDimmChange()    
        if changed:
          self.update()
        if address is not None:
          try:
            newBrightness=self.readBrightness(i2c,address)
            if self.brightnessError is not None or self.brightness is None:
              self.brightness=newBrightness
            else:
              diff=float(newBrightness)-float(self.brightness)
              self.brightness=float(self.brightness)+self.BRIGHTNESS_AV_FACTOR*diff
            self.brightnessError=None
          except Exception as e:
            if self.brightnessError is None:
              self.brightnessError="Read:%"%str(e)
              self.api.error("unable to read brightness: %s",self.brightnessError)    
            else:
              self.brightnessError=str(e)  
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
        return {'status':'OK',
                'brightness':int(self.brightness) if self.brightness is not None else None,
                'step':self.currentStep,
                'duty':self.getCurrentDuty(),
                'volume':self.soundVolume,
                'error':self.error,
                'brightnessError': self.brightnessError}
      if url == 'plus':
        self.update(1)
        return OK
      if url == 'minus':
        self.update(-1)
        return OK
      if url == 'volumePlus':
        self.changeVolume(1)
        return OK
      if url == 'volumeMinus':
        self.changeVolume(-1)
        return OK
      if url == 'saveCurrent':
        with self.lock:
          #TODO: initial brightness
          self.api.saveConfigValues({'volume':self.soundVolume})
          return {'status':'OK','saved':'volume=%s'%str(self.soundVolume)}  
    except Exception as e:
      return {'status':str(e)}    


