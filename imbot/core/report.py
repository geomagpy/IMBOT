# -*- coding: utf-8 -*-
import sys
sys.path.insert(1,'/home/leon/Software/IMBOT/') # should be magpy2

from imbot.core import methods
from imbot.core import steps
from datetime import datetime, timedelta
import os
import numpy as np
import unittest
import shutil
import collections

import copy
# Remove that
import matplotlib.pyplot as plt

"""
report contain all methods for creating reports, tables and figures
plotting functions are untested

|class | method | since version |  runtime test | result verification | manual | *used by |
|----- | ------ | ------------- |  ------------ | ------------------- | ------ | ---------- |
|**core.report** |     |        |               |                     |  | |
|    | _transform_name  | 2.0.0 |               |                     |        | pie chart |
|    | get_last_updates | 2.0.0 |  yes          | yes                 |        | |
|    | imbot_disk_usage | 2.0.0 |  yes          | yes                 |        | |
|    | noiselevel_plot  | 2.0.0 |               |                     |        | |
|    | observatory_list | 2.0.0 |  yes          | yes                 |        | |
|    | pie_chart        | 2.0.0 |               |                     |        | |
|    | yearly_stats  |    2.0.0 |               |                     |        | |

"""

def _transform_name(name):
    if name.find("INTERMAGNET CDF FORMAT;") > -1:
        name = name.replace("INTERMAGNET CDF FORMAT;","IMAGCDF")
    if name.find("1.X") > -1:
        name = name.replace("1.X","unspecified")
    if name.find("1.3") > -1:
        name = name.replace("1.3","(1.3 -> 1.2.1)")
    return name


def get_last_updates(stats, startyear=1777, defaultrange=5):
    """
    DESCRIPTION
        create a table with latest uploads since startyear
        If no startyear is provided the last 5 years are shown.
        see defaultrange
    APPLICATION:
        tablecont = get_last_updates(stats, startyear=1777)
    """
    if not startyear:
        startyear = (datetime.now()-timedelta(days=defaultrange*365.25)).year
    telmsg = ""
    for year in stats:
        if int(year) >= startyear:
            cont = stats.get(year)
            datum = cont.get('Latest_upload',' ')
            telmsg += "{} | {}\n".format(year, datum)
    return telmsg

