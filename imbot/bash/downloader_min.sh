#!/bin/bash

source /home/cobs/env/magpy/bin/activate

# Download one minute data
# ------------------------
source /home/USER/.imbot/ginsource.sh

YEAR=$(date +%Y)

# step1
for ((i=2010;i<=$YEAR;i++)) ; do wget -m -nH -np --cut-dirs=1 --user=$MINSTEP1USER --password=$MINSTEP1PWD ftp://par-gin.ipgp.fr/Mag"$i" -P /srv/imbot/minute/step1/Mag"$i"/ ; done
# step2
for ((i=2010;i<=$YEAR;i++)) ; do wget -m -nH -np --cut-dirs=1 --user=$MINSTEP2USER --password=$MINSTEP2PWD ftp://par-gin.ipgp.fr/mag"$i" -P /srv/imbot/minute/step2/mag"$i"/ ; done
# step3
wget -m -nH -np --cut-dirs=2 --user=$MINSTEP3USER --password=$MINSTEP3PWD ftp://par-gin.ipgp.fr/pub/intermag -P /srv/imbot/minute/step3raw/
# Run the conversion script to get a step like structure for step3 data
imbot_convert -s "/srv/imbot/minute/step3raw/" -d "/srv/imbot/minute/step3"
# end with success
echo "SUCCESS"