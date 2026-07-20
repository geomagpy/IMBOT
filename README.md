# IMBOT - an automatic data reviewing system for INTERMAGNET

The INTERMAGNET ROBOT (short IMBOT) has been developed to provide
some general initial automatic routines to convert and evaluate INTERMAGNET (IM) data submissions. The primary aims of
IMBOT are to (1) simplify one-second and one-minute data submissions for data providers, (2) to speed up the evaluation
process significantly, (3) to consider current IM archive formats and meta information (e.g. on leap seconds), (4) to
simplify and speed up the peer-review process and finally (5) to reduce the workload of human data checkers. Detailed
reports are automatically produced and send out along with templates for corrections to the submitting institute.
Notification of data providers and human referees is also performed by IMBOT and any re-evaluation is triggered 
automatically when updating data or any information in the submission directory. This automated 
system makes data review faster and more reliable, providing high-quality data for the geomagnetic community.

Full documentation: https://egusphere.copernicus.org/preprints/2025/egusphere-2025-2553

## Installation instructions

### Required software

IMBOT is a python project specifically developed and tested in debian like Linux environments. The recommended setup
was tested on Ubuntu 22.04 but will work in future versions provided the underlying packages are still available.
Before installing and using imbot as described in this manuscript you need to install the following additional
packages:

       sudo apt-get install wget curlftpfs p7zip-full p7zip-rar wine python3-virtualenv

These packages are used to access data sources, unpack compressed data and make use of the well established 
check1min routine for one-minute data checking. Then create a separate python environment for imbot.

       virtualenv ~/env/imbot 

Active the new environment:

       source ~/env/imbot/bin/activate

Install MagPy which provides the libraries for file recognition and some analysis tools

       pip install geomagpy

Finally download and install imbot. The installation process will create a .imbot directory in your home folder 
containing a  number of templates and skeletons for configuration files.

       pip install imbot-2.0.0.tar.gz


On a new system and ONLY there run initialization script to create configuration scripts and templates 

       imbot_init 

### Configuration

#### configuring wine for check1min analysis

Copy check1min.exe to your homedirectory. Then do an initial test run with wine. Please note: wine requires X86 and
check1min will run only in win32.

       $ wine check1min.exe

The above command will create a .wine folder in your home directory. After ending the
test run move the check1min program to /home/USER/.wine/drive_c/

       $ mv check1min.exe /home/USER/.wine/drive_c/

Create a data directory under drive_c:

       $ cd /home/USER/.wine/drive_c/
       $ mkdir data

Update imbot.cfg. Modify the inputs for "winepath" with /home/USER/.wine/drive_c/.

#### configuring imbot

go to ~/.imbot and copy the following files to the main directory if not there

1) download_min.sh: edit to download one-minute data from GIN
2) download_min.sh: edit to download one-second data from GIN
3) ginsource.sh: edit for GIN credentials
4) scan.sh: edit to run scan and analysis job
4) report.sh: edit to run regular reporting jobs

modify/edit the following files:

1) conf/imbot.cfg
2) conf/refereelist_minute.cfg
3) conf/refereelist_second.cfg
4) conf/mailinglist.cfg

#### defining referee and observatory mailing lists

Mailing addresses for IMOs are obtained in the following order:

1. conf/mailinglist.cfg
2. memory/memory_email.json (addresses extracted earlier from READMEs)
3. mail addresses extracted from the one-minute submissions (readme file)

Mailing addresses extracted from the one-minute submissions are also stored locally in a json file called 
memory/memory_emails.json. This is important as step3 one-minute data has no readme files any more.  

Fallback addresses, i.e. data checker if observatory has not yet been assigned to a specific data checker, the 
address of the system administrator and imbots mailingaddress are part of the general configuration file.

#### configuring MARTAS applications

1) monitor: monitor disk space and scan file logs
2) backup: add ~/.imbot to the backup routine
3) activate cleanup to clear temporary directory without restart

#### schedule the imbot jobs in crontab

1) download_min
2) download_sec

3) scan 
    scan and analysis
4) report
    imbot_report -c config -j disk,last 

### imbot2.0 general workflow

Scheduled jobs in the following order:

1. download/sync data sources to local harddrive
   - scheduled jon of download_min and download_sec which are both making use of wget
   - step1, step2 minute; step1 second are copied to the harddisk
   - step3 minute plus conversion
   - step2 second requires an rsync process as new data is uploaded and referee reports are downloaded
   - TODO monitor these jobs
