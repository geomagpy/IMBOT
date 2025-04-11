# -*- coding: utf-8 -*-
import sys
sys.path.insert(1,'/home/leon/Software/IMBOT/') # should be magpy2

from imbot.core import methods
import os
import numpy as np
import pathlib
import re
import hashlib
from magpy.core.methods import testtime
from datetime import datetime, timedelta, timezone
import unittest
import shutil
import collections


class botstatus(object):
    """
    DESCRIPTION
        Preparation class to obtain a full dictionary with all analysis states of INTERMAGNET submissions.
        By initializing with configuration data, all suppied sources are tested and evetually added to a summary json
        If directory is not existing but report contains data then send message to imbot admin

    VARIABLES
        report  : list  : contains report messages acquired during runtime - to be used for logging
        result  : dict  : contains a result dictionary of the following format. the result dictionary can be updated
                          or contents extracted with a number of methods provided by this class
        config  : dict  : contains basic parameters and path definitions for the specfic application. Conif data should be read
                          from a dedicated configuration file of the following format
                             mainconfig   :   /home/leon/
                             # Default paths
                             minuterefereepath  :  /home/leon/refereelist_minute.cfg
                             secondrefereepath  :  /home/leon/refereelist_minute.cfg
                             minutefallback  :

    APPLICATION

    TODO:
        - Method to get summaries for year, steps, resolutions
                 - get dates when obs reached step3 in 2022
                 - eventually get bar charts for step1, step2, step3 for year range
        - Scan report for warnings and errors
        - Analyze only selected observatories - not here

| class            |       method     | since vers |  validation   |  comment    | manual  |  *used by |
| ---------------- |  --------------  | ---------- | ------------- | ----------  | ------- | --------- |
|  **core**        |                  |            |               |             |         |           |
|  imbot_steps     |  __init__        |      2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  _find_exclude   |      2.0.0 |      yes      |             |         | _get_step1_information |
|  imbot_steps     |  _get_step1_information | 2.0.0 |    yes      |             |         |           |
|  imbot_steps     |  _get_step_information | 2.0.0 |     yes      |             |         |           |
|  imbot_steps     |  add_contents    |      2.0.0 |               |             |         |           |
|  imbot_steps     |  add_minute_state |     2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  analyse_source  |      2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  get_manager_mails |    2.0.0 |      yes      |             |         | set_contacts |
|  imbot_steps     |  get_contact_mails |    2.0.0 |      yes      |             |         | set_contacts |
|  imbot_steps     |  get_data_checker |     2.0.0 |      yes      |             |         | set_contacts |
|  imbot_steps     |  get_imo         |      2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  get_modified    |      2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  set_contacts    |      2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  set_modification |     2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  update_level    |      2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  update_validity |      2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  yearly_stats    |      2.0.0 |      yes      |             |         |           |

    """

    def __init__(self, result=None, config=None):
        self.config = config if config else {}
        self.result = result if result else {}
        if not config:
            # use testing environment
            self.config = {'configpath': '/tmp/imbottest/conf',
                           'mailinglist': '/tmp/imbottest/conf/mailinglist.cfg',
                           'minuterefereepath': '/tmp/imbottest/conf/refereelist_minute.cfg',
                           'secondrefereepath': '/tmp/imbottest/conf/refereelist_second.cfg',
                           'minutefallback': {'Maxi Musti': 'maxi@example.com'},
                           'sysadmin': {'Roman Leonhardt': 'imbot@conrad-observatory.at'},
                           'telegramconfig': '/tmp/imbottest/conf/imbot_telegram.cfg',
                           'emailcredentials': 'immail',
                           'memory_mail': '/tmp/imbottest/memory/memory_email.json',
                           'memory_directory_analysis': '/tmp/imbottest/memory/memory_directory_analysis.json',
                           'winepath': '/home/leon/.wine/drive_c',
                           'second_local_step2': '/tmp/imbottest/second/step2/',
                           'minute_step1': '/home/leon/Tmp/GIN/step1minute',
                           'minute_step2': '/srv/imbot/minute/step2',
                           'minute_step3': '/srv/imbot/minute/step3',
                           'second_step1': '/home/leon/Tmp/GIN/step1second',
                           'second_step2': '/srv/imbot/second/step2'
                           }
        if not self.result:
            self.result = methods.read_memory(self.config.get('memory_directory_analysis'))
        self.report = []

    def _find_exclude(self, filename, excludelist=None):
        if not excludelist:
            excludelist = ['.listing', 'cln.zip']
        for ex in excludelist:
            if filename.find(ex) > -1:
                return True
        return False

    def _get_step1_information(self, imolayer, obscode='XXX', checkrange=0, debug=False):
        """
        DESCRIPTION:
            Method will check directory structure
            It will extract directory, amount of files, filetype, and last modification date
        RETURN:
            result dictionary extended for directory content information if step1
            or review state if step2
        APPLICTAION:
            for obs in obslist:
                imolayer = obsdata.get(obs)
                imolayer = imostatus._get_step1_information(imolayer, obscode=obs, debug=False)
        """
        acceptabletypes = ['.zip', '.gz', '.tgz', '.tar.gz', '.tar', '.cdf', '.sec', '.min', '.bin',
                           '.{}'.format(obscode.lower()), '.blv', '.BIN', '.BLV', '.{}'.format(obscode.upper())]
        sourcepath = imolayer.get('step1')
        if debug:
            print(" Running directory information analysis")
            print("  for sourcepath: {}".format(sourcepath))
        if not sourcepath or not os.path.exists(sourcepath):
            self.report.append(" _get_step1_information: could not access sourcepath {}".format(sourcepath))
            return imolayer
            # This function is incredibly slow - check - leon 2023-12-11
        for root, dirs, files in os.walk(sourcepath):
            level = root.replace(sourcepath, '').count(os.sep)
            if debug:
                print("LEVEL", level)
            t1 = datetime.now(timezone.utc)
            if debug:
                print("checking source and root", sourcepath, root)
            if level == 0:
                if debug:
                    print(" Found level 0 directory: {}".format(root))
                # append root, and ctime of youngest file in directory
                timelist = []
                extlist = []
                if not obscode:
                    obscode = sourcepath[-3:].upper()
                filedict = {}
                # drop exclude-files from the filelist
                files = [f for f in files if not self._find_exclude(f)]
                for f in files:
                    try:
                        stat = os.stat(os.path.join(root, f))
                        mtime = stat.st_mtime
                        ctime = stat.st_ctime
                        ext = os.path.splitext(f)[1]
                        timelist.append(mtime)
                        extlist.append(ext)
                        filedict[f] = datetime.fromtimestamp(mtime, timezone.utc).strftime("%Y%m%d")
                    except:
                        self.report.append(" step1_directory: Failed to extract creation times for {}".format(imolayer))
                arch = False
                if len(extlist) > 0:
                    for extl in extlist:
                        exttest = extl.lower()
                        # print ("Extension test", exttest)
                        if exttest.endswith('tar') or exttest.endswith('gz') or exttest.endswith(
                                'zip') or exttest.endswith('bz2'):
                            arch = True
                if len(timelist) > 1 or arch:  # requires more than one file (nrcan step3 contains eventualy single definitive files) --- Problem with single files on second
                    youngest = max(timelist)
                    if debug:
                        # print ("  -> youngest file: {}".format(youngest))
                        print("  -> last modified : {} ; checking data older than {}".format(
                            datetime.fromtimestamp(youngest, timezone.utc), datetime.now(timezone.utc) - timedelta(hours=checkrange)))
                    # only if latest file is at least "checkrange" hours old
                    if datetime.fromtimestamp(youngest, timezone.utc) < datetime.now(timezone.utc) - timedelta(hours=checkrange):
                        # check file extensions ... and amount of files (zipped, cdf, sec)
                        # firstly remove txt, par and md from list (meta.txt contain updated parameters)
                        if debug:
                            print("  -> extensions: {}".format(extlist))
                        extlist = [el for el in extlist if not el in ['.txt', '.md']]
                        amount = len(files)
                        if len(extlist) > 0:
                            typ = max(extlist, key=extlist.count)
                            if typ in acceptabletypes:
                                imolayer['filetype'] = typ
                                imolayer['lastmodified'] = datetime.fromtimestamp(np.round(youngest, 0), timezone.utc).strftime(
                                    "%Y-%m-%dT%H:%M:%S")
                                if not imolayer.get('maximum_minute_step', ''):
                                    imolayer['maximum_minute_step'] = 'step1'
                                elif not imolayer.get('maximum_minute_step').endswith('1'):
                                    report = " step1_directory: analyzing step1 data although higher step data for {} is already existing".format(
                                        obscode)
                                statestring = "{}".format(filedict)
                                m = hashlib.md5()
                                m.update(statestring.encode())
                                statusid = str(int(m.hexdigest(), 16))[0:24]
                                oldstatusid = imolayer.get('statusid')
                                oldfiledict = imolayer.get('files')
                                imolayer['files'] = filedict
                                imolayer['exclude'] = False
                                imolayer['statusid'] = statusid
                                if debug:
                                    print("File dictionary", filedict)
                                if not oldstatusid == statusid:
                                    if debug:
                                        print(" Found changes for {}".format(obscode))
                                    if not oldstatusid:
                                        self.report.append(" Got new data for {}".format(obscode))
                                        imolayer['modification'] = 'new'
                                    else:
                                        # fill moddict with changes and add report textNEW data set
                                        self.report.append("Updated/modified data set for {}".format(obscode))
                                        imolayer['modification'] = 'updated'
                                        if debug:
                                            print("Comparison", oldfiledict, filedict)
                                        imolayer['modfiles'] = methods.dictdiff(oldfiledict, filedict)
                                    if imolayer.get('step3') or imolayer.get('review'):
                                        self.report.append(
                                                " step1 data was changed although step3 is already existing or review finished")
                                        imolayer['modification'] = 'updated but already accepted'
                            else:
                                self.report.append(" step1_directory: Found unexpected data type '{}'".format(typ))
                        else:
                            self.report.append(" step1_directory: Directory existing - but no files found")
                    else:
                        self.report.append(" step1_directory: Uploaded recently - eventually not finished")
            elif level > 1:
                self.report.append(" step1_directory: Found subdirectories - ignoring this folder")
            t2 = datetime.now(timezone.utc)
            if debug:
                print("Needed ", (t2 - t1).total_seconds())

        return imolayer

    def _get_step_information(self, imolayer, step=2, obscode='XXX', reviewidentifier="accepted", debug=False):
        """
        DESCRIPTION:
            Method will update step2 and step3 information and test for review reports in step2
            Eventually trigger a random test for identically of step1 and step2 data content
            (if "added to step2" is found in 'modification')
        RETURN:
            update report and results
        APPLICTAION:
            for obs in obslist:
                imolayer = obsdata.get(obs)
                imolayer = imostatus._get_step_information(imolayer, step=2, obscode=obs, debug=False)
        """
        sourcepath = imolayer.get('step{}'.format(step))
        if debug:
            print(" Running directory information analysis - step{}".format(step))
            print("  for sourcepath: {}".format(sourcepath))
        if not sourcepath or not os.path.exists(sourcepath):
            self.report.append(" _get_step{}_information: could not access sourcepath {}".format(step, sourcepath))
            return imolayer
        # This function is incredibly slow - check - leon 2023-12-11
        for root, dirs, files in os.walk(sourcepath):
            level = root.replace(sourcepath, '').count(os.sep)
            t1 = datetime.now(timezone.utc)
            if level == 0:  # ignore any subdirectories
                if debug:
                    print(" Found level 0 directory: {}".format(root))
                if debug:
                    print("checking source and root", sourcepath, root)
                #print([f for f in files])
                # identify any eventually existing review file
                obscode = root.replace(sourcepath, '')[1:4]
                obscode = obscode.upper()
                filedict = {}
                files = [f for f in files if not self._find_exclude(f)]
                extlist = [os.path.splitext(fi)[1] for fi in files]
                typ = max(extlist, key=extlist.count)
                contentname = "step{}date".format(step)
                if not imolayer.get(contentname, ''):
                    imolayer[contentname] = datetime.now().strftime("%Y-%m-%d")
                    cms = imolayer.get('maximum_minute_step','step0')[-1]
                    if not int(cms) > int(step):
                        # check whether a higher step is already existing
                        # important as step3 is analyzed before step2
                        imolayer['maximum_minute_step'] = "step{}".format(step)
                        # IMPORTANT: get the filetyp of the highest available step so that correct mindata is loaded
                        # Min data in step3 is usually zipped (unlike step1 or step2)
                        imolayer['maximum_step_filetype'] = typ
                        imolayer['modification'] = "added to step{}".format(step)
                if debug:
                    print("Found files in step{}:{}".format(step, files))
                if step == 2:
                    if not imolayer.get('review', False):
                        for f in files:
                            if f.find(reviewidentifier) >= 0:
                                imolayer['review'] = True
                                revname = "reviewdate"
                                if not imolayer.get(revname, ''):
                                    imolayer[revname] = datetime.now().strftime("%Y-%m-%d")
                                    imolayer['modification'] = "step{} reviewed".format(step)
            elif level > 1:
                self.report.append(" step{}_directory: Found subdirectories - ignoring this folder".format(step))
            t2 = datetime.now(timezone.utc)
            if debug:
                print("Needed ", (t2 - t1).total_seconds())

        return imolayer

    def add_content(self, year=None, resolution=None, obscode=None, name='maildict', content=None):
        """
        DESCRIPTION:
            Add contents to imostatus
        APPLICTAION:
            add the maildictionary to imostatus (in case mails need to be resend at a later stage)
        """
        year = str(year)
        if year and resolution and obscode:
            yeard = self.result.get(year)
            if yeard:
                rsd = yeard.get(resolution)
                if rsd:
                    imo = rsd.get(obscode)
                    imo[name] = content
        return self

    def add_minute_state(self, modlist, debug=False):
        """
        DESCRIPTION:
            Get current state of one-minute analysis and add this info plus path to one second items
        RETURNS:
            modification list with minutepath and step added
        """

        for obsdict in modlist:
            year = obsdict.get('year')
            obscode = obsdict.get('obscode')
            resolution = obsdict.get('resolution')
            if resolution == 'second':
                minres = self.get_imo(year=year, resolution='minute', obscode=obscode)
                if debug:
                    print("Found corresponding minute data", minres)
                if minres:
                    maxstep = minres.get('maximum_minute_step', '')
                    extension = minres.get('maximum_step_filetype','')
                    if not extension:
                        extension = minres.get('filetype','')
                    obsdict['minutestep'] = maxstep
                    obsdict['minutepath'] = os.path.join(minres.get(maxstep, ''), "*{}".format(extension))
                else:
                    print ("Getting maximum minstep: did not find minuta data for {}, {}".format(obscode, year))
                    obsdict['minutestep'] = ''
                    obsdict['minutepath'] = ''

        return modlist


    def analyse_source(self, sourcepath, step=1, type='second', year=None, debug=False):
        """
        DESCRIPTION:
            Extract year and obscode plus main path
        RETURN:
            list with all sourcepaths connected to a IMO
        APPLICTAION:

        TEST:
        """
        if not year:
            year = []
        result = self.result
        obslist = []
        resolutionlayer = {}
        yearlayer = {}
        useyear = None

        if debug:
            print(" Running directory information analysis")
        if not sourcepath or not os.path.exists(sourcepath):
            self.report.append(" analysis_source: could not access sourcepath {}".format(sourcepath))
            return self
        t1 = datetime.now(timezone.utc)
        for root, dirs, files in os.walk(sourcepath):
            if debug:
                print("Current layer", root, dirs, files)
            path = pathlib.Path(root)
            lastpart = path.parts[-1]
            # get lengths of dirnames in folder
            dl = [len(el) for el in dirs]
            if len(dl) > 0:
                dominant_length = max(set(dl), key=dl.count)
                if dominant_length == 3:
                    if debug:
                        print("Found IMO level")
                    # get year from root
                    fyear = re.findall(r'\d+', lastpart)
                    if debug:
                        print("Extracted the following year from path:", fyear)
                    if len(year) > 0 and len(fyear) > 0:
                        if fyear[0] in year:
                            useyear = fyear[0]
                    elif not len(year) > 0 and len(fyear) > 0:
                        useyear = fyear[0]
                    elif not len(fyear) > 0:
                        print("No year found - doing nothing")
                    obslist = [el for el in dirs if len(el) == 3]
            if useyear and len(obslist) > 0 and lastpart in obslist:
                imolayer = {}
                resolutionlayer = {}
                yearlayer = {}
                useyear = str(useyear)
                if result.get(useyear):
                    yearlayer = result.get(useyear)
                    if yearlayer.get(type):
                        resolutionlayer = yearlayer.get(type)
                        if resolutionlayer.get(lastpart.upper()):
                            imolayer = resolutionlayer.get(lastpart.upper())
                if debug:
                    print("Found content level")
                imolayer['step{}'.format(step)] = root
                resolutionlayer[lastpart.upper()] = imolayer
                yearlayer[type] = resolutionlayer
                result[useyear] = yearlayer
        t2 = datetime.now(timezone.utc)
        if debug:
            print("Needed ", (t2 - t1).total_seconds())
        self.result = result
        return self


    def get_manager_mails(self, debug=False):
        """
        DESCRIPTION
            Obtain manager e-mails.
        PARAMETER:
            results : which contains file path of README.IMO
            config : which contains links to local mail dictionary (obtained from README) and localmaillist
        CALLED BY:
            set_contacts
        RETURNS:
            list with e-mails
        """

        config = self.config
        managers = []
        if os.path.isfile(config.get('mailinglist')):
            obsdict = methods.get_conf(config.get('mailinglist'))
            managers = obsdict.get('managers', [])
        return managers


    def get_contact_mails(self, obscode='xxx', year=str(1777), debug=False):
        """
        DESCRIPTION
            Obtain a dictionary with contact e-mails.
            Admin contacts are part of the config file
            For testruns just skip this get_contact and get_data_checker and use only sysadmin as receiver
        PARAMETER:
            results : which contains file path of README.IMO
            config : which contains links to local mail dictionary (obtained from README) and localmaillist
        CALLED BY:
            set_contacts
        RETURNS:
            dictionary with name and e-mails
        """

        mails = []
        dictkey = "{}{}".format(obscode.lower(), year)
        year = str(year)
        config = self.config
        obsdict = {}
        # Create mailing list
        # -----------
        # A) Extract from manually provided mailinglist for this observatory
        if os.path.isfile(config.get('mailinglist')):
            obsdict = methods.get_conf(config.get('mailinglist'))
        mails = obsdict.get(obscode, [])
        managers = obsdict.get('managers', [])
        if debug:
            print("A) Mails from provided maillinglist", mails)

        if not len(mails) > 0:
            # B) Local memory with yearly reference
            memmails = methods.read_memory(config.get('memory_mail'))
            mails = memmails.get(dictkey, [])
            if debug:
                print("B) Mails from memory", mails)
            if not len(mails) > 0:
                # C) Extract from minute README
                imodict = self.result.get(year).get('minute').get(obscode)
                if imodict and imodict.get('files'):
                    path = imodict.get('step1')
                    readmeimo = [f for f in imodict.get('files') if f.lower() == "readme.{}".format(obscode.lower())]
                    if debug:
                        print(" Found README", readmeimo)
                    if len(readmeimo) > 0:
                        mails = methods.extract_emails(os.path.join(path, readmeimo[0]))
                if debug:
                    print("C) Mails from readme", mails)
                if len(mails) > 0:
                    memmails[dictkey] = mails
                    methods.write_memory(memmails, path=config.get('memory_mail'), debug=False)
                else:
                    self.report.append(
                        "WARNING: could not obtain contact e-mails for {}, year {}".format(obscode, year))

        return mails

    def get_data_checker(self, obscode='XXX', year=str(1777), resolution='minute', debug=False):
        """
        DESCRIPTION
            determine a data checker for the IMO defined by obscode.
            Please note that only one data checker can be assigned for each record.
            The last one will be chosen.
            This method will access config and extract the default referee path.
            It will however search for a file containing "referee", YEAR and RESOLUTION first.
            If not found it will use "referee" and RESOLUTION.
            If no referee is found then fallback referees are used
            If duplicate entries for obscode are found, then the first input is used and a warning is issued
        PARAMETER:
            path ideally should be the same as for mail.cfg
        CALLED BY:
            set_contacts
        RETURNS:
            two strings, a name and a email address
        """
        checker = ''
        checkermail = ''
        refereefiles = []
        year = str(year)
        confpath = self.config.get('configpath')
        if debug:
            print("CONF", confpath)
        onlyfiles = [f for f in os.listdir(confpath) if os.path.isfile(os.path.join(confpath, f))]
        for i in onlyfiles:
            if "referee" in i.lower() and resolution in i and i.endswith('cfg'):
                refereefiles.append(i)
        if debug:
            print("Fitting referee files:", refereefiles)
        if len(refereefiles) > 0:
            refereepath = os.path.join(confpath, refereefiles[0])
        else:
            refereepath = self.config.get('{}refereepath'.format(resolution))
        if debug:
            print("Selected referee file:", refereepath)

        fallback = self.config.get("{}fallback".format(resolution), {"Max Mustermann": "max@mustermann.at"})

        if not refereepath or not os.path.isfile(refereepath):
            self.report.append("WARNING: DID NOT FIND REFEREE CONFIGURATION FILE")
            return fallback
        checkdict = methods.get_conf(refereepath)
        if debug:
            print ("dictionary", checkdict)
        for mail in checkdict:
            subdict = checkdict[mail]
            obslist = subdict.get('obslist', [])
            if not isinstance(obslist, list):
                obslist = [obslist]
            if mail.find("@") >= 0:
                if obscode in obslist:
                    checker = subdict.get('name', '')
                    checkermail = mail
            else:
                # specialdict
                dyear = subdict.get('year')
                if str(dyear) == str(year) and obscode in obslist:
                    checker = subdict.get('name', '')
                    checkermail = subdict.get('email', '')
        if not checker == '' and not checkermail == '':
            return {checker: checkermail}
        else:
            return fallback


    def get_imo(self, year=None, resolution=None, obscode='ZYX'):
        """
        DESCRIPTION:
            Get dict for specific obs
        RETURN:
            data dictionary
        APPLICATION:

        """
        year = str(year)
        if year and resolution and obscode:
            yeard = self.result.get(year)
            if yeard:
                rsd = yeard.get(resolution)
                if rsd:
                    imo = rsd.get(obscode)
                    return imo
        return {}


    def get_step(self, step=1, year=None, resolution='minute'):
        """
        DESCRIPTION:
            Get all IMO codes which are currently on this step
        RETURN:
            obslist
        APPLICTAION:

        """
        obslist = []
        if year:
            if isinstance(year, (list, tuple)):
                years = [str(y) for y in year]
            else:
                years = [str(year)]
        else:
            years = [y for y in self.result]
        for ye in years:
            resd = self.result.get(ye).get(resolution)
            for el in resd:
                obsd = self.result.get(ye).get(resolution).get(el)
                st = obsd.get('maximum_{}_step'.format(resolution))
                if st.endswith(str(step)):
                    obslist.append(el)
        return obslist


    def get_modified(self, year=None, resolution=None, obscode=None, timerange=None):
        """
        DESCRIPTION:
            Get all modified or new paths
        VARIABLES
            timerange : list : [start, end]
        RETURN:
            list of dictionaries with year, IMO, resolution and modification
        APPLICTAION:

        """
        output = []
        if not timerange or not isinstance(timerange, (list,tuple)):
            timerange = []
        if not len(timerange) == 2:
            timerange = []
        if year:
            if isinstance(year, (list, tuple)):
                years = [str(y) for y in year]
            else:
                years = [str(year)]
        else:
            years = [y for y in self.result]
        for ye in years:
            if resolution:
                res = [resolution]
            else:
                res = ['minute', 'second']
            for r in res:
                imo = []
                if obscode:
                    if isinstance(obscode, (list, tuple)):
                        imo = obscode
                    else:
                        imo = [obscode]
                else:
                    if self.result.get(ye).get(r):
                        imo = [im for im in self.result.get(ye).get(r)]
                if len(imo) > 0:
                    for im in imo:
                        obsd = self.result.get(ye).get(r).get(im)
                        if obsd:
                            mod = obsd.get('modification','')
                            exclude = obsd.get('exclude',False)
                            if mod and not exclude in ['True','true',True]:
                                content = { 'obscode' : im ,
                                            'year' : ye,
                                            'resolution' : r ,
                                            'lastmodified' : obsd.get('lastmodified','') ,
                                            'step1path' : obsd.get('step1','') ,
                                            'step2path' : obsd.get('step2','') ,
                                            'modification' : mod }
                                if timerange and testtime(timerange[0]) <= testtime(obsd.get('lastmodified','')) <= testtime(timerange[1]):
                                    output.append(content)
                                elif not timerange:
                                    output.append(content)
        return output


    def set_contacts(self, year=None, resolution=None, obscode='ZYX', debug=False):
        """
        DESCRIPTION:
            Set the modification flag, if flag is set to '' then moddict will be reset as well
        RETURN:
            data dictionary with new modification flag
        APPLICTAION:

        """
        year = str(year)
        if year and resolution and obscode:
            yeard = self.result.get(year)
            if yeard:
                rsd = yeard.get(resolution)
                if rsd:
                    imo = rsd.get(obscode)
                    imo['managers'] = self.get_manager_mails(debug=debug)
                    imo['contacts'] = self.get_contact_mails(obscode=obscode, year=year, debug=debug)
                    imo['referee'] = self.get_data_checker(obscode=obscode, year=year, resolution=resolution,
                                                           debug=debug)
        return self


    def set_modification(self, set='', year=None, resolution=None, obscode='ZYX'):
        """
        DESCRIPTION:
            Set the modification flag, if flag is set to '' then moddict will be reset as well
        RETURN:
            data dictionary with new modification flag
        APPLICTAION:
            imostatus = imostatus.set_modification(set='', obscode=secana.input.get('obscode'), year=secana.input.get('year'), resolution='second')
        """

        year = str(year)
        if not set in ['', 'new', 'updated', 'updated but already accepted', 'added to step2', 'added to step3', 'step2 reviewed']:
            print("Invalid set parameter provided")
            return self
        if year and resolution and obscode:
            yeard = self.result.get(year)
            if yeard:
                rsd = yeard.get(resolution)
                if rsd:
                    imo = rsd.get(obscode)
                    imo['modification'] = set
                    if not set:
                        imo['modfiles'] = []
        return self


    def update_level(self, level=None, year=None, resolution='second', obscode='ZYX'):
        """
        DESCRIPTION:
            Set the analysis grade/level, currently supported for second data.
            The level defines the grade the data set obtained while testing
            level 0 : significant errors
            level 1 : minor errors in data or missing meta information
            level 2 : all tests satisfied
        VARIABLES:
            level : string : needs to be string or None, '0','1' or '2'
        RETURN:
            data dictionary with new level flag
        APPLICTAION:
            Called after secondanalysis
        """
        year = str(year)
        if not level in [None,'0','1','2']:
            print("Invalid level provided")
            return self
        if year and resolution and obscode:
            yeard = self.result.get(year)
            if yeard:
                rsd = yeard.get(resolution)
                if rsd:
                    imo = rsd.get(obscode)
                    levelname = "{}level".format(resolution)
                    imo[levelname] = level
        return self


    def update_validity(self, year=None, resolution=None, includeobs=None, excludeobs=None):
        """
        DESCRIPTION:
            Update validity flag will change "exclude" flag of IMO data set
        RETURN:
            result dictionary updated
        APPLICTAION:
            imostatus = imostatus.update_validity(year=2022, resolution='minute', excludeobs=['CNB','XYZ'])
        """
        if not includeobs:
            includeobs = []
        if not excludeobs:
            excludeobs = []
        year = str(year)
        if year and resolution:
            obsdata = self.result.get(year).get(resolution)
            for obs in excludeobs:
                imolayer = obsdata.get(obs, {})
                if imolayer:
                    imolayer['exclude'] = True
            for obs in includeobs:
                imolayer = obsdata.get(obs, {})
                if imolayer:
                    imolayer['exclude'] = False
        return self


    def yearly_stats(self, resolution='minute'):
        """
        DESCRIPTION
            extract some yearly statistics
        REQUIREMENTS
            makes use of the collection module in order to return an ordered dictionary
        RETURNS
            statsdictionary
        """
        result = self.result
        statsdict = {}
        for year in result:
            step3list = []
            step2reviewlist = []
            step2list = []
            step1list = []
            dataformats = []
            levellist = []
            totallist = []
            leveldict = {}
            noisedict = {}
            resolutiondict = result.get(year).get(resolution,{})
            for imo in resolutiondict:
                imocontent = resolutiondict.get(imo)
                totallist.append(imo)
                if imocontent.get('step3'):
                    step3list.append(imo)
                elif imocontent.get('step2'):
                    if imocontent.get('review'):
                        step2reviewlist.append(imo)
                    else:
                        step2list.append(imo)
                elif imocontent.get('step1'):
                    step1list.append(imo)
                if imocontent.get('imbot_level') in [0,1,2]:
                    level = imocontent.get('imbot_level')
                    leveldict[imo] = level
                    levellist.append(level)
                if imocontent.get('noiselevel'):
                    noise = imocontent.get('noiselevel')
                    noisedict[imo] = noise
                if imocontent.get('dataformat'):
                    dataformats.append(imocontent.get('dataformat').upper())
            contdict = {i:dataformats.count(i) for i in dataformats}
            contdict["N_step3"] = len(step3list)
            contdict["N_step2accepted"] = len(step2reviewlist)
            contdict["N_step2"] = len(step2list)
            contdict["N_step1"] = len(step1list)
            contdict["N_total"] = len(totallist)
            contdict["LevelDetails"] = leveldict
            contdict["NoiseLevel"] = noisedict
            tmpdict = {i:levellist.count(i) for i in levellist}
            for el in tmpdict:
                contdict["Level"+str(el)] = tmpdict[el]
            statsdict[year] = contdict

        return collections.OrderedDict(sorted(statsdict.items()))


