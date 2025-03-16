#!/bin/bash

# DESCRIPTION
# -----------
# Basic bash script to mount Ftp directories locally, perform analysis and unmount afterwards.
# This bash script call the python application 'onesceondanalysis.py' using python3.
# If you are running this job as user please make sure to create the directories
# minute, second and to assign the user as owner
# GIN connection details are stored in a separate file called ginsource.sh (see below).
# Please change the rights on ginsource for some minimal protection: chmod 600 ginsource.sh
#
# PARAMETER and PREREQUISITES
# ---------------------------
# A basic prerequisite is python3 and the magpy package (>=0.9.7). Further recommended packages are 
# telegram_send (for notifications), ...
# You need to specify the following parameters
#  TMPDIR:      a local folder with at least 4 GB memory
#  DESTINATION: a local/remote folder to save the results to; within this folder, a subdir 'level' will be created.
#               Within the directory 'level', subdirectories for each Observatory will be established.
#               A large disk space is required here, suggested is > 1TB.
#  MEMORY:      a full path to a local file, which contains the memory of all performed analyses. Please make sure,
#              that this file is secure and accessible. Dont use a temporary folder.
#
# APPLICATION
# -----------
# Use a separate analysis script for each year. The analysis script should be scheduled to be run at least 
# once every day. The analysis of a single new one-second submission might need approximately one hour.
# Therefore, an execution of this script more often than every three hours is not advisable, if institutes upload 
# several data sets of multiple observatories at once.
#
# MONITORING
# -----------
# The script makes use of a small python application which allows for sending telegram notifications based on
# MARTAS () logging method, i.e. whenever a state is changing. You can also pipe the output of the script into a log 
# file and use other monitoring methods like Nagios etc for checking the run time state of the bash script.
#
# ginsource.sh:
# GINIP=194.254.225.100
# GINMIN='ftp-user:ftp-passwd'
# GINSEC='ftp-user:ftp-passwd'

YEAR=2022

MOUNTCODE="22S"

## QUIETDAYLIST: If provided then a frequency analysis is condicted and averaged for
##              all these days in order to estimate the noise level
# TODO replace with correct data as soon as calculated
QUIETDAYLIST='2022-01-13,2022-01-14,2022-01-19,2022-01-20,2022-01-25,2022-01-27,2022-02-03,2022-02-14,2022-02-16,2022-07-11,2022-07-12,2022-09-09,2022-09-10,2022-09-11,2022-10-09,2022-10-10,2022-10-11,2022-10-14,2022-11-09,2022-11-10,2022-11-14,2022-11-16,2022-11-18,2022-12-04,2022-12-07,2022-12-15,2022-12-18'


## OBSTESTLIST: If provided then full reporting is limited to these
##              observatories. For all other observatories reports
##              will be send to IMBOT manager only.
##              Enter "None" for productive runs i.e. if you don't want to use it.
OBSTESTLIST="None"

## OBSLIST: IF only specific OBS shoud be analyzed then provide them here.
##          If REFEREE is contained, then all observatories listed in
##          refereelist_second.cfg are used.
##          (plus the ones provided here along with REFEREE)
OBSLIST='REFEREE,WIC'


## ##########################################
##   Path definitions
## ##########################################

source /home/cobs/IMANALYSIS/Runtime/ginsource.sh

RSYNC=/usr/bin/rsync
PYTHON=/usr/bin/python3
APP=/home/cobs/Software/IMBOT/imbot/secondanalysis.py
NOTE=/home/cobs/Software/IMBOT/imbot/telegramnote.py
TELEGRAMCFG=/etc/martas/telegram.cfg
TELEGRAMLOG=/var/log/magpy/imbotsec${YEAR}.log

MOUNTLEVEL=/mnt/second/step2

DESTINATION="/srv/imbot/second/${YEAR}"
TMPDIR="${DESTINATION}/tmp/${YEAR}"
MEMORY="/home/cobs/IMANALYSIS/Datacheck/second/sec_analysis${YEAR}.json"
LOCALSOURCE="${DESTINATION}"/level

SOURCEDIR="/srv/imbot/second/step1/${YEAR}"
MINSTEP1="/srv/imbot/minute/step1/Mag${YEAR}"
MINSTEP2="/srv/imbot/minute/step2/mag${YEAR}"
MINSTEP3="/srv/imbot/minute/step3/mag${YEAR}"
LEVELDIR="${MOUNTLEVEL}"/"${YEAR}"

CFGDIR="/home/cobs/IMANALYSIS/Config"

mkdir -p $DESTINATION
mkdir -p $TMPDIR
mkdir -p "/home/cobs/IMANALYSIS/Datacheck/second"

# Please uncomment using # if you are not using Telegram notifications
$PYTHON $NOTE -t $TELEGRAMCFG -n "${MSG}" -l "IMBOTsecond${YEAR}" -p $TELEGRAMLOG
# ANALYSE - auto
$PYTHON $APP -s $SOURCEDIR -d $DESTINATION -t $TMPDIR -i $MINSTEP1 -j $MINSTEP2 -k $MINSTEP3 -m $MEMORY -n $TELEGRAMCFG -e $CFGDIR -q $QUIETDAYLIST -o $OBSLIST -p $OBSTESTLIST -y $YEAR
# The following two lines are used for weekly and daily monitoring
echo "=> ONE-SECOND DATA ANALYSIS SUCCESSFULLY FINISHED"
echo "Analysis performed"


## ##########################################
##   Upload LEVEL 2 results to step2 GIN (sec)
## ##########################################


# SELECT Only level 2 observatories
LEVEL2PATHS=$(find ${LOCALSOURCE}/* -type f -name 'level2*' | sed -r 's|/[^/]+$||' |sort |uniq)

# MOUNT LEVEL DIRECTORY
curlftpfs -o user=$GINSECSTEP2,allow_other $GINADDRESS $MOUNTLEVEL

if grep -qs "$MOUNTLEVEL" /proc/mounts; then
  mkdir -p $LEVELDIR

  for i in $(echo $LEVEL2PATHS)
  do
    NAME=$(basename $i)
    IN="${LOCALSOURCE}"/"${NAME}"/*
    OUT="${LEVELDIR}"/"${NAME}"
    echo "Transferring data for $NAME"
    $RSYNC -avz -T "/tmp" --size-only --no-perms --no-owner --no-group $IN $OUT
  done

  umount $MOUNTLEVEL
  echo "GIN LEVEL unmounted"
else
  MSG="GIN Level directories could not be mounted."
  echo $MSG
  # Please uncomment using # if you are not using Telegram notifications
  $PYTHON $NOTE -t $TELEGRAMCFG -n "${MSG}" -l "IMBOTupload${YEAR}" -p $TELEGRAMLOG
fi

