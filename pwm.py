#!/usr/bin/env python3
import os
import sys
import traceback
import time
gpio=None
try:
  import RPi.GPIO as gpio
except:
   pass

class PWMControl:
  '''
  control the PWM channel via sysfs
  requires an entry
  dtoverlay=pwm,pin=12,func=4
  in /boot/config.txt
  refer to /boot/overlay/README for allowed combinations of pin and func
  '''
  BASE_PATH="/sys/class/pwm/pwmchip0"
  #if we find a pwmchip2 (pi5) we must use this one
  BASE_PATH5="/sys/class/pwm/pwmchip2"
  def __init__(self,frequency=100, dimmFile=None) -> None:
    self.period=None
    self.duty=None
    self.freq=frequency
    self.pwm0=None
    self._setParam(50,frequency)
    self.prepared=False
    self.dimm=False
    self.dimmWritten=False
    self.dimmFile=None
    self.dimmFile=dimmFile
    self.basePath=None   
    
  def _setParam(self,duty,freq=None):
    if freq is not None:
      self.period=int(1000000000.0/float(freq))
    self.duty=int(duty*self.period/100)
    if self.duty > self.period:
      self.duty=self.period
  def _writeDuty(self,duty):
    wfile=os.path.join(self.pwm0,"duty_cycle")
    with open(wfile,"w") as h:
      if self.dimm:
        self.dimmWritten=True
        h.write("0")
      else:
        self.dimmWritten=False   
        h.write(str(duty))
  def _checkDim(self):
    if self.dimmFile is not None:
      return os.path.exists(self.dimmFile)
    return False
                  
  def _write(self):
    self.dimm=self._checkDim()
    wfile=os.path.join(self.pwm0,"period")
    with open(wfile,"r") as h:
      old=h.readline()
      if old is not None and int(old) > self.period:
        #must reset duty
        self._writeDuty(0)
    with open(wfile,"w") as h:
      h.write(str(self.period))
    self._writeDuty(self.duty)
    return not self.dimmWritten

  def checkDimmChange(self):
     newDimm=self._checkDim()
     if newDimm != self.dimmWritten:
        return True
     return False
  def prepare(self,freq=100,duty=50):
    '''
    prepare the pwm controller
    frequency in Hz, duty in %
    will raise an exception if hardware is not accessible
    '''
    if self.basePath is None:
      if os.path.exists(self.BASE_PATH5):
          self.basePath=self.BASE_PATH5
      else:
        if not os.path.exists(self.BASE_PATH):
          raise Exception("pwm not created, missing %s"%self.BASE_PATH)
        self.basePath=self.BASE_PATH
      self.pwm0=os.path.join(self.basePath,"pwm0")
    self.freq=freq  
    try:  
        with open(os.path.join(self.basePath,"export"),"w") as h:
            h.write("0")
    except OSError as ose:
        if ose.errno == 16:
            pass
        else:
            raise
    time.sleep(0.5)      
    if not os.path.exists(self.pwm0):
      raise Exception("cannot access hardware pwm, %s not found",self.pwm0)
    self._setParam(duty,freq)
    self._write()
    wfile=os.path.join(self.pwm0,"enable")
    with open(wfile,"w") as h:
      h.write(str(1))
    self.prepared=True  

  def update(self,duty):
    if not self.prepared:
      self.prepare(freq=self.freq,duty=duty)
    else:  
      self._setParam(duty)
      self._write()
    return not self.dimmWritten  
    

if __name__ == '__main__':
    try:
        pwm=PWMControl()
        freq=None
        if len(sys.argv) > 2:
            freq=int(sys.argv[2])
        pwm.prepare(duty=int(sys.argv[1]),freq=freq)
        print("successfully set period=%d, duty=%d"%(pwm.period,pwm.duty))
        sys.exit(0)
    except Exception as e:
        print("ERROR: %s"%traceback.format_exc())
        sys.exit(1)    
