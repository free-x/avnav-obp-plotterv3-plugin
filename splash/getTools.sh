#! /bin/bash
#get the tools for displaying the splash screen
GITREPO=https://gitlab.com/DarkElvenAngel/initramfs-splash/-/raw/master/boot/initramfs.img
TARGET=initramfs.img
pdir=`dirname $0`
err(){
    echo "ERROR: $*"
    exit 1
}
echo "downloading from $GITREPO"
TARGETFILE="$pdir/$TARGET"
rm -f "$TARGETFILE"
curl -o "$TARGETFILE" "$GITREPO" || err "unable to download"
[ ! -f "$TARGETFILE" ] && err "$TARGETFILE not found after download"
tool="bin/fbsplash"
toolpath="$pdir/$tool"
rm -f "$toolpath"
( cd $pdir && zcat "$TARGET" | cpio -i -d "$tool") || err "unable to extract fbsplash"
[ ! -f "$toolpath" ] && err "could not extract $toolpath"
echo "got $TARGET, $toolpath"






