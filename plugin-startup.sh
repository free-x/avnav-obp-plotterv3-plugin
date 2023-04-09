#! /bin/bash
#OBP plotter v3 setup script
#run as root
#returns 1 if reboot needed

if [ "$AVNAV_SETUP_HELPER" = "" ] ; then
  echo "ERROR: AVNAV_SETUP_HELPER not set"
  exit 1
fi
. "$AVNAV_SETUP_HELPER"
pdir="`dirname $0`"
PATTERN="#OBPPLOTTERV3_DO_NOT_DELETE"

read -r -d '' CFGDATA << 'EOF'
dtoverlay=pwm,pin=12,func=4
dtparam=spi=on
dtparam=i2c_arm=on
dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=1000000
dtoverlay=goodix,reset=4,interrupt=17
dtoverlay=hifiberry-dac
dtoverlay=i2s-mmap
dtoverlay=gpio-shutdown,gpio_pin=22,active_low=1,gpio_pull=up
initramfs initramfs.img
disable_splash=1
EOF

read -r -d '' MODULES << 'MODULES'
i2c_dev
MODULES

read -r -d '' XINITRC << 'XINITRC'
xli -onroot -fillscreen -quiet /usr/lib/avnav/plugins/obp-plotterv3/splash/splash3.png
(sleep 20 ; xsetroot -bg black ) &
XINITRC

needsReboot=0
ENSCRIPT="$pdir/../../plugin.sh"
P1="system-chremote"
P2="system-`basename $pdir`"
service=obpplotterv3.service
servicefile="/etc/systemd/system/$service"
xinitfile='/home/pi/.xinitrc.d/early-obpplotterv3'
xinitdir="`dirname \"$xinitfile\"`"
xinituser='pi:pi'
if [ "$1" = $MODE_EN ] ; then
  log "enable OBPPLOTTERV3"
  checkConfig "$BOOTCONFIG" "$PATTERN" "$CFGDATA"
  checkRes
  if [ -e "$BOOTCONFIG" ] && grep -q -E "^dtparam=audio=on$" "$BOOTCONFIG"; then
    needsReboot=1
    log "need to disable default sound driver, reboot needed"
    sed -i "s|^dtparam=audio=on$|#dtparam=audio=on|" "$BOOTCONFIG" &> /dev/null
  fi
  MODFILE=/etc/modules
  checkConfig "$MODFILE" "$PATTERN" "$MODULES"
  checkRes
  sound="`cat \"$pdir/asound.conf\"`"
  SOUNDCFG=/etc/asound.conf
  replaceConfig "$SOUNDCFG" "$sound"
  checkRes
  
  # splash image handling
  # (1) copy initramfs and splash1 to /boot
  for f in initramfs.img splash.txt splash1.png
  do
    log "copy $f to /boot"
    cp "$pdir/splash/$f" /boot || errExit "unable to copy $f to boot"
  done
  # (2) adapt cmdline.txt for fewer messages
  if grep -q logo.nologox /boot/cmdline.txt ; then
    log "/boot/cmdline OK"
  else
    log "change /boot/cmdline"
    needsReboot=1
    sed -i 's/.*/& logo.nologo splash silent quiet vt.global_cursor_default=0/' /boot/cmdline.txt || errExit "unable to modify /boot/cmdline.txt"  
  fi
  # (3) create a service to show second splash image
  # as soon as the driver initialization is done
  serviceData="`cat \"$pdir/splash/$service\"`"
  replaceConfig "$servicefile" "$serviceData"
  checkRes
  systemctl enable $service

  # (4) add an xinit scipt to be called very early
  # this will show the 3rd splash image now on X
  replaceConfig "$xinitfile" "$XINITRC"
  if [ $? -lt 0 ] ; then
    err "unable to create $xinitfile"
  fi
  chown -R "$xinituser" "$xinitdir" || err "unable to change ownership for $xinitdir"

  # (5) disable login on tty1
  systemctl disable getty@tty1.service

  if [ -x "$ENSCRIPT" ] ; then
    log "activating plugins $P1 and $P2"
    "$ENSCRIPT" unhide "$P1" || errExit "unable to set config"
    "$ENSCRIPT" unhide "$P2" || errExit "unable to set config"
    log "setting default parameters for $P2"
    "$ENSCRIPT" set "$P1" irqPin 13 || errExit "unable to set config"
    "$ENSCRIPT" set "$P1" i2cAddress 36 || errExit "unable to set config"  
    "$ENSCRIPT" set "$P1" ENTER z || errExit "unable to set config"  
  fi
  
fi
if [ "$1" != $MODE_DIS ] ; then
  POWEROFF="$pdir/enablePowerOff.sh"
  if [ -x "$POWEROFF" ] ; then
    log "enabling auto power off"
    "$POWEROFF"
  fi
fi
if [ "$1" = $MODE_DIS ] ; then
  log "disable OBPPLOTTERV3"
  removeConfig "$BOOTCONFIG" "$PATTERN"
  removeConfig /etc/modules "$PATTERN"
  systemctl disable service=obpplotterv3.service
  rm -f "$servicefile"
  rm -f "$xinitfile"
  if [ -x "$ENSCRIPT" ] ; then
    "$ENSCRIPT" hide "$P2"
  fi
  exit 0
else
  exit $needsReboot
fi
exit 0


exit $ret


