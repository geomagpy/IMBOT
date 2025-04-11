
source /home/cobs/env/magpy/bin/activate

# scan all step folders
imbot_scan -c /home/cobs/.imbot/conf/imbot.cfg

# analyse minute and second
imbot_analysis -c /home/cobs/.imbot/conf/imbot.cfg
