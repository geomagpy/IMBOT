# -*- coding: utf-8 -*-

"""
methods contain all methods which do not fit to a magpy specific class

|class | method | since version |  runtime test | result verification | manual | *tested by |
|----- | ------ | ------------- |  ------------ | ------------------- | ------ | ---------- |
|**core.methods** |    |        |               |              |  | |
|    | convert_to_step_dir | 2.0.0 |             |              |        | |
|    | copy_temporary  |  2.0.0 |  yes          | yes          |        | |
|    | dictdiff        |  2.0.0 |  yes          | yes          |        | |
|    | extract_mails   |  2.0.0 |  yes          | yes          |        | |
|    | get_conf        |  2.0.0 |  yes          | yes          |        | |
|    | limit_second_obs | 2.0.0 |  yes          | yes          |        | |
|    | read_memory     |  2.0.0 |  yes          | yes          |        | |
|    | sendmail        |  2.0.0 |               |              |        | |
|    | sendtelegram    |  2.0.0 |               |              |        | |
|    | write_memory    |  2.0.0 |  yes          | yes          |        | |

"""
import re
import os
import pathlib
import json
from datetime import datetime, timezone
import glob
import shutil
import zipfile
import tarfile
import filecmp
import time
import random
from magpy.core.methods import is_number
import configparser  # For Python 3 use the configparser module instead (all lowercase)
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
from magpy.opt import cred as cred



partialcheck_v1 = {
		'IMOS-01' : 'Time-stamp accuracy (centred on the UTC second): 0.01s',
		'IMOS-02' : 'Phase response: Maximum group delay: ±0.01s',
		'IMOS-03' : 'Maximum filter width: 25 seconds',
		'IMOS-04' : 'Instrument amplitude range: ≥±4000nT High Lat., ≥±3000nT Mid/Equatorial Lat.',
		'IMOS-05' : 'Data resolution: 1pT',
		'IMOS-06' : 'Pass band: DC to 0.2Hz',
		'IMOS-11' : 'Noise level: ≤100pT RMS',
		'IMOS-12' : 'Maximum offset error (cumulative error between absolute observations): ±2. 5 nT',
		'IMOS-13' : 'Maximum component scaling plus linearity error: 0.25%',
		'IMOS-14' : 'Maximum component orthogonality error: 2mrad',
		'IMOS-15' : 'Maximum Z-component verticality error: 2mrad',
		'IMOS-21' : 'Noise level: ≤10pT/√Hz at 0.1 Hz',
		'IMOS-22' : 'Maximum gain/attenuation: 3dB',
		'IMOS-31' : 'Minimum attenuation in the stop band (≥ 0.5Hz): 50dB',
		'IMOS-41' : 'Compulsory full-scale scalar magnetometer measurements with a data resolution of 0.01nT at a minimum sample period of 30 seconds',
		'IMOS-42' : 'Compulsory vector magnetometer temperature measurements with a resolution of 0.1°C at a minimum sample period of one minute'
		}

IMAGCDFKEYDICT = {     'FormatDescription':'DataFormat',
                       'IagaCode':'StationID',
                       'ElementsRecorded':'DataComponents',
                       'ObservatoryName':'StationName',
                       'Latitude':'DataAcquisitionLatitude',
                       'Longitude':'DataAcquisitionLongitude',
                       'Institution':'StationInstitution',
                       'VectorSensOrient':'DataSensorOrientation',
                       'TermsOfUse':'DataTerms',
                       'UniqueIdentifier':'DataID',
                       'ParentIdentifiers':'SensorID',
                       'ReferenceLinks':'StationWebInfo',
                       'FlagRulesetType':'FlagRulesetType',
                       'FlagRulesetVersion':'FlagRulesetVersion',
                       'StandardLevel':'DataStandardLevel',
                      }


