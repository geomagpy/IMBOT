# -*- coding: utf-8 -*-

import sys
sys.path.insert(1, '/home/leon/Software/magpy/')  # should be magpy2
sys.path.insert(1,'/home/leon/Software/IMBOT/') # should be magpy2

import os
import subprocess
import time
import glob
import shutil
from magpy.stream import read
from imbot.core import steps
from imbot.core import methods
import unittest

class minute_definitive(object):
    """
    DESCRIPTION
        Analysis class for one-minute data

    VARIABLES
        modificationdict :  contains a single dictionary with one minute contents to be analyzed
        report  : list  : contains report messages acquired during runtime - to be used for logging
        config  : dict  : contains basic parameters and path definitions for the specfic application. Conif data should be read
                          from a dedicated configuration file of the following format
                             mainconfig   :   /home/leon/
                             # Default paths
                             minuterefereepath  :  /home/leon/refereelist_minute.cfg
                             secondrefereepath  :  /home/leon/refereelist_minute.cfg
                             minutefallback  :

    APPLICATION

| class            |       method     | since vers |  validation   |  comment    | manual  |  *used by |
| ---------------- |  --------------  | ---------- | ------------- | ----------  | ------- | --------- |
|  **core**        |                  |            |               |             |         |           |
|  minute_definitive |  __init__      |      2.0.0 |  yes          |             |         |           |
|  minute_definitive |  DOS_check1min |      2.0.0 |  yes          |             |         |           |
|  minute_definitive |  MagPy_check1min |    2.0.0 |  yes          |             |         |           |
|  minute_definitive |  minute_mail_text |   2.0.0 |  yes          |             |         |           |

    """

    def __init__(self, input=None, config=None):
        self.config = config if config else {}
        self.input = input if input else {}
        if not config:
            # use testing environment
            self.config = {'configpath': '/tmp/imbottest/conf',
                           'mailinglist': '/tmp/imbottest/conf/mailinglist.cfg',
                           'minuterefereepath': '/tmp/imbottest/conf/refereelist_minute.cfg',
                           'secondrefereepath': '/tmp/imbottest/conf/refereelist_second.cfg',
                           'minutefallback': {'Maxi Musti': 'maxi@example.com'},
                           'sysadmin': {'Roman Leonhardt': 'ro.test'},
                           'memory_mail': '/tmp/imbottest/memory/memory_email.json',
                           'memory_directory_analysis': '/tmp/imbottest/memory/memory_directory_analysis.json',
                           'second_local_step2': '/tmp/imbottest/second/step2/',
                           'winepath': '/home/leon/.wine/drive_c',
                           'minute_step1': '/home/leon/Tmp/GIN/step1minute',
                           'minute_step2': '/home/leon/Tmp/GIN/step2minute',
                           'minute_step3': '/home/leon/Tmp/GIN/step3minute'
                           }
        self.report = []
        self.logdict = {}
        self.yearprefix = "Mag"

        if not self.input:
            self.report.append("second_analysis: no data provided - aborting")
            return

    def DOS_check1min(self, debug=False):
        """
        DESCRIPTION
            run check1min on magnetic data
        PRERESQUISITE
            wine

        """
        obscode = self.input.get('obscode')
        year = self.input.get('year')
        reportpath = ''
        sleeptime = 10
        sourcepath = self.input.get('step1path') #self.input.get('temporaryfolder')
        # sourcepath = self.config.get('minute_step1')
        winepath = self.config.get('winepath')  # winepath='/root/.wine'

        if debug:
            print("winepath:", winepath)

        # create a symbolic link of data to be analyzed within the wine data directory
        # This creates a symbolic link on python in tmp directory
        if not os.path.exists(os.path.join(winepath, 'data')):
            os.makedirs(os.path.join(winepath, 'data'))
        dst = os.path.join(winepath, 'data', obscode)
        # This creates a symbolic link on python in tmp directory
        if os.path.isdir(dst):
            os.unlink(dst)
        # src = os.path.join(sourcepath, "{}{}".format(self.yearprefix, year), obscode.upper())
        src = sourcepath
        os.symlink(src, dst)
        if debug:
            print("Linking {} to {}".format(src, dst))
            print(" ... now analyzing data for year {}".format(year))

        curwd = os.getcwd()
        os.chdir(winepath)

        cmd = '/usr/bin/wine start check1min.exe C:\\\\data\\\\{} {} {} C:\\\\data\\\\{}\\\\{}report{}.txt'.format(
            obscode, obscode, year, obscode, obscode.lower(), year)
        print(" Calling {}".format(cmd))

        subprocess.call(cmd, shell=True)

        os.chdir(curwd)
        time.sleep(sleeptime)  # wait a while to finish analysis
        dirs = os.listdir(dst)
        if debug:
            print(" DIRS:", dirs)
        os.unlink(dst)

        reportpath = os.path.join(src, "{}report{}.txt".format(obscode.lower(), year))
        self.report.append('check1min (dos) performed')

        return reportpath

    def MagPy_check1min(self, debug=False):
        """
        DESCRIPTION:
            reading data and checking contents
        """
        obscode = self.input.get('obscode')
        year = self.input.get('year')
        sourcepath = self.input.get('step1path') #self.input.get('temporaryfolder')
        winepath = self.config.get('winepath')  # winepath='/root/.wine'

        issuelist = []
        logdict = {}
        logdict['Level'] = 2

        checkingdict = {'blvcheck': {'perfom': True}}

        print(" Running basic MagPy read and folder content test for {}, {}...".format(obscode, year))

        def most_frequent(List):
            return max(set(List), key=List.count)

        minpath = sourcepath

        extension = 'BIN'
        # ======== Checking presence readme.imo yearmean.imo imoyyyy.blv =======
        try:
            bincnt = len(glob.glob(os.path.join(minpath, "*.bin")))
            if bincnt == 12:
                extension = 'bin'
            bincnt += len(glob.glob(os.path.join(minpath, "*.BIN")))
            blvcnt = len(glob.glob(os.path.join(minpath, "*.blv")))
            blvcnt += len(glob.glob(os.path.join(minpath, "*.BLV")))
            addcnt = len(glob.glob(os.path.join(minpath, "*.{}".format(obscode.lower()))))
            addcnt += len(glob.glob(os.path.join(minpath, "*.{}".format(obscode.upper()))))
            # check yearmean and readme
            print("  -> result: {} binary files, {} BLV files, {} *.{} files".format(bincnt, blvcnt, addcnt,
                                                                                     obscode.lower()))
            if bincnt == 12:
                if debug:
                    print("   Requested binary files are present")
            elif bincnt > 12:
                print("   More than requested binary files are present")
                issuelist.append("please check the amount of binary files - only one year")
            else:
                issuelist.append("check binary files")
                print("   ISSUE: check presence of all requested binary files")
                logdict['Level'] = 0
            if blvcnt >= 1:
                if debug:
                    print("   Requested BLV files are present")
            else:
                issuelist.append("check presence of baseline data")
                print("   ISSUE: check baseline data")
                logdict['Level'] = 0
            if addcnt >= 2:
                if debug:
                    print("   Yearmean and readme seem to be present")
            else:
                issuelist.append("check yearmean/readme")
                print("   ISSUE: check presence of yearmean /readme")
                logdict['Level'] = 0
        except:
            issue = "problem when accessing data files"
            issuelist.append(issue)
            print("   ISSUE: {}".format(issue))
            logdict['Level'] = 0

        # ==============  Readability of files
        try:
            data = read(os.path.join(minpath, "*.{}".format(extension)))
            logdict['AmountMin'] = len(data)
        except:
            issuelist.append("binary data read problem")
            logdict['Level'] = 0
            logdict['Issues'] = issuelist
            return logdict.get('Level')

        print("  -> read test successfully passed: found {} data points".format(len(data)))

        # ============== Checking W01..W16 headers in IAF files ================
        """
        W01 Station code              " CLF"  (20 43 4C 46)
        W02 Year and day number      2020001  (A1 D2 1E 00)
        W03 Co-latitude (deg x 1000)   41975  (F7 A3 00 00)
        W04 Longitude (deg x 1000)      2260  (D4 08 00 00)
        W05 Elevation (metres)           145  (91 00 00 00)
        W06 Reported elements         "XYZG"  (58 59 5A 47)
        W07 Institute code            "IPGP"  (49 50 47 50)
        W08 D-conversion factor        10000  (10 27 00 00)
        W09 Data quality code         "IMAG"  (49 4D 41 47)
        W10 Instrument code           "  RC"  (20 20 52 43)
        W11 Limit for K9                 450  (C2 01 00 00)
        W12 Sample period (ms)           200  (C8 00 00 00)
        W13 Sensor orientation        "HDZF"  (48 44 5A 46)
        W14 Publication date          "2102"  (32 31 30 32) Date of acceptation as Definitive - will be set by INTERMAGNET
        W15 Format version           ver 2.1  (03 00 00 00)
        W16 Reserved word                  0  (00 00 00 00)
        """
        if debug:
            print(data.header)
            print(data.header.get('StationIAGAcode'))
            print(data.header.get('DataAcquisitionLatitude'))
            print(data.header.get('DataAcquisitionLongitude'))
            print(data.header.get('DataElevation'))
            print(data.header.get('DataComponents'))
            print(data.header.get('StationInstitution'))
            print(data.header.get('StationK9'))
            print(data.header.get('DataPublicationDate'))
            print(data.header.get('DataSensorOrientation'))
            print(data.header.get('DataFormat'))

        logdict['Issues'] = issuelist
        checklist = logdict.get('CheckList', [])
        checklist.append('basic MagPy test performed')
        logdict['CheckList'] = checklist
        self.logdict = logdict
        if debug:
            print(logdict)

        return logdict.get('Level')

    def minute_mail_text(self, level, imodict, reportpath=None, debug=False):
        """
        DESCRIPTION
            creates mail contents for one-mninute reports
        VARIBALES
            level   : int : the obtained readiness level of final analysis
            dataset : dict : the current dictionary of the modificationlist
            imo_dict : dict : the imo dictionary as obtained by imostatus.get_imo
        RETURN
            a dictionary with subject, text, from, to, attachments
        """
        maildict = {}
        attachfilelist = []
        obscode = self.input.get('obscode')
        resolution = self.input.get('resolution')
        year = int(self.input.get('year'))
        mod = self.input.get('modification')
        step2path = self.input.get('step2path', '')
        step2str = ''

        admin = self.config.get('sysadmin')
        referee = imodict.get('referee')
        modfiles = imodict.get('modfiles')
        contacts = imodict.get('contacts', [])
        imbotmanagers = imodict.get('manager', [])
        receivers = contacts
        nameofdatachecker = [n for n in referee][0]
        adminmail = [admin.get(n) for n in admin][0]
        if reportpath:
            attachfilelist.append(reportpath)
        receivers.append(referee.get(nameofdatachecker))
        if debug:
            print("ADMIN:", admin)

        modtext = ''
        if modfiles:
            for k1, v1 in modfiles.items():
                if k1 == "value_diffs":
                    k1 = "file(s) modified"
                modtext += f"   {k1} : "
                modtext += ", ".join([f"{k2}" for k2, v2 in v1.items()])
                modtext += "\n"
        if debug:
            print("Modified files:", modtext)

        maildict['subject'] = 'IMBOT data check of {} one-{} submission from {}, {}'.format(mod, resolution, obscode,
                                                                                            year)
        maildict['from'] = [adminmail]

        if step2path:
            step2str = '\n\nPlease note that data for {} had been accepted earlier and is already contained in STEP 2.\n'.format(
                obscode)

        if debug:
            print("Current modification", mod)
        maintext = "Dear data submitter,\n\nyou receive the following information as your e-mail address is connected to submissions of geomagnetic data products from {} observatory.\nYour one-minute data submission for {} has been".format(
            obscode, year)
        if mod == 'new':
            maintext += " automatically evaluated by IMBOT, an automatic data checker of INTERMAGNET.\n\nThe evaluation process resulted in\n\n"
        else:
            maintext += " updated within the step1 directory.\n The following files have been modified or newly uploaded:\n{}\n\nSuch updates automatically trigger a new evaluation by IMBOT, an automatic data checker of INTERMAGNET.\n\nThe evaluation process resulted in\n\n".format(
                modtext)

        if int(level) == 0:
            maintext += "    ISSUES to be resolved\n\n"
        else:
            maintext += "    READY for manual data checking\n\n"

        if step2str:
            maintext += step2str

        # level 1 and 2 are identical for minute
        level0 = "Your data did not pass the automatic evaluation test. Please update your data submission.\nDetails can be found in the attached report. Please update your submission accordingly and perform a data check with checking tools provided by INTERMAGNET (see links below) before re-submission of your data set. If you need help please contact {}\n\n".format(
            nameofdatachecker)
        level1 = "Congratulations! An automatic data check was successfully passed. Your submission is ready for evaluation by INTERMAGNET data checkers. Please check the attached check1min report for details.\n\nYour data set has been assigned to an INTERMAGNET data checker for evaluation.\nYour data checker is {}.\nPlease note that INTERMAGNET data checkers perform all checks on voluntary basis beside their usual duties. So please be patient. The data checker will contact you if questions arise.\n\n".format(
            nameofdatachecker)
        level2 = "Congratulations! An automatic data check was successfully passed. Your submission is ready for evaluation by INTERMAGNET data checkers. Please check the attached check1min report for details.\n\nYour data set has been assigned to an INTERMAGNET data checker for evaluation.\nYour data checker is {}.\nPlease note that INTERMAGNET data checkers perform all checks on voluntary basis beside their usual duties. So please be patient. The data checker will contact you if questions arise.\n\n".format(
            nameofdatachecker)

        if int(level) == 0:
            maintext += level0
        elif int(level) == 1:
            maintext += level1
        elif int(level) == 2:
            maintext += level2

        maintext += "If you have any questions regarding the evaluation process please check out/request the general instructions (https://github.com/INTERMAGNET/IMBOT/blob/master/README.md - currently available online only for the IM definitive data committee) or contact the IMBOT manager.\n\n"
        maintext += "\nSincerely,\n       IMBOT\n\n"

        if int(level) < 2:
            instructionstext = """
            -----------------------------------------------------------------------------------
            Important Links:

            check1min (http://magneto.igf.edu.pl/soft/check1min/)

            MagPy (https://github.com/geomagpy/magpy)
                               """
            maintext += instructionstext

        receivers.extend(imbotmanagers)
        receivers = list(dict.fromkeys(receivers))

        maildict['to'] = receivers
        maildict['text'] = maintext
        maildict['attachment'] = attachfilelist

        return maildict


