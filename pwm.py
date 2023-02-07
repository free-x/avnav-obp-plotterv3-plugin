#!/usr/bin/env python3
import os
import sys
import traceback

class PWMControl:
  '''
  control the PWM channel via sysfs
  requires an entry
  dtoverlay=pwm,pin=12,func=4
  in /boot/config.txt
  refer to /boot/overlay/README for allowed combinations of pin and func
  '''
  BASE_PATH="/sys/class/pwm/pwmchip0"
  def __init__(self) -> None:
    self.period=None
    self.duty=None
    self.pwm0=os.path.join(self.BASE_PATH,"pwm0")
    self._setParam(50,100)
    pass
  def _setParam(self,duty,freq=None):
    if freq is not None:
      self.period=int(1000000000.0/float(freq))
    self.duty=int(duty*self.period/100)
  def _write(self):
    wfile=os.path.join(self.pwm0,"period")
    with open(wfile,"w") as h:
      h.write(str(self.period))
    wfile=os.path.join(self.pwm0,"duty_cycle")
    with open(wfile,"w") as h:
      h.write(str(self.duty))

  def prepare(self,freq=100,duty=50):
    '''
    prepare the pwm controller
    frequency in Hz, duty in %
    will raise an exception if hardware is not accessible
    '''
    if not os.path.exists(self.BASE_PATH):
      raise Exception("pwm not created, missing %s"%self.BASE_PATH)
    try:  
        with open(os.path.join(self.BASE_PATH,"export"),"w") as h:
            h.write("0")
    except OSError as ose:
        if ose.errno == 16:
            pass
        else:
            raise
    if not os.path.exists(self.pwm0):
      raise Exception("cannot access hardware pwm, %s not found",self.pwm0)
    self._setParam(duty,freq)
    self._write()
    wfile=os.path.join(self.pwm0,"enable")
    with open(wfile,"w") as h:
      h.write(str(1))

  def update(self,duty):
    self._setParam(duty)
    self._write()
    

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