def _change_subdirectory(maindir):
    subdirs = list(set([os.path.dirname(p) for p in glob.glob(maindir + "/*/*")]))
    if subdirs:
        print ("Found subdirectories after decompression")
        for subd in subdirs:
            #print (subd)
            for zroot, zdirs, zfiles in os.walk(subd):  # repla>
                for zfile in zfiles:
                    print ("Reducing directory level for {} to {}".format(zfile, maindir))
                    path_file = os.path.join(zroot,zfile)
                    shutil.copy2(path_file,maindir)
            shutil.rmtree(subd)


def get_conf(path):
    """
    Version 2020-10-28
    DESCRIPTION:
       can read a text configuration file and extract lists and dictionaries
    SUPPORTED:
       key   :    stringvalue                                 # extracted as { key: str(value) }
       key   :    intvalue                                    # extracted as { key: int(value) }
       key   :    item1,item2,item3                           # extracted as { key: [item1,item2,item3] }
       key   :    subkey1:value1;subkey2:value2               # extracted as { key: {subkey1:value1,subkey2:value2} }
       key   :    subkey1:value1;subkey2:item1,item2,item3    # extracted as { key: {subkey1:value1,subkey2:[item1...]} }
    """
    confdict={}
    with open(path, 'r') as config:
        #try:
        #config = open(path,'r')
        confs = config.readlines()
        for conf in confs:
            conflst = conf.split(':')
            if conf.startswith('#'):
                continue
            elif conf.isspace():
                continue
            elif len(conflst) == 2:
                conflst = conf.split(':')
                key = conflst[0].strip()
                value = conflst[1].strip()
                # Lists
                if value.find(',') > -1:
                    value = value.split(',')
                    value = [el.strip() for el  in value]
                try:
                    confdict[key] = int(value)
                except:
                    confdict[key] = value
            elif len(conflst) > 2:
                # Dictionaries
                if conf.find(';') > -1 or len(conflst) == 3:
                    ele = conf.split(';')
                    main = ele[0].split(':')[0].strip()
                    cont = {}
                    for el in ele:
                        pair = el.split(':')
                        # Lists
                        subvalue = pair[-1].strip()
                        if subvalue.find(',') > -1:
                            subvalue = subvalue.split(',')
                            subvalue = [el.strip() for el  in subvalue]
                        try:
                            cont[pair[-2].strip()] = int(subvalue)
                        except:
                            cont[pair[-2].strip()] = subvalue
                    confdict[main] = cont
                else:
                    print ("Subdictionary expected - but no ; as element divider found")
    #except:
    #    print ("Problems when loading conf data from file. Using defaults")

    return confdict


def extract_emails(path):
    """
    DESCRIPTION
        read text file in path and extract all e-mail addresses in this file
    APPLICATION
        apply on readme.obscode to get e-mails from observers to send report to
    RETURNS
        a list with mail addresses
    """
    mailaddresslist = []

    regex = re.compile(("([a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`"
                        "{|}~-]+)*(@)(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(\.|"
                        "\sdot\s))+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)"))

    try:
        fulltext = ''
        if os.path.isfile(path):
            with open(path, 'r', encoding="latin-1") as infile:
                fulltext = infile.read().lower()

        mailaddresslist = [email[0] for email in re.findall(regex, fulltext) if not email[0].startswith('//')]
    except:
        print(" -> Could not extract mails from {} - permission problem?".format(path))

    return mailaddresslist


def dictdiff(dict_a, dict_b, show_value_diff=True):
    """
    DESCRIPTION
        Compares two dictionaries. Useful for header analysis.
        Code was taken as is from
        https://stackoverflow.com/questions/32815640/how-to-get-the-difference-between-two-dictionaries-in-python
        and written by juandesant.
    """
    result = {}
    result['added']   = {k: dict_b[k] for k in set(dict_b) - set(dict_a)}
    result['removed'] = {k: dict_a[k] for k in set(dict_a) - set(dict_b)}
    if show_value_diff:
        common_keys =  set(dict_a) & set(dict_b)
        result['value_diffs'] = {
            k:(dict_a[k], dict_b[k])
            for k in common_keys
            if dict_a[k] != dict_b[k]
        }
    return result


