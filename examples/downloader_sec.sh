#!/bin/bash

# Get starttime and date and calulate duration per GB
# Download one second data
# ------------------------
# step1
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/2023_step1 -P /srv/imbot/second/step1/2023/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/2022_step1 -P /srv/imbot/second/step1/2022/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/2021_step1 -P /srv/imbot/second/step1/2021/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/2020_step1 -P /srv/imbot/second/step1/2020/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/2019_step1 -P /srv/imbot/second/step1/2019/
