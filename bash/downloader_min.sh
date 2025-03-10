#!/bin/bash

# Download one minute data
# ------------------------
# step1
for i in {2010..2050} ; do wget -m -nH -np --cut-dirs=1 --user='userint' --password='*lanceIs#1' ftp://par-gin.ipgp.fr/Mag"$i" -P /srv/imbot/minute/step1/Mag"$i"/ ; done
# step2
for i in {2010..2050} ; do wget -m -nH -np --cut-dirs=1 --user='steptwo' --password='@AlpdHuez01' ftp://par-gin.ipgp.fr/mag"$i" -P /srv/imbot/minute/step2/mag"$i"/ ; done
# step3
wget -m -nH -np --cut-dirs=2 --user='obsmag' --password='*lanceIs#1' ftp://par-gin.ipgp.fr/pub/intermag -P /srv/imbot/minute/step3raw/