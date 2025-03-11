#!/usr/bin/env bash

PINCTRL=/usr/bin/pinctrl
if [ -x $PINCTRL ] ; then
    $PINCTRL set 23 op dh
    $PINCTRL set 24 op dl
    exit 0
fi
#   Exports pin to userspace
echo 23 >/sys/class/gpio/export
echo 24 >/sys/class/gpio/export
 
sleep 1
# Enable power-off
echo out >/sys/class/gpio/gpio23/direction
echo 1 >/sys/class/gpio/gpio23/value

# power down enable
echo out >/sys/class/gpio/gpio24/direction 
echo 0 >/sys/class/gpio/gpio24/value

