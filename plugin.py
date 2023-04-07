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
gpio=None 
try:
  import smbus
  import RPi.GPIO as gpio
except:
  hasPackages=False

# brightness receiver address (i2c)
address = 0x23

#frequency for pwm in Hz
frequency = 1000

class GpioCfg:
  def __init__(self,board,bcm) -> None:
    self.board=board
    self.bcm=bcm
  def getPin(self,mode):
    if mode == gpio.BOARD:
      return self.board
    else:
      return self.bcm  

DIMM_GPIO=GpioCfg(37,26) #if 1 we are in dimm mode and set duty time to 0
START_BT=GpioCfg(15,22) #if detected low on startup we reset brightness


class Plugin(object):
  CFG_AUTO='adaptiveBrightness'
  CFG_VOLUME='volume'
  CFG_MINLUM='minLuminance'
  CFG_MAXLUM='maxLuminance'
  CONFIG=[
    {
      'name':CFG_VOLUME,
      'description':'speaker volume for our alarm sounds (0...255)',
      'default':128,
      'type': 'NUMBER',
      'rangeOrList': [0,255]
    },
    {
      'name':CFG_AUTO,
      'description':'adapt screen brightness to environmental brightness',
      'default': False,
      'type':'BOOLEAN'
    },
    {
      'name':CFG_MINLUM,
      'description':'the luminance value for minimal brightness',
      'default': 10.0,
      'type':'FLOAT'
    },
    {
      'name':CFG_MAXLUM,
      'description':'the luminance value for 100% brightness',
      'default': 5000.0,
      'type':'FLOAT'
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
    dimmGpio=None
    self.startButton=None
    if gpio is not None:
      self.gpioMode=gpio.getmode()
      if self.gpioMode is None:
        gpio.setmode(gpio.BOARD)
        self.gpioMode=gpio.getmode()
      dimmGpio=DIMM_GPIO.getPin(self.gpioMode)
      self.startButton=START_BT.getPin(self.gpioMode)
      gpio.setup(self.startButton,gpio.IN)
    self.pwm=pwm.PWMControl(frequency,dimmGpio=dimmGpio)
    self.luminance=0
    self.lock=threading.Lock()
    self.error=None
    self.soundVolume=128
    self.luminanceError=None
    self.firstStart=True
    
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

  def getCurrentDuty(self,adapt):
    '''
    get step without changing value
    '''
    idx=self.currentStep
    if idx < 0:
      idx=0
    if idx >= len(self.STEPS):
      idx=len(self.STEPS)-1
    rt= self.STEPS[idx]
    if not adapt:
      return rt 
    return self.adaptiveBrightness(rt)  

  def updateStatus(self):
    if self.error is not None:
      self.api.setStatus('ERROR',self.error)
    else:
      if self.luminanceError is not None:
        if self.pwm.dimmWritten:
          self.api.setStatus('STARTED',"dimm active, luminance error %s"%self.luminanceError)
        else:
          self.api.setStatus('STARTED',"adaptive %s, step %d duty %.2f, luminance error %s"
                             %(self._adaptiveOn(),self.currentStep,self.getCurrentDuty(True),self.luminanceError))
      else:
        if self.pwm.dimmWritten:
          self.api.setStatus('NMEA',"dimm active, luminance %d"%self.luminance)
        else:
          self.api.setStatus('NMEA',"adaptive %s, step %d duty %.2f, luminance %d"
                             %(self._adaptiveOn(),self.currentStep,self.getCurrentDuty(True),self.luminance))      
      
  
  def update(self,change=0):
    with self.lock:
      duty=self.updateIndex(change)
      try:
        self.pwm.update(self.adaptiveBrightness(duty))
        self.error=None
        self.updateStatus()
      except Exception as e:
        self.error=str(e)
        self.updateStatus()
        raise

  def readBrightness(self,i2c,address):
    data=None
    tst=os.getenv('AVNAV_TEST_LUM')
    if tst is not None:
      with open(tst,'rb') as h:
        data=h.read()
    else:    
      data = i2c.read_i2c_block_data(address,0x10,2)
    if len(data) != 2:
      raise Exception("invalid data len %d"%len(data))
    return (data[1] + (256 * data[0]))

  def _adaptiveOn(self):
    active=self.api.getConfigValue('adaptiveBrightness','False')
    if not type(active) is bool:
      active=str(active).lower() == 'true'
    return active
  
  def _getFloat(self,name,default):
    try:
      rt=self.api.getConfigValue(name,default)
      return float(rt)
    except:
      return default

  def adaptiveBrightness(self,userDuty):
    active=self._adaptiveOn()
    if not active:
      return userDuty
    if self.luminanceError is not None:
      return userDuty
    minLuminance=self._getFloat(self.CFG_MINLUM,10.0)
    maxLuminance=self._getFloat(self.CFG_MAXLUM,5000.0)
    currentLuminance=float(self.luminance)
    if currentLuminance < minLuminance:
      currentLuminance=minLuminance
    if currentLuminance > maxLuminance:
      currentLuminance=maxLuminance
    currentOffset=currentLuminance-minLuminance  
    minValue=self.STEPS[0]
    value=currentOffset/float(maxLuminance-minLuminance)*100.0
    if value < minValue:
      #ensure some minimal brightness
      value=minValue
    # we give the user a chance to modify our adaptive brightness
    # if the user selected brightness is at 100% 
    # we ensure that we at least reach our initial brightness
    defaultUser=self.STEPS[self.INITIAL_STEP]
    if userDuty != defaultUser:
      value+=(userDuty-defaultUser)*defaultUser/(100-defaultUser)
      if value < minValue:
        value = minValue
      if value > 100:
        value=100  
    self.api.debug("computed duty %f from brightness %f",value,currentLuminance)
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
    self.api.registerUserApp(self.api.getBaseUrl()+'/gui.html','plotter.svg')
    if self.error is not None:
      self.api.setStatus('ERROR',self.error)
    else:  
      self.api.setStatus('NMEA','running')  
    i2c = smbus.SMBus(1)
    self.api.log("gpio mode=%d",self.gpioMode)
    if self.firstStart:
      self.firstStart=False
      if self.startButton is not None:
        if gpio.input(self.startButton) == gpio.LOW:
          self.api.log("start button pressed on first start, reset brightness")
          self.currentStep=self.INITIAL_STEP
          self.api.saveConfigValues({self.CFG_AUTO:False})
    if address is not None:
      try:
        i2c.write_byte(address,0x10)
      except Exception as e:
        self.luminanceError=str(e)
        self.api.error("Unable to trigger brightness read: %s",str(e))
    lastLuminance=None
    lastadaptive=None    
    while not self.api.shouldStopMainThread():
      try:
        if not self.pwm.prepared:
          try:
            self.update()
          except:
            pass
        if address is not None:
          try:
            newBrightness=self.readBrightness(i2c,address)
            if self.luminanceError is not None or self.luminance is None:
              self.luminance=newBrightness
            else:
              diff=float(newBrightness)-float(self.luminance)
              self.luminance=float(self.luminance)+self.BRIGHTNESS_AV_FACTOR*diff
            self.luminanceError=None
          except Exception as e:
            self.luminance=None
            if self.luminanceError is None:
              self.luminanceError="Read:%s"%str(e)
              self.api.error("unable to read brightness: %s",self.luminanceError)    
            else:
              self.luminanceError=str(e)
        changed=self.pwm.checkDimmChange()
        if lastLuminance != self.luminance:
          changed=True
          lastLuminance=self.luminance
        newadaptive=self._adaptiveOn()
        if newadaptive != lastadaptive:
          changed=True
          lastadaptive=newadaptive  
        if changed:
          self.update()      
        self.updateStatus()        
        time.sleep(0.5)
      except Exception as e:
        self.error=str(e)
        self.updateStatus()
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
                'brightness':int(self.luminance) if self.luminance is not None else None,
                'step':self.currentStep,
                'duty':self.getCurrentDuty(True),
                'userDuty': self.getCurrentDuty(False),
                'volume':self.soundVolume,
                'error':self.error,
                'brightnessError': self.luminanceError,
                'auto': self._adaptiveOn()
                }
      if url == 'plus':
        self.update(1)
        return OK
      if url == 'minus':
        self.update(-1)
        return OK
      if url == 'defaultStep':
        change=self.INITIAL_STEP-self.currentStep
        self.update(change)
        return OK
      if url == 'volumePlus':
        self.changeVolume(1)
        return OK
      if url == 'volumeMinus':
        self.changeVolume(-1)
        return OK
      if url == 'autoOn':
        self.api.saveConfigValues({self.CFG_AUTO:True})
        return OK
      if url == 'autoOff':
        self.api.saveConfigValues({self.CFG_AUTO:False})
        return OK
      if url == 'saveCurrent':
        with self.lock:
          #TODO: initial brightness
          self.api.saveConfigValues({self.CFG_VOLUME:self.soundVolume})
          return {'status':'OK','saved':'volume=%s'%str(self.soundVolume)}  
    except Exception as e:
      return {'status':str(e)}    


