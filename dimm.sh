#! /bin/bash
#OBP Plotter v3 dim
GPIO_DIM=26
GPIO_LED=16
BASE=/sys/class/gpio
err(){
    echo "ERROR: $*"
    exit 1
}
[ "$1" = "" ] &&  err "usage: $0 value"
ctrl=$BASE/export
[ ! -w "$ctrl" ] && err "unable to write $ctrl"
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
    echo 0 > $BASE/gpio$GPIO_DIM/value || err "unable to set dim"
    echo 1 > $BASE/gpio$GPIO_LED/value || err "unable to set led"
else
    echo 1 > $BASE/gpio$GPIO_DIM/value || err "unable to set dim"
    echo 0 > $BASE/gpio$GPIO_LED/value || err "unable to set led"
fi
exit 0


