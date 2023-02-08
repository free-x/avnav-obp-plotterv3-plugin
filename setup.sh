#! /bin/bash
#OBP plotter v3 setup script
#run as root
#returns 1 if reboot needed
PATTERN="OBPPLOTTERV3_DO_NOT_DELETE"
STARTPATTERN="#${PATTERN}_START"
ENDPATTERN="#${PATTERN}_END"

log(){
    echo "OBPPLOTTERV3: $*"
}
err(){
    log ERROR "$*"
    exit -1
}
CONFIG=/boot/config.txt

read -r -d '' CFGDATA << 'EOF'
dtoverlay=pwm,pin=12,func=4
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=1000000
dtoverlay=goodix,reset=4,interrupt=17
dtoverlay=hifiberry-dac
dtoverlay=i2s-mmap
EOF


updateConfig(){
    rm -f $1.save
    cp $1 $1.save || return 1
    sed -i "/$STARTPATTERN/,/$ENDPATTERN/d" $1
    echo "$STARTPATTERN" >> $1 || return 1
    echo "$CFGDATA" >> $1 || return 1
    echo "$ENDPATTERN" >> $1 || return 1
    return 0
}
ret=0
if grep "$PATTERN" "$CONFIG" > /dev/null ; then
  log "$CONFIG found $PATTERN, checking"
  CUR="`sed -n /$STARTPATTERN/,/$ENDPATTERN/p $CONFIG | grep -v $PATTERN`"
  if [ "$CUR" = "$CFGDATA" ] ; then
    log "$CONFIG ok"
  else
    log "updating $CONFIG, reboot needed"
    updateConfig $CONFIG || err "unable to modify $CONFIG"
    ret=1
  fi
else
  log "must modify $CONFIG, reboot needed"
  updateConfig $CONFIG || err "unable to modify $CONFIG"
  ret=1
fi

if [ -e $CONFIG ] && grep -q -E "^dtparam=audio=on$" $CONFIG; then
  ret=1
  log "need to disable default sound driver, reboot needed"
  sed -i "s|^dtparam=audio=on$|#dtparam=audio=on|" $CONFIG &> /dev/null
fi

SOUNDCFG=/etc/asound.conf
if [ -f "$SOUNDCFG" ] ; then
  rm -f "$SOUNDCFG.save"
  mv "$SOUNDCFG" "$SOUNDCFG.save"
fi
cp `dirname $0`/asound.conf "$SOUNDCFG" || err "unable to set up sound config"

#TODO: should we enable aply to avoid noise?

#TODO: should we own this script? - is no official API
HELPER=`dirname $0`/../../raspberry/xui/patchServerConfig.py
BASEDIR=/home/pi/avnav/data
CFG="$BASEDIR/avnav_server.xml"
if [ -x "$HELPER" -a -w "$CFG" ] ; then
  log "setting up dimm command for avnav"
  $HELPER $CFG dimm '$BASEDIR/../plugins/obp-plotterv3/dimm.sh' '' || err "unable to set up dimm"
else
  log "unable to set up dimm $HELPER or $CFG not found"
fi

exit $ret


