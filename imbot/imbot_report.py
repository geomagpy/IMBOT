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
from imbot.core import report
import getopt
import sys
import os

def main(argv):
    debug = False
    config = {}
    confpath = ''
    job = ''
    year=2022
    telmsg = ""


    try:
        opts, args = getopt.getopt(argv,"hc:j:y:D",["config=","job=","year=","debug=",])
    except getopt.GetoptError:
        print ('imbot_report.py -c <config> -j <job> -y <year>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('-------------------------------------')
            print ('Description:')
            print ('-- imbot_report.py will create reports from memory --')
            print ('-----------------------------------------------------------------')
            print ('imbot_report.py is a python3 program to ')
            print ('evaluate the IMBOT memory')
            print ('')
            print ('')
            print ('imbot_report requires imbot >= 2.0.0')
            print ('-------------------------------------')
            print ('Usage:')
            print ('python3 imbot_report.py -c <config>')
            print ('-------------------------------------')
            print ('Options:')
            print ('-c            : imbot config file')
            print ('-j            : report jobs:')
            print ('              : disk  ->  disk space of server')
            print ('              : the following jobs require -y year')
            print ('              : obslist  ->  all observatories')
            print ('              : secondlevel  ->  current level ')
            print ('              : last  ->  last modified submission ')
            print ('-y            : year')
            print ('-------------------------------------')
            print ('Example of memory:')
            print ('-------------------------------------')
            print ('Application:')
            print ('python imbot_report.py -c /home/leon/Tmp/GIN/conf/imbot_test.cfg -y 2022 -j disk,obslist,last')
            print ('-------------------------------------')
            sys.exit()
        elif opt in ("-c", "--config"):
            confpath = os.path.abspath(arg)
        elif opt in ("-j", "--job"):
            job = arg
        elif opt in ("-y", "--year"):
            year = int(arg)
        elif opt in ("-D", "--debug"):
            debug = True

    if not job:
        return
    jobs = job.split(",")
    if confpath:
        config = methods.get_conf(confpath)
    else:
        print ("No config path provided - assuming testrun - make sure to run unittest by python steps.py first")
        config = {}
    # Starting preparations based on imbot_steps
    imostatus = steps.botstatus(config=config)  # allow for testrun which does not update operative imostatus
    # Get stats for one-minute
    minstats = imostatus.yearly_stats(resolution='minute')
    # Get stats for one-second
    secstats = imostatus.yearly_stats(resolution='second')

    if "disk" in jobs:
        telmsg += report.imbot_disk_usage(archive="/srv/imbot", warnlevel=20, critlevel=10)
        telmsg += "\n"
    if "last" in jobs:
        telmsg += "Last uploads:\n"
        telmsg += "\nMinute | Date\n"
        telmsg += "------ | ----\n"
        telmsg += report.get_last_updates(minstats, startyear=year)
        telmsg += "\nSecond | Date\n"
        telmsg += "------ | ----\n"
        telmsg += report.get_last_updates(secstats, startyear=year)
    if year:
        if "secondlevel" in jobs:
            telmsg += report.observatory_list(secstats, year=year, levels=True)
            telmsg += "\n"
        if "obslist" in jobs:
            telmsg += "Minute:\n"
            telmsg += report.observatory_list(minstats, year=year, levels=False)
            telmsg += "Second:\n"
            telmsg += report.observatory_list(secstats, year=year, levels=False)
            telmsg += "\n"
    else:
        print ("Your selected job requires a year -  please provide")

    # USE JUPYTER NOTEBOOK for graphical reports
    #imostatus.referee_assignment(startyear=2016, resolution='second', referee=referee)

    #plt = report.yearly_stats(secstats, display="level", years=['2016', '2022'])

    #displaylist = ['INTERMAGNET CDF FORMAT; 1.X', 'INTERMAGNET CDF FORMAT; 1.2', 'INTERMAGNET CDF FORMAT; 1.1',
    #               'IAGA-2002', 'INTERMAGNET CDF FORMAT; 1.3']
    # displaylist = ["N_step1","N_step2","N_step2accepted","N_step3"]
    # displaylist = ["Level0","Level1","Level2"]
    #year = 2016
    #plt = report.pie_chart(secstats, year, displaylist)

    #plt = report.noiselevel_plot(secstats, year=2016, debug=False)
    # plt.savefig("/home/leon/Software/IMBOT/imbot/documentation/bar_levels.png")

    print("Report generation finished")
    if debug:
        print (telmsg)
    else:
        methods.sendtelegram(telmsg, configpath=imostatus.config.get('telegramconfig'))

if __name__ == "__main__":
   main(sys.argv[1:])
