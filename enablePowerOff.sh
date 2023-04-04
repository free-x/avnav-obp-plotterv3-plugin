#!/usr/bin/env bash

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

