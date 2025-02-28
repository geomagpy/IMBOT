# -*- coding: utf-8 -*-

from imbot.core import methods
import os
import numpy as np
import pathlib
import re
import hashlib
from datetime import datetime, timedelta, timezone

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
|  imbot_steps     |  analyse_source  |      2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  _find_exclude   |      2.0.0 |      yes      |             |         | _get_step1_information |
|  imbot_steps     |  _get_step1_information | 2.0.0 |    yes      |             |         |           |
|  imbot_steps     |  _get_step_information | 2.0.0 |     yes      |             |         |           |
|  imbot_steps     |  get_contact_mails |    2.0.0 |      yes      |             |         | set_contacts |
|  imbot_steps     |  get_data_checker |     2.0.0 |      yes      |             |         | set_contacts |
|  imbot_steps     |  get_imo         |      2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  get_modified    |      2.0.0 |               |             |         |           |
|  imbot_steps     |  set_contacts    |      2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  set_modification |     2.0.0 |      yes      |             |         |           |
|  imbot_steps     |  update_validity |      2.0.0 |      yes      |             |         |           |


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
                           'sysadmin': {'Roman Leonhardt': 'ro.test'},
                           'memory_mail': '/tmp/imbottest/memory/memory_email.json',
                           'memory_directory_analysis': '/tmp/imbottest/memory/memory_directory_analysis.json'
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
            return
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
                obscode = root.replace(sourcepath, '')[1:4]
                obscode = obscode.upper()
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
                        filedict[f] = datetime.utcfromtimestamp(mtime).strftime("%Y%m%d")
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
                            datetime.utcfromtimestamp(youngest), datetime.now(timezone.utc) - timedelta(hours=checkrange)))
                    # only if latest file is at least "checkrange" hours old
                    if datetime.utcfromtimestamp(youngest) < datetime.now(timezone.utc) - timedelta(hours=checkrange):
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
                                imolayer['lastmodified'] = datetime.utcfromtimestamp(np.round(youngest, 0)).strftime(
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
                                print(filedict)
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
                                        print("Comparison", oldfiledict, filedict)
                                        imolayer['modfiles'] = methods.dictdiff(oldfiledict, filedict)
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

    def _get_step_information(self, imolayer, step=2, obscode='XXX', reviewidentifier="review", debug=False):
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
                imolayer = imostatus._get_step2_information(imolayer, obscode=obs, debug=False)
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
                print([f for f in files])
                # identify any eventually existing review file
                obscode = root.replace(sourcepath, '')[1:4]
                obscode = obscode.upper()
                filedict = {}
                contentname = "step{}date".format(step)
                if not imolayer.get(contentname, ''):
                    imolayer[contentname] = datetime.now().strftime("%Y-%m-%d")
                    imolayer['maximum_minute_step'] = "step{}".format(step)
                    imolayer['modification'] = "added to step{}".format(step)
                files = [f for f in files if not self._find_exclude(f)]
                if debug:
                    print("Found files in step{}:{}".format(step, files))
                if step == 2:
                    imolayer['review'] = False
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
        # Create mailing list
        # -----------
        # A) Extract from manually provided mailinglist for this observatory
        obsdict = methods.get_conf(config.get('mailinglist'))
        mails = obsdict.get(obscode, [])
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
            Please note that only one data checker can be asigned for each record.
            The last one will be chosen.
            This method will access config and extrat the default refereepath.
            It will howevere search for a file containin "referee", YEAR and RESOLUTIUON first.
            If not found it will use "referee" and RESOLUTIUON.
            If no referee is found then fallback referees are used
            If duplicate entries for obscode are found, then the first input is used and a waring is issued
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
        if debug:
            print("All referee files:", onlyfiles)
        for i in onlyfiles:
            if "referee" in i.lower() and str(year) in i and resolution in i:
                refereefiles.append(i)
        if len(refereefiles) > 0:
            refereepath = refereefiles
        else:
            refereepath = self.config.get('{}refereepath'.format(resolution))
        if debug:
            print("Referee file:", refereepath)

        fallback = self.config.get("{}fallback".format(resolution), {"Max Mustermann": "max@mustermann.at"})

        if not refereepath or not os.path.isfile(refereepath):
            self.report.append("WARNING: DID NOT FIND REFEREE CONFIGURATION FILE")
            return fallback
        checkdict = methods.get_conf(refereepath)
        for mail in checkdict:
            subdict = checkdict[mail]
            obslist = subdict.get('obslist', [])
            if not isinstance(obslist, list):
                obslist = [obslist]
            if obscode in obslist:
                checker = subdict.get('name', '')
                checkermail = mail
        if not checker == '' and not checkermail == '':
            return {checker: checkermail}
        else:
            return fallback

    def get_imo(self, year=None, resolution=None, obscode='ZYX'):
        """
        DESCRIPTION:
            Get dict for specfic obs
        RETURN:
            data dictionary
        APPLICTAION:

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

    def get_modified(self, year=None, resolution=None, obscode=None):
        """
        DESCRIPTION:
            Get all modified or new paths
        RETURN:
            data dictionary
        APPLICTAION:

        """
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
                if obscode:
                    if isinstance(obscode, (list, tuple)):
                        imo = obscode
                    else:
                        imo = [obscode]
                else:
                    imo = [im for im in self.result.get(ye).get(r)]
                if len(imo) > 0:
                    for im in imo:
                        obsd = self.result.get(ye).get(r).get(im)
                        mod = obsd.get('modification')
                        print(mod)

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

        """
        year = str(year)
        if not set in ['', 'new', 'update']:
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

