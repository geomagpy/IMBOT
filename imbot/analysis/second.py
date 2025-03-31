# -*- coding: utf-8 -*-

import sys
sys.path.insert(1, '/home/leon/Software/magpy/')  # should be magpy2
sys.path.insert(1,'/home/leon/Software/IMBOT/') # should be magpy2

import os
import numpy as np
from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from matplotlib.dates import date2num
from matplotlib import mlab
from imbot.core import methods
import glob
import fnmatch
from magpy.stream import DataStream, read, subtract_streams, magpyversion
from magpy.core.methods import nearestPow2
from magpy.core.activity import K_fmi
from magpy.lib.format_imagcdf import HEADTRANSLATE
from magpy.lib.magpy_formats import IMAGCDFMETA
import unittest


class second_definitive(object):
    """
    DESCRIPTION
        Analysis class for one-second data

    VARIABLES
        modificationdict :  contains a single dictionary with one second contents to be analyzed
        report  : list  : contains report messages acquired during runtime - to be used for logging
        config  : dict  : contains basic parameters and path definitions for the specfic application. Conif data should be read
                          from a dedicated configuration file of the following format
                             mainconfig   :   /home/leon/
                             # Default paths
                             minuterefereepath  :  /home/leon/refereelist_minute.cfg
                             secondrefereepath  :  /home/leon/refereelist_minute.cfg
                             minutefallback  :
                             #latestleapsecond  :  "20170101"  # get from cdflib

    APPLICATION

| class            |       method     | since vers |  validation   |  comment    | manual  |  *used by |
| ---------------- |  --------------  | ---------- | ------------- | ----------  | ------- | --------- |
|  **core**        |                  |            |               |             |         |           |
|  second_analysis |  __init__        |      2.0.0 |            |             |         |           |
|  second_analysis |  get_months      |      2.0.0 |            |             |         |           |
|  second_analysis |  _read_metadata  |      2.0.0 |            | each month  |         | read_month |
|  second_analysis |  read_month      |      2.0.0 |            | each month  |         |           |
|  second_analysis |  delta_f_test    |      2.0.0 |            | each month  |         |           |
|  second_analysis |  check_standard_level | 2.0.0 |            | each month  |         |           |
|  second_analysis |  _compare_meta   |      2.0.0 |            | each month  |         | check_diff_to_minute |
|  second_analysis |  check_diff_to_minute | 2.0.0 |            | each month  |         |           |
|  second_analysis |  extract_selected_days| 2.0.0 |            | each month  |         |           |
|  second_analysis |  _get_PSD        |      2.0.0 |            |             |         | psd_analysis |
|  second_analysis |  update_table    |      2.0.0 |            |             |         |           |
|  second_analysis |  psd_analysis    |      2.0.0 |            |             |         |           |
|  second_analysis |  write_report    |      2.0.0 |            |             |         |           |
|  second_analysis |  _write_meta_update_file | 2.0.0 |         |             |         | write_report |
|  second_analysis |  second_mail_text |     2.0.0 |            |             |         |           |

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
                           'second_local_step2': '/tmp/imbottest/second/step2/'
                           }
        self.report = []
        self.logdict = {}

        step2folder = self.config.get('second_local_step2', '/tmp/')
        year = self.input.get('year')
        obscode = self.input.get('obscode')
        self.step2folder = os.path.join(step2folder, year, obscode)

        if not self.input:
            self.report.append("second_analysis: no data provided - aborting")
            return

    def get_months(self):
        """
        DESCRIPTION:
            Reads data files with magpy, perform basic anaylsis and finally export data as ImagCDF
        PARAMETER:
            addinfo contains a link to additional meta information (e.g. provided on GITHUB, webpage, file, etc)
        RETURNS
            datelist for monthly read command
        """
        sourcepath = self.input.get('temporaryfolder')
        year = int(self.input.get('year'))
        datelist = []

        s = datetime(year, 1, 1)
        e = datetime(year + 1, 1, 1)
        datelist = [[(datetime(s.year, s.month, 1) - timedelta(days=1)).strftime('%Y-%m-%d'),
                     (datetime(s.year, s.month, 1) + relativedelta(months=1) + timedelta(days=1)).strftime('%Y-%m-%d')]]
        while s + timedelta(days=32) < e:
            s += timedelta(days=32)
            datelist.append([(datetime(s.year, s.month, 1) - timedelta(days=1)).strftime('%Y-%m-%d'),
                             (datetime(s.year, s.month, 1) + relativedelta(months=1) + timedelta(days=1)).strftime(
                                 '%Y-%m-%d')])
            s = s.replace(day=1)

        return datelist

    def _read_metadata(self, filename="meta*.txt", debug=False):
        """
        DESCRIPTION
             read additional metainformation for the specific observatory
        """
        IMAGCDFKEYDICT = methods.IMAGCDFKEYDICT

        def _key_convert(key):
            magpykey = IMAGCDFKEYDICT.get(key, key)
            return magpykey

        sourcepath = self.input.get('temporaryfolder')
        newhead = {}
        if os.path.isfile(sourcepath):
            if debug:
                print(" read_metadata: from sourcepath=file")
            metafilelist = [sourcepath]
        else:
            if debug:
                print(" read_metadata: from sourcepath {}".format(sourcepath))
            metafilelist = glob.glob(os.path.join(sourcepath, filename))

        if len(metafilelist) > 0:
            print(" Found auxiliary meta file:", metafilelist)
            if os.path.isfile(metafilelist[0]):
                with open(metafilelist[0], 'r') as infile:
                    for line in infile:
                        if not line.startswith('#'):
                            if line.find(" : ") > 0 or line.find("\t:\t") > 0 or line.find(" :\t") > 0 or line.find(
                                    "\t: ") > 0:
                                paralist = line.replace(" ", "").split(":")
                                # convert paralist [0] to MagPy keys
                                key = _key_convert(paralist[0].strip())
                                try:
                                    newhead[key] = paralist[1].strip()
                                except:
                                    pass
        return newhead

    def read_month(self, dates, optionalheads=None,
                   debug=False):
        """
        DESCRIPTION:
            reading one month of data and checking contents
        """
        sourcepath = self.input.get('temporaryfolder')
        if not optionalheads:
            optionalheads = ['StationWebInfo', 'DataTerms', 'DataReferences']
        metainfo = {}
        issues = {}
        improvements = {}
        warningdict = {}
        tempdict = {}
        scalardict = {}
        allcontents = []
        logdict = {}
        t1 = datetime.now()

        IMAGCDFKEYDICT = methods.IMAGCDFKEYDICT
        starttime = dates[0]
        endtime = dates[1]
        st = datetime.strptime(starttime, '%Y-%m-%d') + timedelta(days=1)
        et = datetime.strptime(endtime, '%Y-%m-%d') - timedelta(days=1)
        days = int(date2num(et) - date2num(st))
        expectedcount = int(days * 24. * 3600.)
        month = (st + timedelta(days=10)).strftime("%m (%b)")

        print(
            "Analyzing second data from {},{} for {}".format(self.input.get('obscode'), self.input.get('year'), month))

        try:
            data = read(os.path.join(sourcepath, '*'), starttime=starttime, endtime=endtime)
        except:
            data = DataStream()
        if debug:
            print("data loaded")
        data = data.trim(starttime=st, endtime=et)
        if debug:
            print("data trimmed")

        newmeta = self._read_metadata()
        if debug:
            print(" got new meta data", newmeta)

        if len(data) > 1:
            print("  -> got {} values for {}".format(len(data), data._get_key_headers()))
            self.logdict['Stationname'] = data.header.get('StationName')
            # drop flagged data
            if data.header.get('DataFlags'):
                print("Found flagging information - flagging contents updated for MagPy2.0 compatibility")
                #fl = data.header.get('DataFlags')
                #data = fl.apply_flags(data, mode='drop')
            contents = data.header.get('FileContents')
            if contents:
                if debug:
                    print("Found different timecolumns", contents)
                # get maxlength in contents
                maxlen = np.max([cont[0] for cont in contents])
                for cont in contents:
                    timecol = cont[1].replace('Times', '')
                    timelen = cont[0]
                    if timecol.find('Temperature') >= 0 and timelen < maxlen:
                        tempdata = read(os.path.join(sourcepath, '*'), starttime=starttime, endtime=endtime,
                                        select=timecol)
                        temp1 = tempdata._get_column('t1')
                        temp2 = tempdata._get_column('t2')
                        tempdict = {cont[1]: tempdata}
                        allcontents.append(tempdict)
                        if len(temp1) > 0:
                            try:
                                txt = "{:.2f}+/-{:.2f} degC".format(np.nanmean(temp1), np.nanstd(temp1))
                                logdict['Temperature1 record'] = "Temperature1: {}".format(txt)
                                print(" Temperature1: {}".format(txt))
                            except:
                                pass
                        if len(temp2) > 0:
                            try:
                                txt = "{:.2f}+/-{:.2f} degC".format(np.nanmean(temp2), np.nanstd(temp2))
                                logdict['Temperature2 record'] = "Temperature2: {}".format(txt)
                                print(" Temperature2: {}".format(txt))
                            except:
                                pass
                    if timecol.find('Scalar') >= 0 and timelen < maxlen:
                        scalardata = read(os.path.join(sourcepath, '*'), starttime=starttime, endtime=endtime,
                                          select=timecol)
                        f2text = "Found F differing in sampling period ({} sec) from vector data. No delta F test conducted\n".format(scalardata.samplingrate())
                        logdict['F'] = f2text
                        scalardict = {cont[1]: scalardata}
                        allcontents.append(scalardict)
            cntbefore = len(data)
            data = data.get_gaps()
            cntafter = len(data)
            st, et = data.timerange()
            if debug:
                print(" read_month: got range from {} to {}".format(st, et))
            effectivedays = int(date2num(et) - date2num(st)) + 1
            ### Try to load any additional meta information provided in file meta_obscode.txt
            if len(newmeta) > 0:
                print("Observatory provided additional meta information: {}".format(newmeta))
                warningdict[
                    'Additional Meta Information'] = "The observatory provided additional meta information using a meta file template: included only into step2 data files"
                for key in newmeta:
                    nkey = key
                    if debug:
                        print("Appending new meta info for {}".format(key))
                    for cdfhead in HEADTRANSLATE:
                        if cdfhead.find(key) > -1 or HEADTRANSLATE[cdfhead].find(key) > -1:
                            nkey = HEADTRANSLATE[cdfhead]
                    if debug:
                        print(" {}".format(nkey))
                    data.header[nkey] = newmeta[key]
            # Write parameters for monthly report
            # print ("Datalimits from {} to {}".format(st,et))
            logdict['Datalimits'] = [st, et]
            #logdict['Data format'] = data.header.get('DataFormat')
            logdict['N'] = len(data)
            logdict['Leap second update'] = data.header.get('DataLeapSecondUpdated')
            # if not str(latestleapsecond) == str(data.header.get('DataLeapSecondUpdated')):
            #    warningdict['Leap second'] = 'Leap second table seems to be outdated - please check'
            logdict['Filled gaps'] = cntafter - cntbefore
            logdict['Difference to expected amount'] = expectedcount - cntafter
            logdict['Level'] = 2
            sr = data.samplingrate()
            logdict['Samplingrate'] = '{} sec'.format(sr)

            if not (expectedcount - cntafter) == 0:
                # Allow a confirmation in newmeta to indicate that missing data is not available and thus does not need to be considered for monthly file generation - but keep issue
                # Example BDV2016 - the submitted files apparently repeat the same dates each month...
                if newmeta.get('MissingData', '') in ['confirmed', 'Confirmed', 'confirm']:
                    logdict['Missing data'] = 'confirmed as missing by submitter'
                else:
                    logdict['Level'] = 1
                    issues[
                        'MissingData'] = 'Amount of data points {} does not correspond to the expected amount {}'.format(
                        cntafter, expectedcount)
            if (effectivedays * 24 * 3600) < cntafter:
                # apparently more data than expected for coverage (duplicates)
                logdict['Level'] = 0
                issues['Data coverage'] = 'Check data files for duplicates and correct coverage'
            if not sr == 1:
                logdict['Level'] = 0
                issues['Samplingrate'] = 'Found sampling rate of {} sec, expected is 1 sec'.format(sr)
            for head in IMAGCDFMETA:
                if not head == 'DataReferences':  # TODO check that
                    value = data.header.get(head, '')
                    if value == '':
                        metainfo[head] = 'missing'
                        if not head in optionalheads:
                            issues[head] = 'header {} missing'.format(
                                head.replace("Data", "").replace("Sensor", "").replace("Station", ""))
                            if not logdict.get('Level') == 0:
                                logdict['Level'] = 1
                        else:
                            improvements[head] = 'provide information on {}'.format(
                                head.replace("Data", "").replace("Sensor", "").replace("Station", ""))
                    else:
                        metainfo[head] = value
        else:
            if newmeta.get('MissingData', '') in ['confirmed', 'Confirmed', 'confirm']:
                logdict['Missing data'] = 'confirmed as missing by submitter'
                warningdict[
                    'Missing data'] = 'missing data confirmed by submitter - please verify that all data has been correctly uploaded as IMBOT in this case cannot distinguish between corrupted and missing data'
            else:
                logdict['Level'] = 0
                issues['Data coverage'] = 'Check data files - data files missing?'

        logdict['Header'] = metainfo
        logdict['Issues'] = issues
        logdict['Warnings'] = warningdict
        logdict['Improvements'] = improvements
        self.logdict[month] = logdict
        if debug:
            t2 = datetime.now()
            print("read_month needed {:.1f} sec".format((t2 - t1).total_seconds()))

        # if debug:
        #    print (" Obtained level {} for this month after checking data contents, data coverage and meta information".format(self.logdict.get('Level')))
        return data, allcontents

    def delta_f_test(self, data, debug=False):
        """
        DESCRIPTION
            reading F values in file, analyzing independency and delta F variaton
        """
        month = (data.start() + timedelta(days=10)).strftime("%m (%b)")
        logdict = self.logdict.get(month)
        issuedict = logdict.get('Issues', {})
        warningdict = logdict.get('Warnings', {})
        fcol = data._get_column('f')
        dfcol = data._get_column('df')
        fmean = 99
        fstd = 99
        if len(fcol) == 0 and len(dfcol) == 0:
            print("  No F or dF values found in main data set")
            if not logdict.get('F',''): # if F with different time column is contained than keep the information
                logdict['F'] = "None"
            logdict['delta F'] = "None"
        else:
            if debug:
                print(" found F/S or G column in data file")
            f1text = 'found f-col - problem -'
            scal = ''
            if len(fcol) > 0:
                scal = 'f'
            elif len(dfcol) > 0:
                scal = 'df'
            ftest = data.copy()
            ftest = ftest._drop_nans(scal)
            fsamprate = ftest.samplingrate()
            f1text = "found independend"
            if scal == 'f':
                ftest = ftest.delta_f()
            # TODO proper treatment of -S values in delta_f in MagPy
            # or ignore: G is quality value for variometer data and
            # should be provided for existing variometer values.
            # If F(S) should be provided, an independent measurement with
            # with eventually different sampling rate or data value at non-existing
            # variometer data, then please provide it as S. G can be easily calculated
            # quick workaround -> exclude large negative  values
            ftest = ftest.extract('df', -15000, '>')
            fmean, fstd = ftest.mean('df', std=True)
            if np.isnan(fmean):
                warningdict['F'] = 'mean delta F could not be determined - please check F/S/G values in cdf'
                print(" Significant amount of F values could not be extracted - only NAN contained?")
            if debug:
                print(" mean delta F of {:.3f} with a std of {:.3f}".format(fmean, fstd))
            logdict['delta F'] = "mean delta F of {:.3f} with a std of {:.3f}".format(fmean, fstd)
            if np.abs(fmean) >= 1.0:
                warningdict['F'] = 'mean delta F exceeds 1 nT'
            if fstd >= 3.0:
                issuedict['F'] = 'dF/G shows large scatter about mean'
            if np.abs(fmean) < 0.01 and fstd < 0.01:
                f1text = 'found'  # eventually not-independent
            if np.abs(fmean) < 0.001 and fstd < 0.001:
                f1text = 'found not-independend'

            f2text = "{} {} with sampling period: {} sec\n".format(f1text, scal, fsamprate)
            logdict['F'] = f2text

        logdict['Issues'] = issuedict
        logdict['Warnings'] = warningdict
        self.logdict[month] = logdict

        return

    def check_standard_level(self, data, partialcheck=None, debug=False):
        """
        DESCRIPTION
            extracting Standard levels as required from ImagCDF and creating a table.
            Some contents will be checked

        STANDARD LEVELS
            as contained in variable partial
            One-second Data: Specifications in the Pass Band [DC to 8mHz (120s)]
            IMOS-01  Time-stamp accuracy (centred on the UTC second): 0.01s
            IMOS-02  Phase response: Maximum group delay: ±0.01s
            IMOS-03  Maximum filter width: 25 seconds
            IMOS-04  Instrument amplitude range:     ≥±4000nT High Lat., ≥±3000nT Mid/Equatorial Lat.
            IMOS-05  Data resolution: 1pT
            IMOS-06  Pass band: DC to 0.2Hz
            IMOS-11  Noise level: ≤100pT RMSIMOS-12Maximum offset error (cumulative error between absolute observations): ±2. 5 nT
            IMOS-13  Maximum component scaling plus linearity error: 0.25%
            IMOS-14  Maximum component orthogonality error: 2mrad
            IMOS-15  Maximum Z-component verticality error: 2mrad
            One-second Data: Specifications in the Pass Band [8mHz (120s) to 0.2Hz]
            IMOS-21  Noise level:                        ≤10pT/√Hz at 0.1 Hz
            IMOS-22  Maximum gain/attenuation: 3dB
            One-second Data: Specifications in the Stop Band [≥ 0.5 Hz]
            IMOS-31  Minimum attenuation in the stop band (≥ 0.5Hz): 50dB
            One-second Data: Auxiliary measurements:
            IMOS-41  Compulsory full-scale scalar magnetometer measurements with a data resolution of 0.01nT at a minimum sample period of 30 seconds.
            IMOS-42  Compulsory vector magnetometer temperature measurements with a resolution of 0.1°C at a minimum sample period of one minute

        VARIABLES
            data    (MagPy DataStream) 	: data and meta information
            partiacheck   (dict) 	: contains Standard levels and their description
            logdict	(dict)		: logdict with Issue information

        RETURN
            table with (list) with partial standard description and whether these points are met/considered
            logdict with an updated Issue subdictionary
        """
        month = (data.start() + timedelta(days=10)).strftime("%m (%b)")
        logdict = self.logdict.get(month)
        warningdict = logdict.get('Warnings', {})
        issuedict = logdict.get('Issues', {})
        if not partialcheck:
            partialcheck = {}
        tablelist = []
        head = data.header
        if head.get('DataStandardLevel', '') in ['full', 'Full', 'FULL']:
            # all criteria have been confirmed
            if debug:
                print("StandardLevel: full")
            for key in partialcheck:
                tableline = []
                tableline.append(key)
                tableline.append(partialcheck.get(key))
                if key in ['IMOS41', 'IMOS-41'] and (
                        logdict.get('F') in ['None', ''] or logdict.get('F').startswith('found no')):
                    tableline.append('confirmed but invalid')
                    warningdict['StandardLevel - IMOS-41'] = 'IMOS41 confirmed but no F-values provided'
                elif key in ['IMOS42', 'IMOS-42'] and logdict.get('T') in ['None', '']:
                    tableline.append('confirmed but invalid')
                    warningdict['StandardLevel - IMOS-42'] = 'IMOS42 confirmed but no temperature values provided'
                else:
                    tableline.append('validity confirmed by submitter')
                tablelist.append(tableline)
        elif head.get('DataStandardLevel', '') in ['partial', 'Partial', 'PARTIAL']:
            pkeyl = [key for key in head if key.find('PartialStandDesc') > -1]
            if len(pkeyl) > 0:
                partialvals = head.get(pkeyl[0])
            else:
                partialvals = []
            # print ("Partial descriptions necessary. They look like:", partialvals)
            if partialvals and not isinstance(partialvals, list):
                if debug:
                    print('partialvals are not provided as list - converting')
                partialvals = partialvals.split(',')
            # Convert IMOS41 to IMOS-41
            nl = []
            for el in partialvals:
                if el.startswith('IMOS') and not el.startswith('IMOS-'):
                    nl.append(el.replace('IMOS', 'IMOS-'))
                else:
                    nl.append(el)
            partialvals = ",".join(nl)
            if debug:
                print("StandardLevel: partial -  provided partial values look like:", partialvals)
            for key in partialcheck:
                tableline = []
                tableline.append(key)
                tableline.append(partialcheck.get(key))
                # try:
                ok = True
                if ok:
                    if partialvals.find(key) > -1:
                        if debug:
                            print("Found the key {} in partialvals".format(key))
                        tableline.append('validity confirmed by submitter')
                        if key == 'IMOS-41' and (
                                logdict.get('F') in ['None', ''] or logdict.get('F').startswith('found no')):
                            print(" F values missing although IMOS41")
                            tableline.append('confirmed but invalid')
                            warningdict['StandardLevel - IMOS41'] = 'IMOS41 confirmed but no F values found'
                        elif key == 'IMOS-42' and logdict.get('T') in ['None', '']:
                            print(" temperature values missing although IMOS42")
                            tableline.append('confirmed but invalid')
                            warningdict['StandardLevel - IMOS42'] = 'IMOS42 confirmed but no temperature values found'
                    else:
                        tableline.append('not met as confirmed by submitter')
                # except:
                #    tableline.append('information missing')
                #    issuedict['PartialStandDesc'] = 'PartialStandDesc required for partial - see TN8: 4.7 Relevant data standards'
                tablelist.append(tableline)
        else:
            issuedict['StandardLevel'] = 'StandardLevel full or partial - see TN8: 4.7 Relevant data standards'
            issuedict[
                'PartialStandDesc'] = 'PartialStandDesc required for partial - see TN8: 4.7 Relevant data standards'
            for key in partialcheck:
                tableline = []
                tableline.append(key)
                tableline.append(partialcheck.get(key))
                tableline.append('not provided')
                tablelist.append(tableline)

        logdict['Issues'] = issuedict
        logdict['Warnings'] = warningdict
        self.logdict[month] = logdict

        return tablelist

    def _compare_meta(self, minhead, sechead, mindatadict, month=1, debug=False):
        """
        DESCRIPTION:
            compare meta information of second and minutedata
        """
        logdict = self.logdict.get(month)
        issuedict = logdict.get('Issues', {})
        warningdict = logdict.get('Warnings', {})

        if debug:
            print("Minute data header: {}".format(minhead))
            print("Second data header: {}".format(sechead))

        diffcnt = 0
        keyname = ''
        refvalue = ''
        compvalue1 = ''
        excludelist = ['DataFormat', 'SensorID', 'DataComponents', 'DataSamplingRate', 'DataPublicationDate',
                       'DataSamplingFilter', 'DataDigitalSampling', 'StationInstitution']
        floatlist = {'DataElevation': 0, 'DataAcquisitionLongitude': 2, 'DataAcquisitionLatitude': 2}
        if minhead and sechead:
            for key in sechead:
                if not key.startswith('col') and not key.startswith(
                        'unit') and not key in excludelist and key in minhead:
                    onlywarn = False
                    if debug:
                        print("Checking key: {}".format(key))
                    refvalue = str(sechead.get(key))
                    compvalue1 = str(minhead.get(key, ''))
                    keyname = key.replace('Data', '').replace('Station', '')
                    refshort = refvalue
                    compshort = compvalue1
                    if key in floatlist:
                        try:
                            refshort = np.round(float(refvalue), floatlist.get(key))
                        except:
                            refshort = 0
                        try:
                            compshort = np.round(float(compvalue1), floatlist.get(key))
                        except:
                            compshort = 0
                    if key == 'DataSensorOrientation':
                        refshort = refvalue.lower()[:3]
                        compshort = compvalue1.lower()[:3]
                        # only warn here as both data sources might come from different instruments
                        onlywarn = True
                    if not refshort == compshort:
                        if not onlywarn:
                            diffcnt += 1
                        warningdict[keyname] = "found differences for {}: {} (sec) vs {} (min)".format(keyname,
                                                                                                       refvalue,
                                                                                                       compvalue1)
                        if debug:
                            print(" Found diff for {}: {} (sec) vs {} (min)".format(keyname, refvalue, compvalue1))
                        # mindatadict['meta-info diff'] = "{}: {} (sec) vs {} (min)".format(keyname, refvalue, compvalue1)
            if diffcnt == 0:
                mindatadict[
                    'meta-info diff'] = "meta information agrees with contents of minute data (note: location data compared at accuracy of 2 digits)".format(
                    keyname, refvalue, compvalue1)
            else:
                issuedict['meta-info minute vs second data'] = "differences observed - see below"
        else:
            mindatadict['meta-info minute vs second data'] = "could not access meta information"
            issuedict['meta-info minute vs second data'] = "could not access meta information"

        logdict['Issues'] = issuedict
        logdict['Warnings'] = warningdict
        self.logdict[month] = logdict

        return mindatadict

    def check_diff_to_minute(self, data, daterange=None, debug=False):
        """
        DESCRIPTION
            Compares the definitive one second data product to one minute
            Please note: differences between the two data products need to be large
            to trigger an automatic issue. The report, however, will contain a summary
            of any questinable differences.
        PARAMETER
            minutesorce needs to be the basedirectory of one mintue data
            this source is scanned for subdirctories with OBSCODE as name
        PROCESSING
            - one second data will be filtered using IM recommended standards
            - filtered on second will then be subtracted from one minute data
            - differences are then analyzed
            - only vector components (x,y,z) are considered
        CHECKING
            - maximal difference amplitudes for each month
            - average difference and its distribtion
            - since 1.0.4: basic meta data
        EXPECTED VALUES
            1. average difference needs to be zero, its distribution below the "numerical noise"
            (numerial noise arises from the 0.1 nT resolution if IAF data and the < 0.01 nT
             resolution of one second data and its filtered product; )
            2. maximal amplitudes shoud be in the order of the numerical noise
        CONSEQUENCES
            If the mean difference is significantly larger than zero, both for daily means and monthly
            mean, then both data sets are termed "different" and the submitting institue needs to clarify
            which one is definitive (data remains on level 1)
            Individual difference spikes and larger deviations indicate that one or a combination
            of different filtering procedures, different outlier treatment, gap treatment, baseline methods,
            or different instruments with other noise characteristics are used for the data sets.
            The average differences are listed in the report, to be considered for level 3 evaluation.
        """

        mindatadict = {}
        quietdays = []
        if not daterange:
            daterange = []
        month = (data.start() + timedelta(days=10)).strftime("%m (%b)")
        logdict = self.logdict.get(month)
        issuedict = logdict.get('Issues', {})
        warningdict = logdict.get('Warnings', {})
        logdict['Definitive comparison'] = 'definitive one-minute not available or not readable'

        minutepath = self.input.get('minutepath')
        minutestep = self.input.get('minutestep')

        mindata = DataStream()
        highresfilt = DataStream()
        if minutepath:
            try:
                print(" Comparing with minute data: ", minutepath, daterange[0], daterange[1])
                mindata = read(minutepath, starttime=daterange[0], endtime=daterange[1])
                print("  -> success. Got {} data points".format(len(mindata)))
            except:
                if debug:
                    print("Problem when reading minute data")
                logdict['Definitive comparison'] = 'definitive one-minute not available or not readable'
                mindata = DataStream()
        if minutepath and len(mindata) > 1:
            secdata = data.copy()
            if debug:
                print(" Time range of one-seconddata: {}".format(secdata.timerange()))
            mindatadict = self._compare_meta(mindata.header, secdata.header, mindatadict, month=month, debug=debug)
            highresfilt = secdata.filter(missingdata='iaga')
            mindata = mindata.trim(highresfilt.start(), highresfilt.end() + timedelta(seconds=1))
            if debug:
                print("  -> seconddata filtered to one-minute using iaga standard filter")
            diff = subtract_streams(highresfilt, mindata, keys=['x', 'y', 'z'])
            if debug:
                print("  -> diff calculated")
            # drop the first time step - quick and dirty - remove if filtering has been checked
            drop = True
            if drop:
                if debug:
                    print("  -> diff length: {}".format(diff.length()[0]))
                if diff.length()[0] > 0:
                    diff = diff.trim(starttime=diff.start() + timedelta(minutes=1))
                if debug:
                    print("  -> removed first insufficiently filtered timestep")
                    print("  -> diff length: {}".format(len(diff)))
            xd, xdst = diff.mean('x', std=True)
            yd, ydst = diff.mean('y', std=True)
            zd, zdst = diff.mean('z', std=True)
            try:
                xa = diff.amplitude('x')
                ya = diff.amplitude('y')
                za = diff.amplitude('z')
            except:
                print("Problem determining amplitudes...")
                xa = 0.00
                ya = 0.00
                za = 0.00
            if debug:
                print("  -> amplitudes determined")
            mindatadict['mean difference - x component'] = "{:.3} nT".format(xd)
            mindatadict['mean difference - y component'] = "{:.3} nT".format(yd)
            mindatadict['mean difference - z component'] = "{:.3} nT".format(zd)
            mindatadict['stddev of difference - x component'] = "{:.3} nT".format(xdst)
            mindatadict['stddev of difference - y component'] = "{:.3} nT".format(ydst)
            mindatadict['stddev of difference - z component'] = "{:.3} nT".format(zdst)
            mindatadict['amplitude of difference - x component'] = "{:.3} nT".format(xa)
            mindatadict['amplitude of difference - y component'] = "{:.3} nT".format(ya)
            mindatadict['amplitude of difference - z component'] = "{:.3} nT".format(za)
            if debug:
                print("  -> dictionary written")
            if max(xd, yd, zd) > 0.3:
                warningdict[
                    'Definitive differences'] = 'one-minute and one-second data differ by more than 0.3 nT in monthly average'
                logdict[
                    'Definitive differences'] = 'One-minute and one-second data differ by more than 0.3 nT in a monthly average'
            if max(xa, ya, za) < 0.12:
                logdict[
                    'Definitive comparison'] = 'excellent agreement between definitive one-minute and one-second data products'
            elif max(xa, ya, za) <= 0.3:
                logdict[
                    'Definitive comparison'] = 'good agreement between definitive one-minute and one-second data products'
            elif max(xa, ya, za) > 0.3 and max(xa, ya, za) <= 5:
                logdict[
                    'Definitive comparison'] = 'small differences in peak amplitudes between definitive one-minute and one-second data products observed'
            elif max(xa, ya, za) > 5:
                warningdict[
                    'Definitive comparison'] = 'Large amplitude differences between definitive one-minute and one-second data products'
                logdict[
                    'Definitive comparison'] = 'Large amplitude differences between definitive one-minute and one-second data products'
            if np.isnan(sum([xd, yd, zd, xa, ya, za])):
                logdict['Definitive comparison'] = 'not conclusive as NAN values are found'
            if debug:
                print("  -> one-minute comparison finished")
        else:
            warningdict['Comparison with definitive one-minute'] = 'definitive one-minute not available or not readable'

        logdict['Issues'] = issuedict
        logdict['Warnings'] = warningdict
        logdict['DefinitiveStatus'] = mindatadict
        self.logdict[month] = logdict

        if len(mindata) > 0:
            kvals = K_fmi(mindata, K9_limit=mindata.header.get('StationK9'), longitude=mindata.header.get('DataAcquisitionLongitude'))
            dmkvals = kvals.dailymeans(keys=['var1'])
            K = 3
            res = sorted(range(len(dmkvals.ndarray[1])), key=lambda sub: dmkvals.ndarray[1][sub])[:K]
            quietdays = [dmkvals.ndarray[0][i].strftime("%Y-%m-%d") for i in res]

        return quietdays

    def extract_selected_days(self, data, dates, selecteddays=None, dayformat='text', debug=False):
        """
        DESCRIPTION
            extract selected quiet days for spectral analysis
        RETURNS
            stream list with daily datastreams
        """
        dailystreamlist = []
        startdate = datetime.strptime(dates[0], '%Y-%m-%d')
        enddate = datetime.strptime(dates[1], '%Y-%m-%d')

        if not selecteddays:
            print("No quiet day list provided - skipping")
            return []

        daylist = [startdate + timedelta(days=el) for el in range(1, 40) if
                   startdate + timedelta(days=el + 1) < enddate]
        if not dayformat == 'datetime':
            daylist = [el.strftime('%Y-%m-%d') for el in daylist]

        for day in selecteddays:
            if day in daylist:
                if debug:
                    print("Found a quiet day ({}) for power analysis - extracting information:".format(day))
                dayst = DataStream()
                dayar = data._select_timerange(starttime=day,
                                               endtime=datetime.strptime(day, '%Y-%m-%d') + timedelta(days=1))
                dayst.ndarray = dayar
                dayst.header = data.header
                if dayst.length()[0] > 0:
                    dailystreamlist.append(dayar)
                    del dayar

        return dailystreamlist

    def export_month(self, data, allcontents, debug=False):
        """
        DESCRIPTION
            exporting final data to an monthly IMAGCDF file
        """
        destinationpath = self.step2folder
        success = True
        scalar, temp1, temp2 = None, None, None

        if debug:
            print("Writing IMAGCDF file")
            print(" - Length:", len(data))
        for cont in allcontents:
            if debug:
                print("Writing additional contents:", cont)
            scalar = cont.get("GeomagneticScalarTimes", None)
            temp1 = cont.get("Temperature1Times", None)
            temp2 = cont.get("Temperature2Times", None)
            temp1 = cont.get("TemperatureTimes", None)
            data.header['FileContents'] = None
        try:
            success = data.write(destinationpath, coverage='month', format_type='IMAGCDF', scalar=scalar,
                                 temperature1=temp1, temperature2=temp2)
            del data
            del allcontents
        except:
            sucess = False
        if success:
            print(" ... monthly treatment successful")
        return success

    def _get_PSD(self, stream, comp):
        dt = stream.samplingrate()
        t = np.asarray(stream._get_column('time'))
        val = np.asarray(stream._get_column(comp))
        mint = np.min(t)
        tnew, valnew = [], []
        nfft = int(nearestPow2(len(t)))
        if nfft > len(t):
            nfft = int(nearestPow2(len(t) / 2.0))

        for idx, elem in enumerate(val):
            if not np.isnan(elem):
                tnew.append((t[idx] - mint).total_seconds())
                valnew.append(elem)

        tnew = np.asarray(tnew)
        valnew = np.asarray(valnew)

        psdm = mlab.psd(valnew, nfft, 1 / dt)
        asdm = np.sqrt(psdm[0])
        freqm = psdm[1]

        return (psdm, asdm, freqm)

    def update_table(self, tablelist, month='01 (Jan)', debug=False):
        # get noiselevel
        monthdict = {}
        lower95noiselevelbound = (float(self.logdict.get('Noiselevel')) - 2 * float(
            self.logdict.get('NoiselevelStdDeviation'))) * 1000.
        try:
            monthdict = self.logdict.get(month)
            warndict = monthdict.get('Warnings')
        except:
            warndict = {}
        if lower95noiselevelbound > 100:
            comment = " - IMBOT indicates failure"
        else:
            comment = " - IMBOT indicates validity"
        if debug:
            print(" updating IMOS table with:", comment)
        newtablelist = []
        for row in tablelist:
            if row[0] == 'IMOS-11':
                if row[2].startswith('validity') and comment.endswith('failure'):
                    # print ("Add a waring that the noise level exceeds the IM criteria and eventually update info in tablelist")
                    warndict['Noiselevel'] = "Noiselevel apparently exceeds 100 pT"
                    try:
                        monthdict['Warnings'] = warndict
                        self.logdict[month] = monthdict
                    except:
                        pass
                row[2] += comment
            newtablelist.append(row)

        return newtablelist

    def psd_analysis(self, dailystreamlist, period=10., debug=False):
        """
        DESCRIPTION
            very simple noiselevel analysis
            calculates mean noise level below a certain threshold period (e.g. 10sec)
            from each daily stream
        RETURNS
            dictionary input at "Noiselevel" containing the arithmetic mean of all noiselevels
            dictionary input at "NoiselevelStdDeviation" containing the StandardDeviation of all noiselevels
        """

        def drop_outliers(inputarray, threshold = 3.5):
            # Drop significant outliers from noiselevel list
            d = np.abs(inputarray - np.median(inputarray))
            mdev = np.median(d)
            s = d / mdev if mdev else np.zeros(len(d))
            return inputarray[s < threshold]

        nl = 0
        nlstd = 0
        print("Running Power Analysis for {} records".format(len(dailystreamlist)))
        if len(dailystreamlist) > 0:
            noiselevellist = []
            failedlist = [0]
            for daystream in dailystreamlist:
                dayst = DataStream()
                dayst.ndarray = daystream
                if debug:
                    print(daystream, dayst.length()[0])

                if dayst.length()[0] > 0:
                    try:
                        # print( "getting power")
                        (psdm, asdm, freqm) = self._get_PSD(dayst, 'x')
                        # print( "getting power 2", len(asdm))
                        asdmar = np.asarray(asdm)
                        idx = (np.abs(freqm - (
                                    1. / period))).argmin()  # for testing purpose the noise level is calculated between nyquist and 10 sec
                        # print( "getting power 3", idx)
                        noiselevel = np.mean(asdmar[idx:])
                        # print( "getting power 4", noiselevel)
                        noiselevellist.append(noiselevel)
                    except:
                        failedlist.append(1)
            #print ("NOISELIST", noiselevellist, len(noiselevellist))
            lenbef = len(noiselevellist)
            noiselevellist = drop_outliers(np.asarray(noiselevellist))
            lenaft = len(noiselevellist)
            print ("lenght of NOISELIST before and after dropping outliers:", lenbef, lenaft)
            try:
                nl = np.median(np.asarray(noiselevellist))
                self.logdict['Noiselevel'] = nl
            except:
                pass
            if len(failedlist) > 1:
                self.logdict['Failed noiselevel determinations'] = np.sum(np.asarray(failedlist))
            try:
                nlstd = np.std(np.asarray(noiselevellist))
                self.logdict['NoiselevelStdDeviation'] = np.std(np.asarray(noiselevellist))
            except:
                self.logdict['NoiselevelStdDeviation'] = 0.0

        return nl, nlstd

    def write_report(self, tablelist=None, debug=False):
        """
        DESCRIPTION
            Write a data report with basic information on submitted data set and possible issues
            The report will be written in markup language into the destination directory.
            The name of the report depends on the suggested data level.
            level0.txt (if reading data failed)
            level1*.txt (if reading was successful, but basic information is missing)
            level2*.txt (if reading was successful, and level 2 criteria are met)
        RETURN
            will return the determined level
        """
        if not tablelist:
            tablelist = []
        obscode = self.input.get('obscode')
        year = int(self.input.get('year'))
        monthlist = [datetime(year, month, 10).strftime("%m (%b)") for month in range(1, 13)]
        destinationpath = self.step2folder

        def _merge_dicts(*dict_args):
            """
            Given any number of dictionaries, shallow copy and merge into a new dict,
            precedence goes to key value pairs in latter dictionaries.
            """
            result = {}
            for dictionary in dict_args:
                result.update(dictionary)
            return result

        # check reportdict and obtain main
        levellist = []
        issuelist = []
        improvelist = []
        warninglist = []

        # 1. Extract the monthly dictionaries
        # monthlydict = {}
        generaldict = {}
        definitivedict = {}
        headerdict = {}
        issuesummary = {}
        improvementsummary = {}
        warningsummary = {}

        if debug:
            print("Running write_report")
        for month in monthlist:
            md = self.logdict.get(month)
            if md:
                levellist.append(md.get("Level"))
                issuedict = md.get("Issues", {})
                improvedict = md.get("Improvements", {})
                warningdict = md.get("Warnings", {})
                headerdict = md.get("Header", {})
                if debug:
                    print("Issues", issuedict, improvedict, warningdict)

                for issue in issuedict:
                    validmonths = issuesummary.get(issuedict.get(issue), [])
                    validmonths.append(month)
                    issuesummary[issuedict[issue]] = validmonths
                for improve in improvedict:
                    validmonths = improvementsummary.get(improvedict.get(improve), [])
                    validmonths.append(month)
                    improvementsummary[improvedict[improve]] = validmonths
                for warn in warningdict:
                    validmonths = warningsummary.get(warningdict.get(warn), [])
                    validmonths.append(month)
                    warningsummary[warningdict[warn]] = validmonths
                # Establish a monthly table with all information
                definitivedict[month] = md.get("DefinitiveStatus")
            # get the non-monthly keys
            keys = [key for key in self.logdict if not key in monthlist]
            for key in keys:
                generaldict[key] = self.logdict.get(key)

        if debug:
            print("Levellist", levellist)
        # remove Nones from levellist
        levellist = [el for el in levellist if not el in [None, '']]
        if len(levellist) > 0:
            level = min(levellist)
        else:
            level = 0

        if debug:
            print("   ISSUES", issuesummary)
            print("   IMPROVEMENTS", improvementsummary)
            print("   WARNINGS SUMMARY:", warningsummary)
            # print ("Generaldict", generaldict)

        for issue in issuesummary:
            months = issuesummary[issue]
            if debug:
                print("Lenght", len(months))
            foundat = "every month"
            if not len(months) == 12:
                foundat = ",".join(months)
            issuelist.append("{} | {}\n".format(issue, foundat))

        for improve in improvementsummary:
            months = improvementsummary[improve]
            improvelist.append("{} | {}\n".format(improve, ",".join(months)))

        for warn in warningsummary:
            months = warningsummary[warn]
            warninglist.append("{} | {}\n".format(warn, ",".join(months)))

        text = [
            "# {} - Level {}\n\n# Analysis report for one second data from {} {}\n\n".format(obscode, level, obscode,
                                                                                             year)]
        text.append("### Issues to be clarified for level 2:\n")
        if len(issuelist) > 0:
            text.append("\n")
            text.append("Issue | Observed in months\n")
            text.append("----- | -----\n")
            for issue in issuelist:
                text.append(issue)
        else:
            text.append("\nNone\n")

        text.append("\n### Possible improvements (not obligatory):\n")
        if len(improvelist) > 0:
            text.append("\n")
            text.append("Improvements | Applicable for months\n")
            text.append("----- | -----\n")
            for improve in improvelist:
                text.append(improve)
        else:
            text.append("\nNone\n")

        text.append("\n\n### ImagCDF standard levels as provided by the submitter\n\n")
        text.append("StandardLevel | Description | Validity\n--------- | --------- | ---------\n")
        for element in tablelist:
            text.append("{} | {} | {}\n".format(element[0], element[1], element[2]))

        if len(warninglist) > 0 and level >= 1:
            text.append("\n### Too be considered for final evaluation\n")
            text.append("\n")
            text.append("Considerations for manual checking | Observered \n")
            text.append("----- | -----\n")
            for warn in warninglist:
                text.append(warn)

        text.append("\n\n### Provided Header information\n\n")
        if len(headerdict) > 0:
            text.append("\n")
            text.append("Header | Content\n")
            text.append("----- | -----\n")
            for head in headerdict:
                text.append("{} | {}\n".format(head, str(headerdict[head]).strip()))
        else:
            text.append("\nNone\n")

        text.append("\n\n### Basic analysis information\n\n")
        text.append("* Current one-minute step  :  {}\n".format(self.input.get('minutestep')))

        """
        for key in parameterdict:
            # if not key a dictionary
            if not isinstance(parameterdict[key],dict):
                if not key == "lastmodified":
                    text.append("* {}  :  {}\n".format(key,parameterdict[key]))
                else:
                    try:
                        text.append("* {}  :  {}\n".format(key,datetime.fromtimestamp(float(parameterdict[key]))))
                    except:
                        text.append("* {}  :  {}\n".format(key,parameterdict[key]))
        """

        for key in generaldict:
            # if not key a dictionary
            if not isinstance(generaldict[key], dict):
                if key.startswith('Noiselevel'):
                    text.append("* {}  :  {:.0f} pT\n".format(key, float(generaldict[key]) * 1000.))
                else:
                    text.append("* {}  :  {}\n".format(key, generaldict[key]))
        # TODO: add daylist

        text.append("\n\n### Details on monthly evaluation\n\n")
        #print("Definitive dict", definitivedict)
        for month in monthlist:
            defdi = definitivedict.get(month)
            monthly = self.logdict.get(month)
            text.append("\nMonth {} | Value \n".format(month))
            text.append("------ | ----- \n".format(month))
            try:  # if month is not evaluated as no data has been provided...
                for el in defdi:
                    text.append("{} | {}\n".format(el, defdi[el]))
            except:
                pass
            try:
                for el in monthly:
                    if not isinstance(monthly[el], dict):
                        text.append("{} | {}\n".format(el, str(monthly[el]).strip()))
            except:
                pass

        if debug:
            print(text)

        # delete any previous level description
        def removeFilesByMatchingPattern(dirPath, pattern):
            listOfFilesWithError = []
            for parentDir, dirnames, filenames in os.walk(dirPath):
                for filename in fnmatch.filter(filenames, pattern):
                    try:
                        os.remove(os.path.join(parentDir, filename))
                    except:
                        print("Error while deleting file : ", os.path.join(parentDir, filename))
                        listOfFilesWithError.append(os.path.join(parentDir, filename))
            return listOfFilesWithError

        removeFilesByMatchingPattern(destinationpath, "level*.txt")

        # path might not exist for level0 data
        if not os.path.exists(destinationpath):
            os.makedirs(destinationpath)

        filename = os.path.join(destinationpath, "level{}_underreview.txt".format(level))
        with open(filename, 'w') as out:
            out.write("".join(text))

        # Now also construct an update file for new meta information
        issuesum = {}
        for month in monthlist:
            issuedict = self.logdict.get(month,{}).get("Issues",{})
            issuesum = _merge_dicts(issuesum, issuedict)
        if debug:
            print("issue sum", issuesum)
        if len(issuesum) > 0:
            self._write_meta_update_file(issuesum, debug=debug)

        print("... write_report finished")
        return level


    def _write_meta_update_file(self, dictionary, debug=False):
        """
        DESCRIPTION
            prepare a correction sheet.
            submitters can edit this sheet and update missing information
        """
        if debug:
            print("WRITING correction sheet")

        destinationpath = self.step2folder
        obscode = self.input.get('obscode')
        destination = os.path.join(destinationpath, "meta_{}.txt".format(obscode)),

        def _key_convert(magpykey):
            try:
                key = (list(methods.IMAGCDFKEYDICT.keys())[list(methods.IMAGCDFKEYDICT.values()).index(magpykey)])
                return key
            except:
                return magpykey

        text = ['## Parameter sheet for additional or missing meta information\n',
                '## ------------------------------------------------------\n',
                '## Please provide "key : value" pairs as shown below.\n',
                '## The key need to correspond to the IMAGCDF key. Please\n',
                '## check out the IMAGCDF format description at INTERMAGNET\n',
                '## for details. Alternatively you can use MagPy header keys.\n',
                '## Values must not contain special characters or colons.\n',
                '## Enter "None" to indicate that a value is not available.\n',
                '## Comments need to start in new lines beginning with a\n',
                '## hash.\n',
                '## Please note - you can also provide optional keys here.\n',
                '## \n',
                '## Example:\n',
                '## Providing Partial standard value descriptions as requested:\n',
                '# StandardLevel  :  partial\n',
                '# PartialStandDesc  :  IMOS11,IMOS14,IMOS41\n\n\n']

        headlinedict = {'StandardLevel': '# Provide a valid standard level (full, partial), None is not accepted\n',
                        'PartialStandDesc': '# If Standard Level is partial, provide a list of standards met\n',
                        'ReferenceLinks': '# Reference to your institution (e.g. webaddress)\n',
                        'TermsOfUse': '# Provide Terms of Use (e.g. creative common lisence)\n',
                        'MissingData': '# If data is not available please confirm by MissingData  :  confirmed\n',
                        }

        for key in dictionary:
            if headlinedict.get(key, ''):
                text.append("{}".format(headlinedict[key]))
            text.append("{}  :  {}\n\n".format(_key_convert(key), dictionary[key]))
        try:
            with open(destination, 'w') as outfile:
                outfile.write("".join(text))
        except:
            return False
        return True


    def second_mail_text(self, level, imodict=None, debug=False):
        """
        DESCRIPTION
            creates mail contents for one-second reports
        VARIBALES
            level   : int : the obtained readiness level of final analysis
            dataset : dict : the current dictionary of the modificationlist
            imo_dict : dict : the imo dictionary as obtained by imostatus.get_imo
        RETURN
            a dictionary with subject, text, from, to, attachments
        """
        maildict = {}
        if not imodict:
            imodict = {}
        obscode = self.input.get('obscode')
        resolution = self.input.get('resolution')
        year = int(self.input.get('year'))
        minutestate = self.input.get('minutestep')
        mod = self.input.get('modification')
        stationname = self.logdict.get('Stationname', '')
        admin = self.config.get('sysadmin')
        adminmail = [admin.get(n) for n in admin][0]

        referee = imodict.get('referee')
        contacts = imodict.get('contacts', [])
        imbotmanagers = imodict.get('manager', [])
        destinationpath = self.step2folder

        attachfilelist = glob.glob(os.path.join(destinationpath, "*.txt"))
        receivers = contacts
        nameofreferee = [n for n in referee][0]

        maildict['subject'] = 'IMBOT data check of {} one-{} submission from {}, {}'.format(mod, resolution, obscode,
                                                                                            year)
        maildict['from'] = [adminmail]

        maintext = "Dear data provider,\n\nyou receive the following information as your e-mail address is connected to submissions of geomagnetic data products from {} {} observatory.\nYour one-second data submission from {} has been automatically evaluated by IMBOT, an automatic data checker of INTERMAGNET.\n\nThe evaluation process resulted in\n\n".format(
            stationname, obscode, year)
        maintext += "LEVEL {}\n\n".format(level)
        if minutestate in ['', 'step0', 'step1', 'step2', None]:
            maintext += "!! Please note: this is just a preliminary evaluation result as your obligatory one-minute data product has not yet been finally accepted. "
            if minutestate in ['', 'step0', None]:
                maintext += "Currently there is no one-minute data available. "
            else:
                maintext += "Your one-minute data is currently on {}. ".format(minutestate)
            maintext += "You will receive an update of your evaluation report whenever your one-minute data reaches the next step. If corrections to your one-second product are suggested in the following, please perform those already now in order to speed up the final acceptance process.\n\n"
            time = 'will be'
            last = ' as soon as your one-minute data is finally accepted.'
        else:
            time = 'has been'
            last = ". Your data checker is {}.\nPlease note that INTERMAGNET data checkers perform all check on voluntary basis beside their usual duties. So please be patient. The data checker will contact you if questions arise".format(
                nameofreferee)
            if level > 0:
                receivers.append(referee.get(nameofreferee))
        level0 = "Level 0 means that your data did not pass the automatic reading and conversion test. Please update your data submission.\nOften a level 0 report is connected to corrupted files.\nPlease read the attached report and instructions before re-submission.\n\n"
        level1 = "Level 1 indicates that your data is almost ready for final reviews. In order to continue the evaluation process some issues need to be clarified. Please read the attached report and follow the instructions. In most cases obligatory meta-information is missing. You can easily provide that by filling out and uploading the attached meta_{}.txt file.\n\n".format(
            obscode)
        level2 = "Congratulations! Your data fulfills all requirements of the automatic checking process. A level 2 data product is an excellent source for high resolution magnetic information. Your data set {} assigned to an INTERMAGNET data checker for final decision{}\n\n".format(
            time, last)
        if int(level) == 0:
            maintext += level0
        elif int(level) == 1:
            maintext += level1
        elif int(level) == 2:
            maintext += level2
        maintext += "The attached report makes use of markdown syntax and can be viewed in a formatted way i.e. using https://dillinger.io/. If you have any questions regarding the evaluation process please check out the general instructions (https://github.com/INTERMAGNET/IMBOT/blob/master/README.md - currently only available online for IM definitive data committee) or contact the IMBOT manager and request a pdf.\n\n"
        maintext += "\nSincerely,\n       IMBOT\n\n"

        if int(level) < 2:
            if debug:
                print("Loading instructions and adding them to attachments")
            homedir = os.getenv("HOME")
            path = os.path.abspath(os.path.join(homedir, ".imbot", "templates","second_instructions.txt"))
            attachfilelist.append(path)

            destinationpath = self.step2folder
            obscode = self.input.get('obscode')
            metapath = os.path.join(destinationpath, "meta_{}.txt".format(obscode))
            attachfilelist.append(metapath)

        receivers.extend(imbotmanagers)
        receivers = list(dict.fromkeys(receivers))

        maildict['to'] = receivers
        maildict['text'] = maintext
        maildict['attachment'] = attachfilelist

        return maildict

class TestImbotSecond(unittest.TestCase):

    def test_runtime(self):
        # also tests idf and hdz tools
        print ("testrun requires running steps.py first")
        config = {}
        dataset = {'obscode': 'CNB', 'year': '2022', 'resolution': 'second', 'lastmodified': '2025-02-25T20:17:03', 'step1path': '/home/leon/Tmp/GIN/step1second/2022_step1/CNB', 'modification': 'new', 'temporaryfolder': '/tmp/imbottest/unpacked/2022/second/CNB', 'minutestep': 'step1', 'minutepath': '/home/leon/Tmp/GIN/step1minute/Mag2022/CNB/*.bin'}
        # for dataset in modificationlist:
        secana = second_definitive(input=dataset)
        datelist = secana.get_months()
        datelist = datelist[:1]
        daystreams = []
        for i, dates in enumerate(datelist):
            data, allcontents = secana.read_month(dates, debug=False)
            month = (data.start() + timedelta(days=10)).strftime("%m (%b)")
            secana.delta_f_test(data)
            mtable = secana.check_standard_level(data, partialcheck=methods.partialcheck_v1, debug=False)
            secana.check_diff_to_minute(data, daterange=datelist[0], debug=False)
            daystreams.extend(
                secana.extract_selected_days(data, datelist[0], selecteddays=['2022-01-21', '2022-01-22', '2022-01-23'],
                                             dayformat='text', debug=False))
            secana.export_month(data, allcontents, debug=False)
        # select day checks
        if len(daystreams) > 0:
            secana.psd_analysis(daystreams)
            tablelist = secana.update_table(mtable, month)

        secana.write_report(tablelist=mtable, debug=True)
        #self.assertEqual(res3, '')
        #self.assertEqual('meta_KOU.txt', key_a)
        #self.assertDictEqual({'kou2021.blv': '20231205'}, res4.get('removed'))


if __name__ == "__main__":
    unittest.main(verbosity=2)