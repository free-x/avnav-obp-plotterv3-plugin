#! /bin/bash
#OBP Plotter v3 dim
GPIO_DIM=26
GPIO_LED=16
BASE=/sys/class/gpio
DIMM_MARKER=/tmp/obpdimm
err(){
    echo "ERROR: $*"
    exit 1
}
[ "$1" = "" -o "$2" = "" ] &&  err "usage: $0 hdmi|backlight value"
ctrl=$BASE/export
dimmHdmi=0
[ "$1" = hdmi ] && dimmHdmi=1
shift
PINCTRL=/usr/bin/pinctrl
if [ -x $PINCTRL ] ; then
  logger -t obpdim "dimm with pinctrl dimmHdmi=$dimmHdmi, mode=pinctrl, v=$1"
  DIM_V=h
  LED_V=l
  if [ "$1" -eq 0 ] ; then
    LED_V=h
    if [ $dimmHdmi = 1 ] ; then
      DIM_V=l
    fi
    touch "$DIMM_MARKER"
  else
    rm -f "$DIMM_MARKER"
  fi
  $PINCTRL set $GPIO_DIM op d$DIM_V
  $PINCTRL set $GPIO_LED op d$LED_V
  exit 0
fi
[ ! -w "$ctrl" ] && err "unable to write $ctrl"
logger -t obpdim "dimm with pinctrl dimmHdmi=$dimmHdmi, mode=sysfs, v=$1"
echo $GPIO_DIM > $ctrl 2> /dev/null
echo $GPIO_LED > $ctrl 2> /dev/null
wt=3
while [ "$wt" -gt 0 ]
do
  if [ -w $BASE/gpio$GPIO_DIM/direction ] ; then
    break
  fi
  sleep 1
  wt=$(($wt - 1))
done
echo out > $BASE/gpio$GPIO_DIM/direction 
echo out > $BASE/gpio$GPIO_LED/direction 
if [ "$1" -eq 0 ] ; then
    #activate dimm
    if [ $dimmHdmi = 1 ] ; then
      echo 0 > $BASE/gpio$GPIO_DIM/value || err "unable to set dim"
    else
      echo 1 > $BASE/gpio$GPIO_DIM/value || err "unable to set dim"
    fi  
    echo 1 > $BASE/gpio$GPIO_LED/value || err "unable to set led"
    touch "$DIMM_MARKER"
else
    echo 1 > $BASE/gpio$GPIO_DIM/value || err "unable to set dim"
    echo 0 > $BASE/gpio$GPIO_LED/value || err "unable to set led"
    rm -f "$DIMM_MARKER"
fi
exit 0