class TestImbotStep(unittest.TestCase):

    def test_runtime(self):
        # also tests idf and hdz tools
        config = {}

        referenced1 = {'kou21may.bin': '20231205', 'KOU2021_report.txt': '20231205', 'kou21apr.bin': '20231205', 'kou21feb.bin': '20231205', 'kou21jun.bin': '20231205', 'readme.kou': '20231205', 'kou21oct.bin': '20231205', 'kou21sep.bin': '20231205', 'kou2021.blv': '20231205', 'kou21mar.bin': '20231205', 'kou21nov.bin': '20231205', 'kou21dec.bin': '20231205', 'kou21jul.bin': '20231205', 'kou21jan.bin': '20231205', 'kou21aug.bin': '20231205', 'yearmean.kou': '20231205'}
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
        shutil.copytree(os.path.join(basepath, 'imbot', 'config'), "/tmp/imbottest/conf")
        if os.path.exists("/tmp/imbottest/memory"):
            shutil.rmtree("/tmp/imbottest/memory")

        imostatus = botstatus(config=config)  # allow for testrun which does not update operative imostatus
        sourcepath = "/tmp/imbottest/step1"
        step2path = "/tmp/imbottest/step2"
        # Create am initial result memory including only paths
        imostatus = imostatus.analyse_source(sourcepath, step=1, type='minute', debug=False)
        res1 = imostatus.result.get('2021').get('minute').get('KOU').get('step1')
        self.assertEqual(res1[-3:], 'KOU')

        empty = imostatus.get_contact_mails(obscode='KOU', year=2021, debug=False)
        self.assertEqual(empty, [])
        dc = imostatus.get_data_checker(year=2021, resolution='minute', obscode='KOU', debug=False)
        refname = [key for key in dc][0]
        self.assertEqual(refname, 'Maxi Musti')

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
                    #print ("assertexitsting key files exists and contains dict", imostatus.result.get('2021').get('minute').get('KOU').get('files'))
                    self.assertDictEqual(referenced1, imostatus.result.get('2021').get('minute').get('KOU').get('files'))
                    imostatus = imostatus.set_contacts(year=year, resolution=restype, obscode=obs)
                    self.assertEqual(['bcmt@ipgp.fr'], imostatus.result.get('2021').get('minute').get('KOU').get('contacts'))

        obsres = imostatus.get_imo(year=2021, resolution='minute', obscode='KOU')
        self.assertEqual(11, len([e for e in obsres]))
        modres = imostatus.get_modified(year=2021, resolution='minute')
        self.assertEqual(1, len(modres))

        imostatus = imostatus.update_validity(year=2021, resolution='minute', excludeobs=['KOU'])
        self.assertTrue(imostatus.result.get('2021').get('minute').get('KOU').get('exclude'))
        res2 = imostatus.result.get('2021').get('minute').get('KOU').get('modification')
        self.assertEqual(res2, 'new')
        imostatus = imostatus.set_modification(set='', year=2021, resolution='minute', obscode='KOU')
        res3 = imostatus.result.get('2021').get('minute').get('KOU').get('modification')
        self.assertEqual(res3, '')
        methods.write_memory(imostatus.result, path=imostatus.config.get('memory_directory_analysis'),debug=True)
        print ("PHASE 1 done") #, imostatus.result)

        # Testing step1 again and step2
        imostatus = imostatus.analyse_source(sourcepath, step=1, type='minute', debug=False)
        imostatus = imostatus.analyse_source(step2path, step=2, type='minute', debug=False)
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
        self.assertEqual('added to step2', modres[0].get('modification'))
        print ("PHASE 2 done") #, imostatus.result)
        imostatus = imostatus.set_modification(set='', year=2021, resolution='minute', obscode='KOU')

        # now add meta_IMO.txt, remove blv file and modify README
        shutil.copy(os.path.join(basepath,'imbot','templates','meta_OBSCODE.txt'), "/tmp/imbottest/step1/Mag2021/KOU/meta_KOU.txt")
        from pathlib import Path
        for p in Path("/tmp/imbottest/step1/Mag2021/KOU").glob("*.blv"):
            p.unlink()
        for p in Path("/tmp/imbottest/step1/Mag2021/KOU").glob("*.BLV"):
            p.unlink()
        with open('/tmp/imbottest/step1/Mag2021/KOU/readme.kou', 'a') as file:
            file.write('Added a note')
        # Testing step1 again
        imostatus = imostatus.analyse_source(sourcepath, step=1, type='minute', debug=False)
        imostatus = imostatus.analyse_source(step2path, step=2, type='minute', debug=False)
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

        res4 = imostatus.result.get('2021').get('minute').get('KOU').get('modfiles')
        key_a = [el for el in res4.get('added')][0]
        self.assertEqual('meta_KOU.txt', key_a)
        self.assertDictEqual({'kou2021.blv': '20231205'}, res4.get('removed'))
        key_b = [el for el in res4.get('value_diffs')][0]
        self.assertEqual('readme.kou', key_b)
        imostatus = imostatus.update_level(level='1', year=2021, obscode='KOU')
        print ("PHASE 3 done") #, imostatus.result)
        print (imostatus.report)
        stats = imostatus.yearly_stats()
        print (stats)

    def test_preparation(self):
        # also tests idf and hdz tools
        config = {}
        imostatus = botstatus(config=config)  # allow for testrun which does not update operative imostatus
        modificationlist = imostatus.get_modified()
        modificationlist = imostatus.add_minute_state(modificationlist, debug=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)