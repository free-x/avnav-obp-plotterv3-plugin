#!/usr/bin/env bash

sleep 10

#   Exports pin to userspace
echo 23 >/sys/class/gpio/export
echo 24 >/sys/class/gpio/export
 
sleep 1
 
# pin direction = output
echo out >/sys/class/gpio/gpio23/direction
echo out >/sys/class/gpio/gpio24/direction 

# Enable shutdown
echo 1 >/sys/class/gpio/gpio23/value
echo 0 >/sys/class/gpio/gpio24/value
