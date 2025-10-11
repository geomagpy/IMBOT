#!/usr/bin/env python3
# coding=utf-8

"""
IMBOT - automatic analysis of one minute data

"""
import sys
sys.path.insert(1,'/home/leon/Software/IMBOT/') # should be magpy2

from imbot.core import steps
from imbot.core import methods
from imbot.core import report
from datetime import datetime, timedelta
from magpy.core.methods import testtime

import getopt
import sys
import os

def main(argv):
    debug = False
    test = False
    confpath = ''
    config = {}
    typ = "bar"
    res = 'second'
    imo = "WIC"
    year = year = datetime.now().year - 1
    levels = False

    try:
        opts, args = getopt.getopt(argv,"hc:r:i:t:y:TD",["config=","resolution=","imo","type=","year=","test=","debug=",])
    except getopt.GetoptError:
        print ('imbot_analysis.py -c <config>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('-------------------------------------')
            print ('Description:')
            print ('-- imbot_chart.py will create simple charts --')
            print ('-----------------------------------------------------------------')
            print ('imbot_chart.py is a python3 program to generate charts for IMBOT')
            print ('analyses. Charts can be viewed using MARTAS telegrambot options.')
            print ('')
            print ('')
            print ('imbot_chart.py requires magpy >= 2.0.0')
            print ('-------------------------------------')
            print ('Usage:')
            print ('python3 imbot_chart.py -c <config>')
            print ('-------------------------------------')
            print ('Options:')
            print ('-c            : imbot config file')
            print ('-r            : resolution : minute or second')
            print ('-i            : imo - obscode')
            print ('-t            : type : bar, imo or list')
            print ('              :        bar creates a bar chart of 5 years before given year with level or step')
            print ('              :        imo will print the current memory content for the selected Obs')
            print ('              :        list will plot all Obscodes for the selected year')
            print ('-y            : year. ')
            print ('-------------------------------------')
            print ('Example of memory:')
            print ('-------------------------------------')
            print ('Application:')
            print ('-------------------------------------')
            print ('- request memory information for a specific imo')
            print ('python3 imbot_chart.py -c /home/leon/.imbot/conf/imbot.cfg -t imo -i DOU -y 2022 -r minute')
            print ('- bar chart - for the last five years')
            print ('python3 imbot_chart.py -c /home/leon/.imbot/conf/imbot.cfg -t bar -r second')
            print ('- observatory list for 2023')
            print ('python3 imbot_chart.py -c /home/leon/.imbot/conf/imbot.cfg -t list -y 2023 -r second')
            sys.exit()

        elif opt in ("-c", "--config"):
            confpath = os.path.abspath(arg)
        elif opt in ("-r", "--resolution"):
            res = arg
        elif opt in ("-i", "--imo"):
            imo = arg
        elif opt in ("-t", "--type"):
            typ = arg
        elif opt in ("-y", "--year"):
            year = arg
        elif opt in ("-D", "--debug"):
            debug = True

    if confpath:
        config = methods.get_conf(confpath)
    else:
        print ("No config path provided - setting testrun to True")
        test = True
        config = {}

    imostatus = steps.botstatus(config=config)
    if res == 'minute':
        stats = imostatus.yearly_stats(resolution='minute')
        display = 'step'
        levels = False
    else:
        stats = imostatus.yearly_stats(resolution='second')
        display = 'level'
        levels = True

    # dsiplay can be "steps" or "level"
    if typ == 'bar':
        years = [year-4,year-3,year-2,year-1,year]
        years = [str(y) for y in years]
        plt = report.yearly_stats(stats,display=display, years=years)
        #plt.show()
        plt.savefig("/tmp/bar_levels.png")
    elif typ == 'imo':
        text = imostatus.get_imo(year=year, resolution=res, obscode=imo)
        fi = text.get('files')
        text['files'] = list(fi.keys())[0]
        import pandas as pd
        s = pd.Series(text)
        df = s.explode().reset_index(name='content')
        #df = pd.DataFrame(text)
        markdown_table = df.to_markdown(index=False)
        print(markdown_table)
    elif typ == 'list':
        ores = report.observatory_list(stats, year=year, levels=levels)
        print(ores)


if __name__ == "__main__":
   main(sys.argv[1:])
