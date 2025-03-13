#!/usr/bin/env python3
# coding=utf-8

"""
IMBOT - automatic analysis of one minute data

"""
import sys
sys.path.insert(1, '/home/leon/Software/magpy/')  # should be magpy2
sys.path.insert(1,'/home/leon/Software/IMBOT/') # should be magpy2

from imbot.core import methods
from imbot.core import steps
import getopt
import sys
import os

def main(argv):
    debug = False
    config = {}
    confpath = ''
    firstrun = False


    try:
        opts, args = getopt.getopt(argv,"hc:FD",["config=","firstrun=","debug=",])
    except getopt.GetoptError:
        print ('imbot_scan.py -c <config> -F <firstrun>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('-------------------------------------')
            print ('Description:')
            print ('-- imbot_scan.py will automatically analyse one second data products --')
            print ('-----------------------------------------------------------------')
            print ('imbot_scan.py is a python3 program to automatically')
            print ('evaluate one second data submissions to INTERMAGNET.')
            print ('')
            print ('')
            print ('minuteanalysis requires magpy >= 0.9.5.')
            print ('-------------------------------------')
            print ('Usage:')
            print ('python3 minuteanalysis.py -s <source> -d <destination> -t <temporary>')
            print ('-------------------------------------')
            print ('Options:')
            print ('-t            : temporary directory for conversion and analysis')
            print ('-m            : a json file with full path for "memory"')
            print ('-------------------------------------')
            print ('Example of memory:')
            print ('-------------------------------------')
            print ('Application:')
            print ('-------------------------------------')
            print ('- debug mode')
            print ('python3 /home/leon/Software/IMBOT/imbot/minuteanalysis.py -s /home/leon/Cloud/Test/IMBOTminute/IMinput/2020_step1 -d /home/leon/Cloud/Test/IMBOTminute/IMoutput/ -t /tmp -m /home/leon/Cloud/Test/IMBOTminute/analysetest.json -n /etc/martas/telegram.cfg -e /home/leon/Software/IMBOTconfig -o DOU -w /home/leon/.wine/drive_c -D')
            print ('- test mode')
            print ('python3 minuteanalysis.py -s /home/leon/Tmp -t /tmp -d /tmp -o BOU -i /home/leon/Tmp/minute')
            print ('python3 secondanalysis.py -s /media/leon/Images/Mag2020 -d /tmp -t /media/leon/Images/DataCheck/tmp -i /media/leon/Images/DataCheck/2016/minute/Mag2016 -m /media/leon/Images/DataCheck/2016/testanalysis.json -o WIC')
            print ('python3 minuteanalysis.py -s /media/leon/Images/Mag2020 -d /tmp -t /tmp -o CLF -e /home/leon/IMBOT/minute -D')
            sys.exit()
        elif opt in ("-c", "--config"):
            confpath = os.path.abspath(arg)
        elif opt in ("-F", "--firstrun"):
            firstrun = True
        elif opt in ("-D", "--debug"):
            debug = True

    if confpath:
        config = methods.get_conf(confpath)
    else:
        config = {}
    # Starting preparations based on imbot_steps
    imostatus = steps.botstatus(config=config)  # allow for testrun which does not update operative imostatus
    imostatus = imostatus.analyse_source(imostatus.config.get('minute_step1'), step=1, type='minute', debug=debug)
    imostatus = imostatus.analyse_source(imostatus.config.get('second_step1'), step=1, type='second', debug=debug)

    yearlist = [el for el in imostatus.result]
    for year in yearlist:
        for restype in ['minute', 'second']:
            obsdata = imostatus.result.get(year).get(restype)
            if obsdata:
                obslist = [el for el in obsdata]
                for obs in obslist:
                    if debug:
                        print(obs, restype, year)
                    imolayer = obsdata.get(obs)
                    imolayer = imostatus._get_step1_information(imolayer, obscode=obs, debug=debug)
                    imostatus = imostatus.set_contacts(year=year, resolution=restype, obscode=obs)
                    if firstrun:
                        # reset all inputs, remove "new" flags
                        imostatus = imostatus.set_modification(set='', year=year, resolution=restype, obscode=obs)
                imostatus = imostatus.update_validity(year=year, resolution=restype, excludeobs=['CNB', 'XYZ'])

    methods.write_memory(imostatus.result, path=imostatus.config.get('memory_directory_analysis'), debug=debug)

    print("Directory evaluation and memory update finished")
    print("Please note: modification flags are NOT changed")
    if debug:
        print (imostatus.result)

if __name__ == "__main__":
   main(sys.argv[1:])
