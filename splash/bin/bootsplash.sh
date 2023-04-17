#! /bin/bash
echo "bootsplash started"
num=100
dev=/dev/fb0
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
pwm=/sys/class/pwm/pwmchip0/
#set the brightness to 40%
if [ -d "$pwm" ] ; then
  echo 0 > $pwm/export
  num=20
  while [ "$num" -gt 0 ] 
  do
    if [ -f $pwm/pwm0/period ] ; then
      break
    fi
    num=$(( $num - 1 ))
    sleep 0.1  
  done
  echo 1000000 > $pwm/pwm0/period
  echo 400000 > $pwm/pwm0/duty_cycle
  echo 1 > $pwm/pwm0/enable
fi
`dirname $0`/fbsplash --resize --freeaspect `dirname $0`/../splash2.png
echo "bootsplash done"