def read_memory(memorypath, debug=False):
    """
    DESCRIPTION
         read memory
    """
    memdict = {}
    if memorypath and os.path.isfile(memorypath):
        if debug:
            print(" reading memory: {}".format(memorypath))
        with open(memorypath, 'r') as file:
            memdict = json.load(file)
    else:
        print(" memory path not found - please check (first run?)")
    if debug and memdict:
        print(" found in Memory: {}".format([el for el in memdict]))
    return memdict


def write_memory(mydict, path=None, debug=False):
    """
    DESCRIPTION
        save dictionary to json
    """
    if not path:
        return False
    if debug:
        print(" writing memory files to {}".format(path))
    try:
        dirpath = pathlib.Path(path).parent.absolute()
        pathlib.Path(dirpath).mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(mydict, f, ensure_ascii=False, indent=4)
    except:
        print(" writing memory files {} failed".format(path))
        return False
    return True


def convert_to_step_dir(sourcepath, destinationpath, destlevel1_prefix='mag', debug=False):
    """
    DESCRIPTION:
        reads a directory structure in identifies recusively all IAF files. copies the files into a structure similar
        as to be found on step1 and step2 directories. mag2020 -> IMO -> files
    VARIABLES:
        sourcepath : string : the base path of the i.e. my/path/step3raw
        destination : string : the base path of the new directory i.e. my/path/step3
    APPLICATION
        apply this method directly after downloading minute step3 raw data
    """
    existcounter = 0
    copycounter = 0
    if not os.path.isdir(destinationpath):
        print ("Destinationdirectory need to exist")
        return False
    for root, dirs, files in os.walk(sourcepath):
        #level = root.replace(sourcepath, '').count(os.sep)
        for file in files:
            if (file.endswith('.zip') or file.endswith('.bin') or file.endswith('.BIN')):
                filename = os.path.basename(file).split(".")[0]
                if len(filename) == 8:
                    y = filename[3:5]
                    if is_number(y):
                        # Found a IAF file
                        y = int(y)
                        obscode = filename[:3].upper()
                        if y < 70:
                            year = y+2000
                        else:
                            year = y+1900
                        src = os.path.join(root,file)
                        dst = os.path.join(destinationpath, "{}{}".format(destlevel1_prefix,year), obscode, file)
                        if not os.path.exists(os.path.dirname(dst)):
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                        if debug:
                            print ("Would copy file {} to destination {}".format(src, dst))
                        else:
                            if not os.path.exists(dst) or not filecmp.cmp(src, dst):
                                shutil.copyfile(src, dst)
                                copycounter += 1
                                if debug:
                                    print ("Copying new file to {}".format(dst))
                            else:
                                existcounter += 1
                                if debug:
                                    print ("file {} existing")
    print (" convert_to_step_directory structure: copied {} files and ignored {} existing, unchanged data sets".format(copycounter, existcounter))
    return True


