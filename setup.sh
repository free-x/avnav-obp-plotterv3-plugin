#OBP plotter v3 setup script
#run as root
#returns 1 if reboot needed
PATTERN="OBPPLOTTERV3_DO_NOT_DELETE"
STARTPATTERN="${PATTERN}_START"
ENDPATTERN="${PATTERN}_END"

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
    echo "$CONFIG" >> $1 || return 1
    echo "$ENDPATTERN" >> $1 || return 1
    return 0
}
ret=0
if grep "$PATTERN" "$CONFIG" > /dev/null ; then
  log "$CONFIG found $PATTERN, checking"
  CUR="`sed -n /$STARTPATTERN/,/$ENDPATTERN/p $CONFIG | grep -v $PATTERN`"
  if [ "$CUR" = "$CONFIG" ] ; then
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

#TODO:
#modify avnav_server.xml for dim button
#modify firefox startup




