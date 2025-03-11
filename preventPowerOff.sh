#! /bin/bash
PINCTRL=/usr/bin/pinctrl
if [ -x $PINCTRL ] ; then
    mode=`$PINCTRL get 24 | sed 's/.*= *//'`    
    if [ "$mode"  != "none" ] ; then
        logger -t obppreventpo "prevent poweroff on reboot"
        $PINCTRL set 24 no
    fi
else
    if [ -f /sys/class/gpio/gpio24/value ] ; then
        logger -t obppreventpo "prevent poweroff on reboot"
        echo in >/sys/class/gpio/gpio24/direction 
        sleep 0.1
    fi
fi
