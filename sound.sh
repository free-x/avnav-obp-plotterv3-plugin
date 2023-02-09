#! /bin/sh
#play a sound with setting the volume before
echo "obp-plotterv3: playing $2 with volume $1"
amixer  cset numid=1 $1
mpg123 -q $2