class TestImbotMinute(unittest.TestCase):

    def test_runtime(self):
        # also tests idf and hdz tools
        config = {}
        debug = False

        referenced1 = {'kou21may.bin': '20231205', 'KOU2021_report.txt': '20231205', 'kou21apr.bin': '20231205',
                       'kou21feb.bin': '20231205', 'kou21jun.bin': '20231205', 'readme.kou': '20231205',
                       'kou21oct.bin': '20231205', 'kou21sep.bin': '20231205', 'kou2021.blv': '20231205',
                       'kou21mar.bin': '20231205', 'kou21nov.bin': '20231205', 'kou21dec.bin': '20231205',
                       'kou21jul.bin': '20231205', 'kou21jan.bin': '20231205', 'kou21aug.bin': '20231205',
                       'yearmean.kou': '20231205'}
        # Create test environment in temporary directory
        basepath = "/home/leon/Software/IMBOT/"  # replace with __file__
        os.makedirs(os.path.dirname("/tmp/imbottest"), exist_ok=True)
        os.makedirs(os.path.dirname("/tmp/imbottest/step1"), exist_ok=True)
        os.makedirs(os.path.dirname("/tmp/imbottest/step2"), exist_ok=True)
        os.makedirs(os.path.dirname("/tmp/imbottest/step3"), exist_ok=True)
        if os.path.exists("/tmp/imbottest/step1"):
            shutil.rmtree("/tmp/imbottest/step1")
        if os.path.exists("/tmp/imbottest/step2"):
            shutil.rmtree("/tmp/imbottest/step2")
        if os.path.exists("/tmp/imbottest/step3"):
            shutil.rmtree("/tmp/imbottest/step3")
        shutil.copytree(os.path.join(basepath, 'test', 'step1'), "/tmp/imbottest/step1")
        shutil.copytree(os.path.join(basepath, 'test', 'step1'), "/tmp/imbottest/step2")
        os.makedirs(os.path.dirname("/tmp/imbottest/conf"), exist_ok=True)
        if os.path.exists("/tmp/imbottest/conf"):
            shutil.rmtree("/tmp/imbottest/conf")
        shutil.copytree(os.path.join(basepath, 'config'), "/tmp/imbottest/conf")
        if os.path.exists("/tmp/imbottest/memory"):
            shutil.rmtree("/tmp/imbottest/memory")

        imostatus = steps.botstatus(config=config)  # allow for testrun which does not update operative imostatus

        sourcepath = "/tmp/imbottest/step1"
        step2path = "/tmp/imbottest/step2"
        step3path = "/tmp/imbottest/step3"
        # Create am initial result memory including only paths
        imostatus = imostatus.analyse_source(sourcepath, step=1, type='minute', debug=False)
        imostatus = imostatus.analyse_source(step2path, step=2, type='minute', debug=False)
        imostatus = imostatus.analyse_source(step3path, step=3, type='minute', debug=False)

        # Analyze step1 directory and update contents with current directory and reviewing iunformation
        yearlist = [el for el in imostatus.result]
        for year in yearlist:
            for restype in ['minute']:
                obsdata = imostatus.result.get(year).get(restype)
                obslist = [el for el in obsdata]
                for obs in obslist:
                    imolayer = obsdata.get(obs)
                    imostatus.report.append("Analyzing {} {} data from {}".format(obs, restype, year))
                    imolayer = imostatus._get_step1_information(imolayer, obscode=obs, debug=False)
                    imostatus = imostatus.set_contacts(year=year, resolution=restype, obscode=obs)

        methods.write_memory(imostatus.result, path="/tmp/imbot_memory.json", debug=False)

        # the read the memory again
        imostatus.result = methods.read_memory("/tmp/imbot_memory.json", debug=debug)
        # print (imostatus.result)

        modres = imostatus.get_modified(year=2021, resolution='minute')
        #print("PHASE2", modres)
        cmod = modres[0].get('modification')
        self.assertEqual(cmod, "updated but already accepted")

        imostatus = imostatus.set_modification(set='new', year=2021, resolution='minute', obscode='KOU')
        modres = imostatus.get_modified(year=2021, resolution='minute')

        dataset = modres[0]
        minana = minute_definitive(input=dataset)
        reportpath = minana.DOS_check1min(debug=debug)
        pathtest = os.path.isfile(reportpath)
        self.assertTrue(pathtest)
        level = minana.MagPy_check1min(debug=debug)
        self.assertEqual(minana.logdict.get('AmountMin'), 525600)
        imodict = imostatus.get_imo(obscode=minana.input.get('obscode'), year=minana.input.get('year'),
                                    resolution='minute')
        maildict = minana.minute_mail_text(level, imodict, reportpath=reportpath, debug=debug)
        if debug:
            print("maildict", maildict)
        tt = maildict.get('text')
        tt1, tt2 = False, False
        if tt.find("data checker is Maxi Musti") >= 0:
            tt1 = True
        pt = maildict.get('attachment')
        if isinstance(pt, (list, tuple)) and len(pt) > 0:
            tt2 = True
        self.assertTrue(tt1)
        self.assertTrue(tt2)

        # now add meta_IMO.txt, remove blv file and modify README
        shutil.copy(os.path.join(basepath, 'examples', 'meta_OBSCODE.txt'),
                    "/tmp/imbottest/step1/Mag2021/KOU/meta_KOU.txt")
        from pathlib import Path
        for p in Path("/tmp/imbottest/step1/Mag2021/KOU").glob("*.blv"):
            p.unlink()
        for p in Path("/tmp/imbottest/step1/Mag2021/KOU").glob("*.BLV"):
            p.unlink()
        with open('/tmp/imbottest/step1/Mag2021/KOU/readme.kou', 'a') as file:
            file.write('Added a note')
        # Testing step1 again
        imostatus = imostatus.analyse_source(sourcepath, step=1, type='minute', debug=False)

        yearlist = [el for el in imostatus.result]
        for year in yearlist:
            for restype in ['minute']:
                obsdata = imostatus.result.get(year).get(restype)
                obslist = [el for el in obsdata]
                for obs in obslist:
                    imolayer = obsdata.get(obs)
                    imolayer = imostatus._get_step_information(imolayer, step=3, obscode=obs, debug=False)
                    imolayer = imostatus._get_step_information(imolayer, step=2, obscode=obs, debug=False)
                    imolayer = imostatus._get_step1_information(imolayer, obscode=obs, debug=False)
                    imostatus = imostatus.set_contacts(year=year, resolution=restype, obscode=obs)

        modres = imostatus.get_modified(year=2021, resolution='minute')
        imostatus = imostatus.set_modification(set='updated', year=2021, resolution='minute', obscode='KOU')
        modres = imostatus.get_modified(year=2021, resolution='minute')

        dataset = modres[0]
        minana = minute_definitive(input=dataset)
        reportpath = minana.DOS_check1min(debug=debug)
        pathtest = os.path.isfile(reportpath)
        self.assertTrue(pathtest)
        level = minana.MagPy_check1min(debug=debug)
        # self.assertEqual(minana.logdict,get('AmountMin'), 525600)
        imodict = imostatus.get_imo(obscode=minana.input.get('obscode'), year=minana.input.get('year'),
                                    resolution='minute')
        maildict = minana.minute_mail_text(level, imodict, reportpath=reportpath, debug=True)
        if debug:
            print("PHASE2", maildict)
        tt = maildict.get('text')
        if tt.find("added") >= 0:
            tt1 = True
        self.assertTrue(tt1)

        # Testing again - now setting modification to ''
        imostatus = imostatus.analyse_source(sourcepath, step=1, type='minute', debug=False)

        yearlist = [el for el in imostatus.result]
        for year in yearlist:
            for restype in ['minute']:
                obsdata = imostatus.result.get(year).get(restype)
                obslist = [el for el in obsdata]
                for obs in obslist:
                    imolayer = obsdata.get(obs)
                    imolayer = imostatus._get_step_information(imolayer, step=3, obscode=obs, debug=False)
                    imolayer = imostatus._get_step_information(imolayer, step=2, obscode=obs, debug=False)
                    imolayer = imostatus._get_step1_information(imolayer, obscode=obs, debug=False)
                    imostatus = imostatus.set_contacts(year=year, resolution=restype, obscode=obs)

        modres = imostatus.get_modified(year=2021, resolution='minute')
        imostatus = imostatus.set_modification(set='', year=2021, resolution='minute', obscode='KOU')
        modres = imostatus.get_modified(year=2021, resolution='minute')
        # should be empty
        self.assertFalse(modres)

if __name__ == "__main__":
    unittest.main(verbosity=2)