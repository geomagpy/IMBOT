#!/bin/bash

# Download one minute data
# ------------------------
# step1
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/Mag2023 -P /srv/imbot/minute/step1/Mag2023/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/Mag2022 -P /srv/imbot/minute/step1/Mag2022/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/Mag2021 -P /srv/imbot/minute/step1/Mag2021/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/Mag2020 -P /srv/imbot/minute/step1/Mag2020/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/Mag2019 -P /srv/imbot/minute/step1/Mag2019/
# step2
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/mag2023 -P /srv/imbot/minute/step2/mag2023/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/mag2022 -P /srv/imbot/minute/step2/mag2022/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/mag2021 -P /srv/imbot/minute/step2/mag2021/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/mag2020 -P /srv/imbot/minute/step2/mag2020/
wget -m -nH -np --cut-dirs=1 --user='user' --password='secret' ftp://par-gin.ipgp.fr/mag2019 -P /srv/imbot/minute/step2/mag2019/