def copy_temporary(modificationlist, tmpdir="/tmp/imbottest", debug=False):
    """
    DESCRIPTION:
        copy files to temporary directory
        zipped files and tar archives will be extracted
    VARIABLES:
        modifictaionlist :
          [{'obscode': 'KOU', 'year': '2021', 'resolution': 'minute', 'step1path': '/tmp/imbottest/step1/Mag2021/KOU',
          'modification': 'updated'}, {'obscode': 'CNB', 'year': '2022', 'resolution': 'minute',
          'step1path': '/home/leon/Tmp/GIN/step1minute/Mag2022/CNB', 'modification': 'new'}]
    RETURN:
        A new version of modificationlist only with new/update flags and with temporary directories added
    """
    newmodificationlist = []

    for obsdict in modificationlist:
        obscode = obsdict.get('obscode')
        year = obsdict.get('year')
        path = obsdict.get('step1path')
        resolution = obsdict.get('resolution')
        modification = obsdict.get('modification')
        if modification in ['new', 'updated']:
            # Copy only new or updated data sets to temporary folder
            condict = {}
            newdir = os.path.join(tmpdir, 'unpacked', year, resolution, obscode)
            if not os.path.exists(newdir):
                os.makedirs(newdir)

            print("Copying {} data from {},{} to temporary folder {}".format(resolution, obscode, year, newdir))
            for fname in os.listdir(path):
                src = os.path.join(path, fname)
                dst = os.path.join(newdir, fname)
                if fname.endswith('.zip') or fname.endswith('.ZIP'):
                    if not fname.endswith("cln.zip"):
                        try:
                            with zipfile.ZipFile(src, 'r') as zip_ref:
                                zip_ref.extractall(newdir)
                            if debug:
                                print("  unzipped {}".format(fname))
                        except:
                            if debug:
                                print("  ZIP file problem - trying 7z")
                            try:
                                unzip = "7z x {} -y -o{}".format(src, newdir)
                                if debug:
                                    print("  Running: {}".format(unzip))
                                os.system(unzip)
                                if debug:
                                    print("  unzipped {}".format(fname))
                            except:
                                print("  significant ZIP file problem")
                                # Create error message
                                # newdir remains empty
                                break
                        _change_subdirectory(newdir)
                elif fname.endswith(".tar.gz") or fname.endswith(".TAR.GZ") or fname.endswith(
                        ".tgz") or fname.endswith(".TGZ"):
                    with tarfile.open(src, "r:gz") as tar:
                        tar.extractall(newdir)
                    if debug:
                        print("  unzipped and tar extracted")
                elif fname.endswith(".tar") or fname.endswith(".TAR"):
                    with tarfile.open(src, "r:") as tar:
                        tar.extractall(newdir)
                    if debug:
                        print("  tar extracted")
                else:
                    # print (" -> copying individual files...")
                    if not os.path.isdir(src):
                        # eventually use a filter method here like "if not fname in []"
                        # try:
                        ok = True
                        if ok:
                            # print (" -> source is not directory - OK ...")
                            if not os.path.exists(dst):
                                if debug:
                                    print("   -> copying new file ...")
                                try:
                                    shutil.copyfile(src, dst)
                                except:
                                    # for some unkown reason Jan.bin files sometimes cannot be cópied
                                    # not reproducible... i have no idea why ... workaround below
                                    if debug:
                                        print(" -> failed ... retrying")
                                    for i in range(10):
                                        time.sleep(5)
                                        try:
                                            shutil.copyfile(src, dst)
                                        except:
                                            if debug:
                                                print("Retry {} of {} failed".format(i + 1, 10))
                                if debug:
                                    print("file {} copied".format(fname))
                            elif not filecmp.cmp(src, dst):
                                if debug:
                                    print("   -> replacing existing temporary file ...")
                                shutil.copyfile(src, dst)
                                if debug:
                                    print("file {} copied".format(fname))
                            else:
                                if debug:
                                    print("   -> identical file already exists ...")
                        # except:
                        #    print (" -> Failed ...")
                        #    condict[fname] = "copying file failed"
            print(" -> Done ...")

            obsdict['temporaryfolder'] = newdir
            newmodificationlist.append(obsdict)

    return newmodificationlist


def limit_second_obs(modlist, limit=3, debug=False):
    """
    DESCRIPTION
        method to reduce the number of treated observatories
        to a given limit. This is helpful to get rid of memory and duration
        issues if too many data has been uploaded a the same time. Only
        a limited amount is treated and the rest is dealed with during a
        future run
        Limit_obs will also randomly change the order of dicts in modlist.
        If a single obs is prodicing a critical system error, other data is analyzed.
    TEST
        provide a dummy dict and dummy notification
        and then run unittest
    APPLICATION
        modlist = limit_obs(modlist, limit=3, debug=True)
    """
    #limited obslist
    newmodlist = []
    secondlist = []
    for obsdict in modlist:
        resolution = obsdict.get('resolution')
        if resolution == 'second':
            secondlist.append(obsdict)
        else:
            newmodlist.append(obsdict)
    if len(secondlist) > 1:
        random.shuffle(secondlist)
    if len(secondlist) > limit:
        orglength = len(secondlist)
        if debug:
            print("limit_second_obs: dropping the following item(s) for this analysis: {}".format(secondlist[limit:]))
        secondlist = secondlist[:limit]
        print ("limit_second_obs: Reduced the amount of second data for current analysis from {} to {}".format(orglength, limit))
    else:
        if debug:
            print("limit_second_obs: Nothing to be done")
    newmodlist.extend(secondlist)
    return newmodlist


