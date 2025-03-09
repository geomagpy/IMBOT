#!/bin/bash

# Get starttime and date and calulate duration per GB
# Download one second data
# ------------------------
# step1
for i in {2018..2050} ; do wget -m -nH -np --cut-dirs=1 --user='user1sec' --password='71IUE2%f' ftp://par-gin.ipgp.fr/"$i"_step1 -P /srv/imbot/second/step1/"$i"/ ; done
# step2