2. imbot_scan.py is called to update local memory based on download folders
   - creates a local memory file with all step and analysis information for all data sets
   - require a backup of the memory (weekly) - using MARTAS
   - monitor using MARTAS
3. analysis.py is called to extract modified data from memory and run min/sec analysis
   - run the jobs and create mails
   - send mails to receivers
   - create reports and send via messenger and mail
   - monitor successful completion of analysis
 

##  examples for a meta_OBSCODE.txt

In order to update meta information for your data submission you rename, fill out and upload the information in the
meta template file to step1. The filename needs to be like "meta_XXX.txt" if your imo code is "XXX".

The default template:

```sh
# Parameter sheet for additional/missing metainformation
## ------------------------------------------------------
## Please provide key - value pairs as shown below.
## The key need to correspond to the IMAGCDF key. Please
## check out the IMAGCDF format description at INTERMAGNET
## for details. Alternatively you can use MagPy header keys.
## Values must not contain special characters or colons.
## Enter "None" to indicate that a value is not available
## Comments need to start in new lines and every comment line.
## must start with a hash.
## Please note - you can also provide optional keys here.
## 
## Example:
## Providing Partial standard value descriptions as requested:
# StandardLevel  :  partial
# PartialStandDesc  :  IMOS11,IMOS14,IMOS41


# Provide a valid standard level (full, partial), None is not accepted
#StandardLevel  :  partial

# If Standard Level is partial, provide a list of standards met
#PartialStandDesc  :  IMOS-01,IMOS-02,IMOS-03,IMOS-04,IMOS-05,IMOS-11,IMOS-14,IMOS-41

# If data is not available please confirm by MissingData  :  confirmed
#MissingData  :  confirmed
```

Providing/updating information on standard levels (see [INTERMAGNET technical manual](https://tech-man.intermagnet.org/stable/appendices/dataformats.html#imagcdf-intermagnet-exchange-format)):

```sh
## Parameter sheet for additional/missing metainformation
## ------------------------------------------------------

# Provide a valid standard level (full, partial), None is not accepted
StandardLevel  :  partial

# If Standard Level is partial, provide a list of standards met
PartialStandDesc  :  IMOS-01,IMOS-02,IMOS-03,IMOS-04,IMOS-05,IMOS-11,IMOS-14,IMOS-41
```

More then one month of data is missing, and add Terms of use:

```sh
## Parameter sheet for additional/missing metainformation
## ------------------------------------------------------

# Missing data treatment (if data is not available please uncomment)
MissingData  :  confirmed

TermsOfUse   :  CC-BY4.0
```

IMBOT is ready for a number of future challenges. It can treat data which includes flagging information. IMBOT
one-minute is already capable of reading and analyzing other $D_{min}$ formats i.e. like a yearly IMAGCDF one-minute 
data file (IMO\_2016\_PT1M.cdf). At the current state only basic read tests, verifying correct data formats and general 
readability are performed. This one-minute test module can, however, be extended for more intense data checking similar 
to check1min. Although IMBOT has been created for definitive $D_{sec}$ it can also be modified and used for other data 
sets as well. A possible application would be high resolution variation data which could be quickly checked with such
routine and provided as a tested data product by INTERMAGNET basically on the fly. Further data sources might also be 
included \added[id=ref2]{, as long as the data formats are supported by MagPy \citep{Leonhardt2025} which is used a 
format interpreter for IMBOT. As the main developer of MagPy is involved in IMBOT and also in the INTERMAGNET definitive
data committee, any format changes are quickly included.} IMBOT is written completely modular. Each checking technique 
is described and coded in an individual module. Thus, IMBOT can be simply extended or modified towards other tests and 
data sets  \added[id=ref2]{and its methods might be applied to completely different projects. The IMBOT repository with
all modules and methods is available on GitHUB under MIT licence (https://github.com/geomagpy/IMBOT). It is possible
to fork this repository and adapt it to other data sources. The repository is actively maintained by the authors. 
Updates are only included upon request by the INTERMAGNET definitive data committee, which meets at least once per year.
A quick and easy way for reporting problems makes use of the GitHUB issues, so that the authors are automatically 
informed. When adapting this project on other data sets you have to consider that all data quality testing routines have
been developed for geomagnetic data. As long as the underlying data formats are supported by MagPy, the effort to adapt 
the tools for your data set is relatively small.} 
