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
    startyear = 1777
    confpath = ''
    firstrun = False


    try:
        opts, args = getopt.getopt(argv,"hc:y:FD",["config=","startyear","firstrun=","debug=",])
    except getopt.GetoptError:
        print ('imbot_scan.py -c <config> -y <startyear> -F <firstrun>')
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
            print ('imbot_scan requires magpy >= 2.0.0')
            print ('-------------------------------------')
            print ('Usage:')
            print ('python3 imbot_scan.py -c <config>')
            print ('-------------------------------------')
            print ('Options:')
            print ('-c            : imbot config file')
            print ('-y            : ignore/reset all modifications before this startyear')
            print ('-------------------------------------')
            print ('Example of memory:')
            print ('-------------------------------------')
            print ('Application:')
            print ('-------------------------------------')
            print ('- debug mode')
            sys.exit()
        elif opt in ("-c", "--config"):
            confpath = os.path.abspath(arg)
        elif opt in ("-y", "--startyear"):
            startyear = int(arg)
        elif opt in ("-F", "--firstrun"):
            firstrun = True
        elif opt in ("-D", "--debug"):
            debug = True

    if confpath:
        config = methods.get_conf(confpath)
    else:
        print ("No config path provided - assuming testrun - make sure to run unittest by python steps.py first")
        config = {}
    # Starting preparations based on imbot_steps
    imostatus = steps.botstatus(config=config)  # allow for testrun which does not update operative imostatus
    imostatus = imostatus.analyse_source(imostatus.config.get('minute_step1'), step=1, type='minute', debug=debug)
    imostatus = imostatus.analyse_source(imostatus.config.get('second_step1'), step=1, type='second', debug=debug)
    imostatus = imostatus.analyse_source(imostatus.config.get('minute_step2'), step=2, type='minute', debug=debug)
    imostatus = imostatus.analyse_source(imostatus.config.get('second_step2'), step=2, type='second', debug=debug)
    imostatus = imostatus.analyse_source(imostatus.config.get('minute_step3'), step=3, type='minute', debug=debug)
    #imostatus = imostatus.analyse_source(imostatus.config.get('second_step3'), step=3, type='second', debug=debug)

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
                    imolayer = imostatus._get_step_information(imolayer, step=3, obscode=obs, debug=debug)
                    imolayer = imostatus._get_step_information(imolayer, step=2, obscode=obs, debug=debug)
                    imolayer = imostatus._get_step1_information(imolayer, obscode=obs, debug=debug)
                    #imolayer = imostatus._get_step_information(imolayer, step=2, obscode=obs, debug=debug)
                    #imolayer = imostatus._get_step_information(imolayer, step=3, obscode=obs, debug=debug)
                    imostatus = imostatus.set_contacts(year=year, resolution=restype, obscode=obs)
                    if firstrun:
                        # reset all inputs, remove "new" flags
                        imostatus = imostatus.set_modification(set='', year=year, resolution=restype, obscode=obs)
                    if startyear and not startyear == 1777:
                        if int(year) < int(startyear):
                            # ignore/reset all modifications for years before startyear
                            imostatus = imostatus.set_modification(set='', year=year, resolution=restype, obscode=obs)

                #imostatus = imostatus.update_validity(year=year, resolution=restype, excludeobs=['CNB', 'XYZ'])

    methods.write_memory(imostatus.result, path=imostatus.config.get('memory_directory_analysis'), debug=debug)

    print("Directory evaluation and memory update finished")
    print("Please note: existing modification flags are NOT changed")
    if debug:
        print (imostatus.result)

if __name__ == "__main__":
   main(sys.argv[1:])
