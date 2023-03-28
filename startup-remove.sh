#! /bin/bash
#OBP plotter v3 remove script
#run as root
#returns 1 if reboot needed
PATTERN="OBPPLOTTERV3_DO_NOT_DELETE"
STARTPATTERN="#${PATTERN}_START"
ENDPATTERN="#${PATTERN}_END"
CONFIG=/boot/config.txt
if grep "$PATTERN" "$CONFIG" > /dev/null ; then
	echo "found $PATTERN in $CONFIG, removing it now"
	sed -i "/$STARTPATTERN/,/$ENDPATTERN/d" "$CONFIG"
fi


