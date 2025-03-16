#!/bin/bash

# Get starttime and date and calulate duration per GB
# Download one second data
# ------------------------
source /home/leon/ginsource.sh
# GINSOURCE looks like
# SECSTEP2USER='user'
# SECSTEP2pwd='secret'
# GINSECSTEP2='cdfsteptwo:86XaqU%'

# step1
for i in {2018..2050} ; do wget -m -nH -np --cut-dirs=1 --user='user1sec' --password='71IUE2%f' ftp://par-gin.ipgp.fr/"$i"_step1 -P /srv/imbot/second/step1/"$i"/ ; done
# step2
MOUNTLEVEL=/mnt/level
STEP2DIR=/srv/imbot/second/step2
RSYNC=/usr/bin/rsync

# MOUNT LEVEL DIRECTORY
curlftpfs -o user=$GINSECSTEP2,allow_other $GINIP $MOUNTLEVEL

# Eventually create LEVEL DIRECTORY
mkdir -p $STEP2DIR

if grep -qs "$MOUNTLEVEL" /proc/mounts; then
  $RSYNC -avz -T "/tmp/" --no-perms --no-owner --no-group $MOUNTLEVEL $OUT
  umount $MOUNTLEVEL
  echo "GIN level unmounted"
