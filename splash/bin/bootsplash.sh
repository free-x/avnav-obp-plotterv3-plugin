#! /bin/bash
echo "bootsplash started"
num=100
dev=/dev/fb0
CFG=/boot/avnav.conf
if [ ! -f $CFG ] ; then
  echo "$CFG not found"
  exit 0
fi
. $CFG
if [ "$AVNAV_OBPPLOTTERV3" != yes ] ; then
  echo "AVNAV_OBPPLOTTERV3 not set to yes"
  exit 0
fi
while [ "$num" -gt 0 ] 
do
  if [ -c $dev ] ; then
    break
  fi
  num=$(( $num - 1 ))
  sleep 0.1
done
sleep 0.2
if [ ! -c $dev ] ; then
  echo "ERROR: device $dev not found"
  exit 1
fi
echo "$dev available, loading image"
`dirname $0`/fbsplash --resize --freeaspect `dirname $0`/splash2.png
echo "bootsplash done"
