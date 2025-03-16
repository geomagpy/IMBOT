#!/usr/bin/env python3
# coding=utf-8

"""
IMBOT - automatic analysis of one minute data

imbot_init will create folders, setup all configuration files, eventually install dependencies

"""
import sys
sys.path.insert(1, '/home/leon/Software/magpy/')  # should be magpy2
sys.path.insert(1,'/home/leon/Software/IMBOT/') # should be magpy2

import shutil
import getopt
import sys
import os

def main(argv):
    debug = False

    try:
        opts, args = getopt.getopt(argv,"hD",["debug=",])
    except getopt.GetoptError:
        print ('imbot_init.py')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('-------------------------------------')
            print ('Description:')
            print ('-- imbot_init.py will initialize imbot configuration --')
            print ('-----------------------------------------------------------------')
            print ('imbot_init.py will perform the following tasks:')
            print ('- create a ~/.imbot directory')
            print ('- copy skeleton configuration files to .imbot/conf/')
            print ('- copy bash scripts to .imbot/conf/')
            print ('- check for wine and eventually copy check1min')
            print ('')
            print ('-------------------------------------')
            print ('Application:')
            print ('-------------------------------------')
            print ('python3 imbot_init.py')
            sys.exit()
        elif opt in ("-D", "--debug"):
            debug = True

    # get home directory of current user
    homedir = os.getenv("HOME")
    print(homedir)
    # create .imbot
    if not debug:
        os.makedirs(os.path.join(homedir,".imbot"), exist_ok=True)
        # create sudirs
        os.makedirs(os.path.join(homedir,".imbot","log"), exist_ok=True)
    #
    # copy files into subdirs
    if not os.path.isdir(os.path.join(homedir,".imbot","conf")):
        shutil.copytree("../config", os.path.join(homedir,".imbot","conf"))
    if not os.path.isdir(os.path.join(homedir,".imbot","bash")):
        shutil.copytree("../bash", os.path.join(homedir,".imbot","bash"))
    if not os.path.isdir(os.path.join(homedir,".imbot","app")):
        shutil.copytree("../external", os.path.join(homedir,".imbot/app"))
    if not os.path.isdir(os.path.join(homedir,".imbot","templates")):
        shutil.copytree("../templates", os.path.join(homedir,".imbot/templates"))
    #
    # check for wine and copy check1minute to it
    if not os.path.exists(os.path.join(homedir,".wine")):
        print ("PLEASE INSTALL WINE BEFORE CONTINUIUNG")
        print ("i.e. sudo apt install wine")
    else:
        if os.path.exists(os.path.join(homedir,".wine","drive_c","check1min.exe")):
            print (" Wine and check1min already installed - continuing")
        else:
            print ("copy check1min")
    print ("Now update all the configuration files manually")




    print("SUCCESS")  # used for monitoring of logfile
    # end of init

if __name__ == "__main__":
   main(sys.argv[1:])
