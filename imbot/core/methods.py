# -*- coding: utf-8 -*-

"""
methods contain all methods which do not fit to a magpy specific class

|class | method | since version |  runtime test | result verification | manual | *tested by |
|----- | ------ | ------------- |  ------------ | ------------------- | ------ | ---------- |
|**core.methods** |    |        |               |              |  | |
|    | get_conf        |  2.0.0 |  yes          | yes          |        | |
|    | extract_mails   |  2.0.0 |  yes          | yes          |        | |
|    | dictdiff        |  2.0.0 |  yes          | yes          |        | |
|    | read_memory     |  2.0.0 |  yes          | yes          |        | |
|    | write_memory    |  2.0.0 |  yes          | yes          |        | |

"""
import re
import os
import pathlib
import json
from datetime import datetime, timezone

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
    ok = True
    if ok:
        #try:
        config = open(path,'r')
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
            print("Reading memory: {}".format(memorypath))
        with open(memorypath, 'r') as file:
            memdict = json.load(file)
    else:
        print("Memory path not found - please check (first run?)")
    if debug and memdict:
        print("Found in Memory: {}".format([el for el in memdict]))
    return memdict


def write_memory(mydict, path=None, debug=False):
    """
    DESCRIPTION
        save dictionary to json
    """
    if not path:
        return False
    if debug:
        print("imbot_prep: writing memory files to {}".format(path))
    try:
        dirpath = pathlib.Path(path).parent.absolute()
        pathlib.Path(dirpath).mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(mydict, f, ensure_ascii=False, indent=4)
    except:
        print("imbot_prep: writing memory files {} failed".format(path))
        return False
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
