#!/bin/bash

# Get starttime and date and calculate duration per GB
# Download one second data
# ------------------------
source /home/USER/.imbot/ginsource.sh

# step1
for i in {2018..2050} ; do wget -m -nH -np --cut-dirs=1 --user=$SECSTEP1USER --password=$SECSTEP1PWD ftp://par-gin.ipgp.fr/"$i"_step1 -P /srv/imbot/second/step1/"$i"/ ; done
# step2
MOUNTLEVEL=/mnt/level
STEP2DIR=/srv/imbot/second/step2
RSYNC=/usr/bin/rsync

# MOUNT REMOTE STEP2 DIRECTORY
curlftpfs -o user=$SECSTEP2FULL,allow_other $GINIP $MOUNTLEVEL

# Eventually create LOCAL DIRECTORY
mkdir -p $STEP2DIR

if grep -qs "$MOUNTLEVEL" /proc/mounts; then
  $RSYNC -avz -T "/tmp/" --no-perms --no-owner --no-group $MOUNTLEVEL $STEP2DIR
  umount $MOUNTLEVEL
  echo "GIN level unmounted"
