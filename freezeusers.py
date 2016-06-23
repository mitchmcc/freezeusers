#---------------------------------------------------------------------------------------------------------
#
#   Module: freezeusers.py
#
#   Author: Mitchell McConnell
#
#---------------------------------------------------------------------------------------------------------
#
#  Date     Who         Description
#
# 06/22/16  mjm         Original version
#
#---------------------------------------------------------------------------------------------------------

import sys
import os
import string
import datetime 
import getopt
import csv
import pdb
import requests
from datetime import datetime
import time
from datetime import timedelta
from time import gmtime, strftime
#import logging
from simple_salesforce import Salesforce
from simple_salesforce import SalesforceLogin
requests.packages.urllib3.disable_warnings() # this squashes insecure SSL warnings

debug = False
verbose = False
version = "00.00.02"
testLogin = False
orgType = 'test'
filename = 'freezeusers.csv'
whereClause = None

# This is the destination directory for the export files

filePath = os.path.normpath("C:/")

outputFile = ''

#---------------------------------------------------------------------------------------------------------
#
#   Function: usage
#
#---------------------------------------------------------------------------------------------------------
def usage():
  global version

  print("sfloader Version ",version)
  
  print("Usage:")
  print("  -p  [Salesforce Password]")
  print("  -t  [Salesforce Security Token]")
  print("  -d  Enable debug")
  print("  -o  [org type] 'test' or 'login', default = 'test']")
  print("  -l  Test login and exit")
  print("  -w  Profile(s) to append to WHERE clause for Profiles to exclude from freezing, default = 'System Admnistrator'")
  print("   E.g. -w \"System Administrator\" -w Support -w \"Integration User\"")
  print("  -f  CSV file name")
  print("  -P  Output file path (default: C:\)")
  print("  -v  Enable verbose")
  print("  -h  logging.info(this help message")

#---------------------------------------------------------------------------------------------------------
#
#   Module: main
#
#---------------------------------------------------------------------------------------------------------

login = 'username'
passwd = 'password'
token = 'token'
starttime = datetime.now()
begin_time = time.time()

print "freezeusers version ",version," starting up at ",starttime.strftime("%Y-%m-%d %H:%M:%S")

# process command-line options

try:
    opts, args = getopt.getopt(sys.argv[1:], "u:p:t:o:P:w:f:ldvh", ["help", "output="])
except getopt.GetoptError, err:
    usage()
    sys.exit(0)

for o, a in opts:
    if o == "-u":
        login = a
        if debug:
            print("Got SF username from command line: " + login)
    elif o == "-p":
        passwd = a
        if debug:
            print("Got SF passwd from command line: " + passwd)
    elif o == "-t":
        token = a
        if debug:
            print("Got SF security token from command line: " + token)
    elif o == "-f":
        filename = a
        if debug:
          print("Got output file name from command line: " + filename)
    elif o == "-w":
        if whereClause == None:
          whereClause = a + ','
        else:
          whereClause += a + ','

        if debug:
          print("Got whereClause from command line: " + whereClause)
    elif o == "-o":
        orgType = a
        if debug:
            print("Got org type from command line: " + orgType)
    elif o == "-P":
        filePath = a
        if debug:
            print("Got filePath from command line: " + filePath)
    elif o == "-d":
        debug = True
        if debug:
            print("Set debug from command line")
    elif o == "-l":
        testLogin = True
        if debug:
            print("Set testLogin from command line")
    elif o == "-v":
        verbose = True
        if debug:
            print("Set verbose from command line")
    elif o == "-h":
        usage()
        sys.exit(0)
    else:
        print("ERROR: unhandled option: ",o)
        usage()
        sys.exit(1)

# Fix up where clause if any Profiles were entered
# Strip off extra commas, and then iterate over and put on single quotes

if whereClause == None:
  whereClause = "where Name = 'System Administrator'"
else:
  tempWhere = whereClause.rstrip(',')

  whereClause = "where Name in ("

  parts = tempWhere.split(',')

  for p in parts:

    whereClause += "'" + p + "'" + ","

  whereClause = whereClause.rstrip(',')

  whereClause += ")"

  if debug:
    print "final whereClause: ",whereClause

#sys.exit(1)

# do some sanity checking on inputs

if (orgType != 'login') and (orgType != 'test'):
    print "ERROR: invalid org type: ",orgType
    print "   Valid values are: 'login' and 'test'"
    sys.exit(2)

outputFile = filePath + "/" + filename

if debug:
  print "filename: ",filename,", filepath: ",filePath,", outputFile: ",outputFile