def sendmail(dic, credentials="webmail", debug=False):
    """
    DESCRIPTION
        Mailing function for sending contents of a mailing dictionary with attachments
    DEPENDENCIES
        requires the magpy credential module to obsfucate credential information on mail server.
        You can insert new credentials either with "addcred" after installation of MagPy or use:
        from magpy.opt import cred as cred
        cred.cc('mail','webmail', user='user@web.xx', passwd="secret", smtp='smtp.provider.xx', port='587')
    VARIABLES
        dic : dict with 'subject', 'from', 'to', 'text', 'attachment'
    """

    #if not smtpserver:
    #    smtpserver = 'smtp.web.de'
    if 'attachment' in dic and isinstance(dic.get('attachment',[]), (list,tuple)):
        files = dic.get('attachment',[])
    else:
        files = []
    text = dic.get('text','Cheers, Your Analysis-Robot')
    subject = dic.get('subject','Automatic message')

    smtpserver = cred.lc(credentials,'smtp')
    user = cred.lc(credentials,'user')
    pwd = cred.lc(credentials,'passwd')
    port = cred.lc(credentials,'port')
    if port:
        port = int(port)

    msg = MIMEMultipart()
    msg['From'] = user #dic.get('from')
    send_to = ', '.join(dic.get('to'))
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach( MIMEText(text) )

    # TODO log if file does not exist
    for f in files:
        if not os.path.isfile(f):
            print ("File {} not existing".format(f))
        else:
            part = MIMEBase('application', "octet-stream")
            part.set_payload( open(f,"rb").read() )
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
            msg.attach(part)

    # seems as if server name needs to be specified in py3.7 and 3.8, should work in older versions as well
    if port in [465]:
        smtp = smtplib.SMTP_SSL(smtpserver)
    else:
        smtp = smtplib.SMTP(smtpserver)
    smtp.set_debuglevel(False)
    if port:
        smtp.connect(smtpserver, port)
    else:
        smtp.connect(smtpserver)
    smtp.ehlo()
    if port in [587]:
        if debug:
            print ("Using tls")
        smtp.starttls()
    smtp.ehlo()
    if user and not user in ['None','False']:
        smtp.login(user, pwd)
    smtp.sendmail(user, send_to, msg.as_string())
    smtp.close()


def sendtelegram(message, configpath="", debug=True):
    """
    DESCRIPTION
        Sending a telegram message provided that token and chat_id are provided
        Requires configuartion data read by configparser of the following form:

    VARIABLES
        message : string
        configpath  :
    """

    print ("Running telegram send:", configpath, message)
    if not message or not configpath or not os.path.isfile(configpath):
        return False
    # telegram notifications - replace and cut
    rep = message.replace('&', 'and').replace('/', '')[:4000]
    print("Sending by telegram:", rep)
    # Send report to the specific user i.e. by telegram
    config = configparser.ConfigParser()
    config.read(configpath)
    token = config.get('telegram', 'token')
    chat_id = config.get('telegram', 'chat_id')
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={rep}"
    print(requests.get(url).json())  # this sends the message
    return True