def imbot_disk_usage(archive="/srv/imbot", warnlevel=20, critlevel=10, debug=False):
    """
    DESCRIPTION
        analyse disk usage on a imbot server and create reoprts or issue warning
    """
    result = {}
    percm, perca = 100., 100.
    totalm, usedm, freem = shutil.disk_usage("/")
    percm = freem/totalm*100.
    telmsg = "IMBOT | disk-usage\n"
    telmsg += "----- | ----------\n"
    result["/"] = "Free: {}GiB ({:.1f}%)".format((freem // (2**30)), percm)
    if archive and os.path.isdir(archive):
        totala, useda, freea = shutil.disk_usage(archive)
        perca = freea/totala*100.
        result[archive] = "Free: {}GiB ({:.1f}%)".format((freea // (2**30)), perca)
    if perca < 10 or percm < 10:
        result["disk space"] = "CRITICAL !!"
    elif perca < 20 or percm < 20:
        result["disk space"] = "warning"

    for key in result:
        telmsg += "{} | {}\n".format(key, result[key])

    return telmsg


def noiselevel_plot(stats, year=2016, debug=False):
    """
    DESCRIPTION
        Create a noise level distribution plot of one-second submission
    REQUIRES
        yearly_stats
    APPLICATION
        stats = imostatus.yearly_stats(resolution='second')
        result = noiselevel_plot(stats, year=2022)
    """
    noise = stats.get(str(year)).get('NoiseLevel')
    noise = {imo:noise.get(imo) for imo in sorted(noise, key=noise.get)}
    if debug:
        print (noise)
    fig, ax = plt.subplots()
    fig.set_size_inches(12, 4)
    ax.set_yscale('log')
    width = 0.5
    imos = [imo for imo in noise]
    nois = [noise.get(imo) for imo in noise]
    p = ax.bar(imos, nois, width)
    plt.xticks(rotation=90)
    ax.set_title("Average Noiselevel")
    ax.legend(loc="upper right")
    ax.set_ylabel("noiselevel [$nT$/$\sqrt{Hz}$] below 0.1 $Hz$")
    ax.set_xlabel("INTERMAGNET observatory (IMO)")
    return plt


def observatory_list(stats,year=2016, levels=False):
    """
    DESCRIPTION
        Method to get a list of all observatories for a selected year. (ONLY ONE-SECOND)
        It is possible to return levels as well
    REQUIRES
        yearly_stats
    APPLICATION
        stats = imostatus.yearly_stats(resolution='second')
        result = observatory_list(stats, startyear=2016, levels=False)
    """
    l = stats.get(str(year)).get('LevelDetails')
    if levels:
        telmsg = "IMO | Level\n"
        telmsg += "--- | -----\n"
        obslist = collections.OrderedDict(sorted(l.items()))
        for key in obslist:
            telmsg += "{} | {}\n".format(key, obslist[key])

    else:
        obslist = sorted([e for e in l])
        telmsg = ",".join(obslist)

    return telmsg


def pie_chart(stats, year=2016, displaylist=["Level0","Level1","Level2"]):
    """
    DESCRIPTION
        Create a pie chart of contents in stats, depending on the provided displaylist
        # Possible displaylists for second data are
        displaylist = ['INTERMAGNET CDF FORMAT; 1.X','INTERMAGNET CDF FORMAT; 1.2','INTERMAGNET CDF FORMAT; 1.1','IAGA-2002','INTERMAGNET CDF FORMAT; 1.3']
        #displaylist = ["N_step1","N_step2","N_step2accepted","N_step3"]
        #displaylist = ["Level0","Level1","Level2"]
    REQUIRES
        yearly_stats
    APPLICATION
        stats = imostatus.yearly_stats(resolution='second')
        result = pie_chart(stats, year=2022, displaylist='steps')
    """
    fig, ax = plt.subplots()
    counts = []
    disp = []
    cols = []
    colorlist = ['olivedrab','cyan','gray', 'saddlebrown','pink','olive','rosybrown','blue','orange','green','purple','brown']
    for i,step in enumerate(displaylist):
        num = stats.get(str(year)).get(step,0)
        if num:
            counts.append(num)
            step = _transform_name(step)
            disp.append(step)
            cols.append(colorlist[i])
    p = ax.pie(counts, labels=disp, colors=cols)
    ax.set_title(str(year))
    #ax.legend(loc="upper right")
    #plt.show()
    return plt


def yearly_stats(stats, display='level', years='all'):
    """
    DESCRIPTION
        Create a bar chart with yearly statistics on step or level
    REQUIRES
        yearly_stats
    APPLICATION
        stats = imostatus.yearly_stats(resolution='second')
        result = yearly_stats(stats, display='steps', years='all'')
    """
    fig, ax = plt.subplots()
    width = 0.5
    if not years or years in ['all','ALL','All']:
        years = [el for el in stats]
    #years = ['2016','2022']
    if display in ['steps','step']:
        displaylist = ["N_step1","N_step2","N_step2accepted","N_step3"]
    else:
        displaylist = ["Level0","Level1","Level2"]
    bottom = np.zeros(len(years))
    for step in displaylist:
        counts = [stats.get(el).get(step,0) for el in years]
        p = ax.bar(years, counts, width, label=step, bottom=bottom)
        bottom += counts
    ax.set_title("Current status of submitted data")
    ax.legend(loc="upper right")
    return plt


class TestImbotStep(unittest.TestCase):

    def test_getlastupdates(self):
        config = {}
        imostatus = steps.botstatus(config=config)
        stats = imostatus.yearly_stats(resolution='second')
        l = get_last_updates(stats, startyear=1777)
        self.assertTrue(l)

    def test_imbot_disk_usage(self):
        l = imbot_disk_usage(archive=None, warnlevel=20, critlevel=10)
        self.assertTrue(l)

    def test_observatory_list(self):
        config = {}
        imostatus = steps.botstatus(config=config)
        stats = imostatus.yearly_stats(resolution='second')
        l = observatory_list(stats, year=2021, levels=False)
        print (l)
        l = observatory_list(stats, year=2021, levels=True)
        self.assertTrue(l)

if __name__ == "__main__":
    unittest.main(verbosity=2)