# NOTE: for anyone who wants to use the logging package
# set up logging the way we want it
##if debug:
##  logging.basicConfig(format='%(asctime)s : %(levelname)s - %(message)s',level=logging.DEBUG)
##elif verbose:
##  logging.basicConfig(format='%(asctime)s : %(levelname)s - %(message)s',level=logging.INFO)
##else:
##  logging.basicConfig(format='%(asctime)s : %(levelname)s - %(message)s',level=logging.WARN)
##
##logging.info("bmxpush version %s starting up\n",version)

# setup our salesforce connection to get instance

sessId, instanceUrl = SalesforceLogin(username=login,
                password=passwd,
                security_token=token,
                sandbox= (True if orgType == 'test' else False))

instanceParts = instanceUrl.split('.')
instance = instanceParts[0]

if testLogin:
  print "Logged in successfully, instanceUrl: ",instanceUrl,", instance: ",instance
  sys.exit(0)

# Now setup our salesforce connection

sf = Salesforce(username=login,
                password=passwd,
                security_token=token,
                sandbox= (True if orgType == 'test' else False))

thistime = datetime.now()

# This is a dictionary of all active users, where the User Id is the key, and the returned map of the SELECT values is the data
userMap = {}
# This is a dictionary of the Profiles that are not to be frozen, where the Profile Id is the key, and the Profile Name is the data
profileMap = {}
# This is a dictionary where the User ID is the key and the UserLogin Id is the data
loginMap = {}

userQuery = "select Id, Name, ProfileId, IsActive FROM user where IsActive = true"

if debug:
  print userQuery

if verbose:
  print "Querying for active users"

userResult = sf.query(userQuery)

userRset = userResult["records"]

for rec in userRset:
  userId = rec["Id"]
  userProfileId = rec["ProfileId"]

  userMap[userId] = userProfileId

  if debug:
    print userId,",",userProfileId,", isActive: ",rec["IsActive"]

#print userMap

if whereClause == '':
  profileQuery = "select Id, Name FROM profile where Name in ('System Administrator')"
else:  
  profileQuery = "select Id, Name FROM profile " + whereClause

if debug:
  print profileQuery
#pdb.set_trace()

if verbose:
  print "Getting Profiles to skip, WHERE clause: ",whereClause

profileResult = sf.query(profileQuery)

profileRset = profileResult["records"]

for rec in profileRset:
  profileId = rec["Id"]
  profileMap[profileId] = rec["Name"]

  if debug:
    print profileId,",",profileId,", Name: ",profileMap[profileId]

#print profileMap

finalList = ()

loginQuery = "select Id, UserId, IsFrozen FROM UserLogin"

if debug:
  print loginQuery

#pdb.set_trace()

if verbose:
  print "Getting UserLogin records"

loginResult = sf.query(loginQuery)

loginRset = loginResult["records"]

if debug:
  print "UserLoginId,UserId"

for rec in loginRset:
  loginId = rec["Id"]
  userId = rec["UserId"]

  loginMap[userId] = loginId

  if debug:
    print userId,",",loginId

# now build the csv file

#print "\n-------------------------------------------------------------------------\n"
#print "CSV values"

if verbose:
  print "\n"
  print "Total Active Users:      ",len(userMap)
  print "Total Profiles excluded: ",len(profileMap)
  print "Total UserLogin entries: ",len(loginMap)

totalToFreeze = 0
totalSkippedInactive = 0
totalExcludedProfile = 0

#pdb.set_trace()

with open(outputFile, 'wb') as f:
  w = csv.writer(f, quoting=csv.QUOTE_ALL)

  # write the csv header

  f.write('ID,USERID,ISFROZEN')
  f.write('\n')
            
  for key, value in loginMap.iteritems():
    #pdb.set_trace()

    if debug:
      print "key: ",key,", value: ",value

    # just in case, make sure this User Id is in our active users list

    if key in userMap:

      # now, get the users profile ID, which is the data part of the dictionary

      thisUserProfileId = userMap[key]

      if debug:
        print "thisUserProfileId: ",thisUserProfileId

      if not thisUserProfileId in profileMap:
        totalToFreeze += 1

        rowData = value,key,"TRUE"
        
        if debug:
          print value,",",key,",","TRUE"

        w.writerow(rowData)
      else:
        totalExcludedProfile += 1
        if debug:
          print "Skipping User ID",key, " due to excluded profile: ",thisUserProfileId

    else:
      totalSkippedInactive += 1
      #pdb.set_trace()

      if debug:
        print "Skipping Inactive userId: ", key

# close our file

f.close()

print "\n"
print "Total users to freeze:           ",totalToFreeze
print "Total users skipped as Inactive: ",totalSkippedInactive
print "Total users excluded by Profile: ",totalExcludedProfile

thistime =  datetime.now()  
print "\nfreezeusers ended at  at ",thistime.strftime("%Y-%m-%d %H:%M:%S"), "\n"

end_time = time.time()
elapsed = end_time - begin_time

print "Total time: ", str(timedelta(seconds=elapsed))