if __name__ == '__main__':

    print()
    print("----------------------------------------------------------")
    print("TESTING: Methods PACKAGE")
    print("THIS IS A TEST RUN OF THE IMBOT.CORE METHODS PACKAGE.")
    print("All main methods will be tested. This may take a while.")
    print("If errors are encountered they will be listed at the end.")
    print("Otherwise True will be returned")
    print("----------------------------------------------------------")
    print()
    # tested elswhere:
    # - func_to_file and func_from_file in stream together with functiontools
    testlist1 = [
        {'obscode': 'KOU', 'year': '2021', 'resolution': 'minute', 'step1path': '/tmp/imbottest/step1/Mag2021/KOU',
         'modification': 'updated', 'temporaryfolder': '/tmp/imbottest/unpacked/2021/minute/KOU'},
        {'obscode': 'CNB', 'year': '2022', 'resolution': 'minute',
         'step1path': '/home/leon/Tmp/GIN/step1minute/Mag2022/CNB', 'modification': 'new',
         'temporaryfolder': '/tmp/imbottest/unpacked/2022/minute/CNB'},
        {'obscode': 'ZYX', 'year': '2022', 'resolution': 'second'},
        {'obscode': 'CNB', 'year': '2022', 'resolution': 'second'},
        {'obscode': 'XYZ', 'year': '2022', 'resolution': 'second'},
        {'obscode': 'BBA', 'year': '2022', 'resolution': 'second'},
        {'obscode': 'ABB', 'year': '2022', 'resolution': 'second'}]
    testlist2 = [
        {'obscode': 'KOU', 'year': '2021', 'resolution': 'minute', 'step1path': '/tmp/imbottest/step1/Mag2021/KOU',
         'modification': 'updated', 'temporaryfolder': '/tmp/imbottest/unpacked/2021/minute/KOU'},
        {'obscode': 'CNB', 'year': '2022', 'resolution': 'minute',
         'step1path': '/home/leon/Tmp/GIN/step1minute/Mag2022/CNB', 'modification': 'new',
         'temporaryfolder': '/tmp/imbottest/unpacked/2022/minute/CNB'},
        {'obscode': 'ZYX', 'year': '2022', 'resolution': 'second'},
        {'obscode': 'CNB', 'year': '2022', 'resolution': 'second'}]

    errors = {}
    try:
        da = {0:"a",1:"b",2:"c"}
        db = {0:"a",1:"b",2:"d"}
        res = dictdiff(da, db, show_value_diff=True)
    except Exception as excep:
        errors['dictdiff'] = str(excep)
        print(datetime.now(timezone.utc).replace(tzinfo=None), "--- ERROR dictdiff.")
    try:
        test = get_conf("../../config/imbot.cfg")
        #check test
        print (test)
    except Exception as excep:
        errors['get_conf'] = str(excep)
        print(datetime.now(timezone.utc).replace(tzinfo=None), "--- ERROR get_conf.")
    try:
        test = extract_emails("../../config/imbot.cfg")
        #check test
        print (test)
    except Exception as excep:
        errors['extract_emails'] = str(excep)
        print(datetime.now(timezone.utc).replace(tzinfo=None), "--- ERROR extract_emails.")
    try:
        da = {"0":"a","1":"b","2":"c"}
        write_memory(da, path="/tmp/test_delete.json")
        db = read_memory("/tmp/test_delete.json")
        print (dictdiff(da, db))
    except Exception as excep:
        errors['read_write'] = str(excep)
        print(datetime.now(timezone.utc).replace(tzinfo=None), "--- ERROR read_write.")
    try:
        modlist = [{'obscode': 'KOU', 'year': '2021', 'resolution': 'minute', 'step1path': '/tmp/imbottest/step1/Mag2021/KOU', 'modification': 'updated'}]
        modificationlist = copy_temporary(modlist, debug=False)
        print (modificationlist) # should contain an input with temporaryfolder
    except Exception as excep:
        errors['copy_temporary'] = str(excep)
        print(datetime.now(timezone.utc).replace(tzinfo=None), "--- ERROR copy_temporary.")
    try:
        modificationlist = limit_second_obs(testlist1, limit=3, debug=True)
        modificationlist = limit_second_obs(testlist2, limit=3, debug=True)
    except Exception as excep:
        errors['limit_second_obs'] = str(excep)
        print(datetime.now(timezone.utc).replace(tzinfo=None), "--- ERROR limit_second_obs.")

    print()
    print("----------------------------------------------------------")
    if errors == {}:
        print("0 errors! Great! :)")
    else:
        print(len(errors), "errors were found in the following functions:")
        print(str(errors.keys()))
        print()
        print("Exceptions thrown:")
        for item in errors:
            print("{} : errormessage = {}".format(item, errors.get(item)))
