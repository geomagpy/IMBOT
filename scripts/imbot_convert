#!/usr/bin/env python3
# coding=utf-8

"""
IMBOT - automatic analysis of one minute data

imbot_convert will create a step like dictionary structure

"""
import sys
sys.path.insert(1, '/home/leon/Software/magpy/')  # should be magpy2
sys.path.insert(1, '//') # should be magpy2

from imbot.core import methods
import getopt
import sys
import os

def main(argv):
    debug = False
    prefix = "mag"
    source = "/home/leon/Tmp/GIN/step3raw"
    destination = "/home/leon/Tmp/GIN/step3minute"

    try:
        opts, args = getopt.getopt(argv,"hs:d:p:D",["source=","destination=","prefix=","debug=",])
    except getopt.GetoptError:
        print ('imbot_convert.py')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('-------------------------------------')
            print ('Description:')
            print ('-- imbot_convert.py will convert data into a step like dictionary structure --')
            print ('-----------------------------------------------------------------')
            print ('imbot_convert.py will perform the following tasks:')
            print ('-s  :  base source directory')
            print ('-d  :  base destination directory')
            print ('-p  :  prefix to be used with year i.e. "mag" for "mag2022"')
            print ('')
            print ('-------------------------------------')
            print ('Application:')
            print ('-------------------------------------')
            print ('python3 imbot_convert.py')
            sys.exit()
        elif opt in ("-s", "--source"):
            source = arg
        elif opt in ("-d", "--destination"):
            destination = arg
        elif opt in ("-p", "--prefix"):
            prefix = arg
        elif opt in ("-D", "--debug"):
            debug = True

    methods.convert_to_step_dir(source, destination, destlevel1_prefix=prefix,
                        debug=debug)

    print("SUCCESS")  # used for monitoring of logfile
    # end of init

if __name__ == "__main__":
   main(sys.argv[1:])
