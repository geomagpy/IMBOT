#!/usr/bin/env python3
# coding=utf-8

"""
IMBOT - automatic analysis of one minute data

"""
import sys
sys.path.insert(1, '/home/leon/Software/magpy/')  # should be magpy2
sys.path.insert(1,'/home/leon/Software/IMBOT/') # should be magpy2

from magpy.stream import magpyversion
from imbot.core import steps
from imbot.core import methods
from imbot.analysis import minute
from imbot.analysis import second
from datetime import timedelta
import shutil
import getopt
import sys
import os

def main(argv):
    debug = False
    test = False
    confpath = ''
    config = {}
    telmsg = ''
    nomail = False
    maxamount = 40
    resolution = ''
    year = None
    repeatobs = []
    excludeobs = ''
    includeobs = ''
    successminnew = []
    successminupd = []
    failedmin = []
    successsecnew = []
    successsecupd = []
    failedsec = []

    try:
        opts, args = getopt.getopt(argv,"hc:s:r:y:m:NTD",["config=","sampling=","repeat=","year=","maxamount=","no-mail=","test=","debug=",])
    except getopt.GetoptError:
        print ('imbot_analysis.py -c <config>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('-------------------------------------')
            print ('Description:')
            print ('-- imbot_analysis.py will automatically analyse step1 data products --')
            print ('-----------------------------------------------------------------')
            print ('imbot_analysis.py is a python3 program to automatically')
            print ('evaluate data submissions to INTERMAGNET.')
            print ('')
            print ('')
            print ('imbot_analysis.py requires magpy >= 2.0.0')
            print ('-------------------------------------')
            print ('Usage:')
            print ('python3 imbot_analysis.py -c <config>')
            print ('-------------------------------------')
            print ('Options:')
            print ('-c            : imbot config file')
            print ('-s            : sampling rate: analyze minute and second on default.')
            print ('              : set to "minute" or "second" to limit analyses.')
            print ('-r            : redo/repeat list, provide a list of obscode which will')
            print ('              : flagged as new records and reanalyzed')
            print ('-y            : year. only used together with redo/repeat list')
            print ('-m            : maximum amount of tolerated changed files, default = 40')
            print ('                 - if larger, then nothing is done')
            print ('-N            : NO e-mail notification send to IMOs.')
            print ('-------------------------------------')
            print ('Example of memory:')
            print ('-------------------------------------')
            print ('Application:')
            print ('-------------------------------------')
            print ('- debug mode - will not send reports but print them to stdout, no memory update')
            print ('python3 imbot_analysis.py -c ~/imbot.cfg -D')
            print ('- test mode - will send reports only to sysadmin, no memory update')
            print ('python3 imbot_analysis.py -c ~/imbot.cfg -T')
            print ('- no IMO mail - will send reports only to sysadmin')
            print ('python3 imbot_analysis.py -c ~/imbot.cfg -N')
            print ('- repeat mode - will flag IMO for second period and year 2022 as new')
            print ('python3 imbot_analysis.py -c ~/imbot.cfg -r WIC,KOU,CLF -s second -y 2022')
            """
            TODO - but that should be done in imbot_scan
            print ('-e            : exclude path. Provide a path to a exclude json structure')
            print ('              : containing year, resolution and obslist to be ignored.')
            print ('              : Include again by using -i to change its exclude state.')
            print ('-i            : include path.')
            """
            sys.exit()

        elif opt in ("-c", "--config"):
            confpath = os.path.abspath(arg)
        elif opt in ("-s", "--sampling"):
            resolution = arg
        elif opt in ("-r", "--repeat"):
            repeatobs = arg.split(',')
        elif opt in ("-y", "--year"):
            year = arg
        elif opt in ("-m", "--maxamount"):
            maxamount = int(arg)
        elif opt in ("-N", "--no-mail"):
            nomail = True
        elif opt in ("-T", "--test"):
            test = True
        elif opt in ("-D", "--debug"):
            debug = True

    if confpath:
        config = methods.get_conf(confpath)
    else:
        print ("No config path provided - setting testrun to True")
        test = True
        config = {}

    if test:
        telmsg = 'TESTRUN - not operative\n'

    # Now initialize IMBOT and read the current memory list as defined in config
    imostatus = steps.botstatus(config=config)
    # a pure runtime test requires the execution of unittest by "python steps.py" first
    # This will create a temporary structure with dummy configurations and a minute test submission

    # eventually use update_validity to exclude data sets from analysis
    # imostatus = imostatus.update_validity(year=2022, resolution='second', includeobs=['CNB'])

    # eventually update the modification list based on resolution, year and obslist
    if len(repeatobs) > 0:
        for obs in repeatobs:
            imostatus = imostatus.set_modification(set='new', obscode=obs,
                                                   year=year, resolution=resolution)
    # Analyse memory and extract all modified data sets
    # get all (year, resolution, obscode) with modification flags and exclude=False
    modlist = imostatus.get_modified()

    # Now copy data to be analyzed to a temporary directory (why? because some data is packed/zipped/tared) only second?
    modificationlist = methods.copy_temporary(modlist, tmpdir=config.get("temporary_dir","/tmp/imbottest"), debug=False)
    # tmpdir will look like os.path.join(tmpdir, 'unpacked', year, resolution, obscode)

    # Please note: modificationlist will only contain new/update flags. step2/step3 additions will be dropped as they are not analyzed
    # Final preparations: limit the amount of second data sets treated in this run and add current
    # maximum minute state+path to second analyses

    # update one-second input for efficient analysis and necessary one-minute step information
    modificationlist = imostatus.add_minute_state(modificationlist, debug=False)
    if len(modificationlist) > maxamount:
        print("It is very unlikely that more than 40 data sets have been uploaded in one day")
        print("Abort and inform sysadmin")
        telmsg = 'More than 40 records found to be analyzed - seems unlikely, aborting'
        methods.sendtelegram(telmsg, imostatus.config.get('telegramconfig'))

    modificationlist = methods.limit_second_obs(modificationlist, limit=3, debug=False)

    for dataset in modificationlist:
        # modificationlist only contains new and updated flags
        if debug:
            print("Running analysis for {},{} with {} resolution".format(dataset.get("obscode"), dataset.get("year"),
                                                                         dataset.get("resolution")))
        if dataset.get('modification') in ['new', 'updated']:  # don't analyse "updated but already accepted"
            if dataset.get('resolution') == 'minute' and resolution in ['','minute']:
                try:
                    minana = minute.minute_definitive(input=dataset)
                    reportpath = minana.DOS_check1min(debug=False)
                    level = minana.MagPy_check1min(debug=False)
                    imodict = imostatus.get_imo(obscode=minana.input.get('obscode'), year=minana.input.get('year'),
                                                resolution='minute')
                    maildict = minana.minute_mail_text(level, imodict, reportpath=reportpath)
                    imostatus = imostatus.add_content(obscode=minana.input.get('obscode'), year=minana.input.get('year'),
                                                      resolution='minute', name='maildict_minute', content=maildict)
                    imostatus = imostatus.set_modification(set='', obscode=minana.input.get('obscode'),
                                                           year=minana.input.get('year'), resolution='minute')
                    if not debug and not test:
                        methods.write_memory(imostatus.result, path=imostatus.config.get('memory_directory_analysis'),
                                         debug=True)
                    if debug:
                        print (maildict)
                    else:
                        if test or nomail:
                            maildict['to'] = maildict.get('from')
                        methods.sendmail(maildict, credentials=imostatus.config.get('emailcredentials'))
                    # delete temporary directories
                    mintempdir = minana.input.get('temporaryfolder')
                    if os.path.exists(mintempdir):
                        shutil.rmtree(mintempdir)
                    if dataset.get('modification') in ['new']:
                        successminnew.append(dataset.get('obscode'))
                    else:
                        successminupd.append(dataset.get('obscode'))
                except:
                    failedmin.append(dataset.get('obscode'))
            elif dataset.get('resolution') == 'second' and resolution in ['','second']:
                try:
                    secana = second.second_definitive(input=dataset)
                    datelist = secana.get_months()
                    secana.logdict['MagPyVersion'] = magpyversion
                    # Monthly checks
                    if debug:
                        datelist = datelist[:1]
                    daystreams = []
                    for i, dates in enumerate(datelist):
                        data, allcontents = secana.read_month(dates, debug=False)
                        month = (data.start() + timedelta(days=10)).strftime("%m (%b)")
                        secana.delta_f_test(data)
                        mtable = secana.check_standard_level(data, partialcheck=methods.partialcheck_v1, debug=False)
                        quietdays = secana.check_diff_to_minute(data, daterange=datelist[0], debug=False)
                        daystreams.extend(secana.extract_selected_days(data, datelist[0],
                                                                       selecteddays=quietdays, dayformat='text',
                                                                       debug=False))
                        secana.export_month(data, allcontents, debug=False)
                        if len(secana.logdict.get(month).get('Issues')) > 0 and not secana.logdict.get('Level') == 0:
                            secana.logdict['Level'] = 1
                        if debug:
                            print(secana.logdict.get(month).get('Issues'))
                            print(secana.logdict.get(month).get('Warnings'))
                    print("   month second analysis finished")
                    # select day checks
                    if len(daystreams) > 0:
                        secana.psd_analysis(daystreams)
                        tablelist = secana.update_table(mtable, month)
                    # write the report (mtable is just needed once)
                    level = secana.write_report(tablelist=tablelist, debug=False)
                    imodict = imostatus.get_imo(obscode=secana.input.get('obscode'), year=secana.input.get('year'),
                                                resolution='second')
                    maildict = secana.second_mail_text(level, imodict)
                    imostatus = imostatus.add_content(obscode=secana.input.get('obscode'), year=secana.input.get('year'),
                                                      resolution='second', name='maildict_second', content=maildict)
                    imostatus = imostatus.set_modification(set='', obscode=secana.input.get('obscode'),
                                                           year=secana.input.get('year'), resolution='second')
                    if not debug and not test:
                        methods.write_memory(imostatus.result, path=imostatus.config.get('memory_directory_analysis'),
                                         debug=True)
                    if debug:
                        print (maildict)
                    else:
                        if test or nomail:
                            maildict['to'] = maildict.get('from')
                        methods.sendmail(maildict, credentials=imostatus.config.get('emailcredentials'))
                    # delete temporary directories
                    sectempdir = secana.input.get('temporaryfolder')
                    if os.path.exists(sectempdir):
                        shutil.rmtree(sectempdir)
                    if dataset.get('modification') in ['new']:
                        successsecnew.append(dataset.get('obscode'))
                    else:
                        successsecupd.append(dataset.get('obscode'))
                except:
                    failedsec.append(dataset.get('obscode'))

    for dataset in modlist:
        if debug:
            print(" Found the following mod:", dataset.get('modification'))
            print(dataset)
        if dataset.get('modification') in ['updated but already accepted']:
            pass
        elif dataset.get('modification') in ['added to step2']:
            contacts = imostatus.get_contact_mails(obscode=dataset.get('obscode'), year=dataset.get('year'))
            managers = imostatus.get_manager_mails()
            receivers = contacts + managers
            maildict = {'subject': "Submission one-{} {}, {} moved to step2".format(dataset.get('resolution'),dataset.get('obscode'),dataset.get('year')),
                        'text': "Dear data provider\nyour data submission has been moved to step2.\nSincerely,\n     IMBOT",
                        'to': receivers}
            if debug:
                print(maildict)
            else:
                if test or nomail:
                    maildict['to'] = maildict.get('from')
                methods.sendmail(maildict, credentials=imostatus.config.get('emailcredentials'))
            imostatus = imostatus.set_modification(set='', obscode=dataset.get('obscode'),
                                                   year=dataset.get('year'), resolution=dataset.get('resolution'))
        elif dataset.get('modification') in ['added to step3']:
            contacts = imostatus.get_contact_mails(obscode=dataset.get('obscode'), year=dataset.get('year'))
            managers = imostatus.get_manager_mails()
            receivers = contacts + managers
            maildict = {'subject': "Submission one-{} {}, {} moved to step3".format(dataset.get('resolution'),dataset.get('obscode'),dataset.get('year')),
                        'text': "Dear data provider\nyour data submission has been moved to step3 and will be published soon.\nSincerely,\n     IMBOT",
                        'to': receivers}
            if debug:
                print(maildict)
            else:
                if test or nomail:
                    maildict['to'] = maildict.get('from')
                methods.sendmail(maildict, credentials=imostatus.config.get('emailcredentials'))
            imostatus = imostatus.set_modification(set='', obscode=dataset.get('obscode'),
                                                   year=dataset.get('year'), resolution=dataset.get('resolution'))
        elif dataset.get('modification') in ['step2 reviewed']:
            managers = imostatus.get_manager_mails()
            receivers = managers
            maildict = {'subject': "Submission one-{} {}, {} has been reviewed".format(dataset.get('resolution'),dataset.get('obscode'),dataset.get('year')),
                        'text': "Dear managers\na step2 data has been reviewed and is ready for final decisions.\nSincerely,\n     IMBOT",
                        'to': receivers}
            if debug:
                print(maildict)
            else:
                if test or nomail:
                    maildict['to'] = maildict.get('from')
                methods.sendmail(maildict, credentials=imostatus.config.get('emailcredentials'))
            imostatus = imostatus.set_modification(set='', obscode=dataset.get('obscode'),
                                                   year=dataset.get('year'), resolution=dataset.get('resolution'))

    if len(successminnew) > 0:
        telmsg += "New minute: {}\n".format(",".join(successminnew))
    if len(successminupd) > 0:
        telmsg += "Updated minute: {}\n".format(",".join(successminupd))
    if len(successsecnew) > 0:
        telmsg += "New second: {}\n".format(",".join(successsecnew))
    if len(successsecupd) > 0:
        telmsg += "Updated second: {}\n".format(",".join(successsecupd))
    if len(failedmin) > 0:
        telmsg += "Failed minute: {}\n".format(",".join(failedmin))
    if len(failedsec) > 0:
        telmsg += "Failed second: {}\n".format(",".join(failedsec))

    if debug:
        print(telmsg)
    else:
        methods.sendtelegram(telmsg, configpath=imostatus.config.get('telegramconfig'))
    print("SUCCESS")  # used for monitoring of logfile
    # end of analysis

if __name__ == "__main__":
   main(sys.argv[1:])
