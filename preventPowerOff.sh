#! /bin/bash
if [ -f /sys/class/gpio/gpio24/value ] ; then
    logger -t obppreventpo "prevent poweroff on reboot"
    echo in >/sys/class/gpio/gpio24/direction 
    sleep 0.1
fi
