#---------------------------------------------------------------------------------------------------------
#
#   Module: bmxpush.py
#
#   Author: Mitchell McConnell
#
#---------------------------------------------------------------------------------------------------------
#
#  Date     Who         Description
#
# 12/03/14  mjm         Original version
#
#---------------------------------------------------------------------------------------------------------

import sys
import os
import string
import datetime 
import getopt
import csv
import pdb
from datetime import datetime
import time
from datetime import timedelta
from time import gmtime, strftime
#import logging
from simple_salesforce import Salesforce

SUCCESS = 0

beep = True
debug = False
special = False
verbose = False
version = "00.00.01"
pdbTrace = 1
haltOnError = False
maxErrors = 1

allMaps = {}

# This is the destination directory for the export files

filePath = os.path.normpath("C:/Users/mjmcconnell/")
outfile = 'freezeusers.csv'

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
  print("  -P  Pause in debugger after each step")
  print("  -v  Enable verbose")
  print("  -h  logging.info(this help message")


#---------------------------------------------------------------------------------------------------------
#
#   Function: csvToMap
#
#   This function returns a map that is indexed by the old ID
#
#---------------------------------------------------------------------------------------------------------
def csvToMap(sf, sfObject, filename):
    global debug
    global special





#---------------------------------------------------------------------------------------------------------
#
#   Function: csvToMap
#
#   This function returns a map that is indexed by the old ID
#
#---------------------------------------------------------------------------------------------------------
def csvToMap(filename):
    global debug
    global special
    
    newMap = {}
    newId = None

    if debug:
      print "(csvToMap) Enter, file: ",filename
    
    input_file = csv.DictReader(open(filename))

    for row in input_file:
        # Save the original ID as the MIGRATION_ID__C for later lookups
        
        row["MIGRATION_ID__C"] = row["ID"]
        newId = row["ID"]
        
        # delete the actual id from the map, as the upsert does not like that
        del(row["ID"])
        
        # also, delete stuff that we don't need or that will get created on the upsert..
        # Note: some do not exist in all files, hence the 'try-except' logic
        
        del(row["LASTMODIFIEDDATE"])
        del(row["LASTMODIFIEDBYID"])
        
        try:
            del(row["LASTREFERENCEDDATE"])
        except KeyError, ke:
            #print "Key not found: ",ke
            pass
            
        try:
            del(row["OWNERID"])
        except KeyError, ke:
            #print "Key not found: ",ke
            pass
        
        del(row["CREATEDDATE"])
        del(row["CREATEDBYID"])
        del(row["SYSTEMMODSTAMP"])

        try:
            del(row["LASTVIEWEDDATE"])
        except KeyError, ke:
            #print "Key not found: ",ke
            pass
        
        del(row["ISDELETED"])
        
        newMap[newId] = row
        
    # change uppercase TRUE/FALSE to lowercase
    for key in newMap.keys():
        if debug:
            print "****************** newMap key: ",key,", value: ",newMap[key],"******************"
        for key1 in newMap[key].keys():
            if (newMap[key][key1] == "FALSE") or (newMap[key][key1] == "TRUE"):
                newMap[key][key1] = newMap[key][key1].lower()
            
    return newMap

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

print "bmxpush version ",version," starting up at ",starttime.strftime("%Y-%m-%d %H:%M:%S")

# process command-line options

try:
    opts, args = getopt.getopt(sys.argv[1:], "u:p:t:dvh", ["help", "output="])
except getopt.GetoptError, err:
    # logging.info(help information and exit:
    #logging.info(str(err)) # will logging.infosomething like "option -a not recognized"
    usage()
    sys.exit(2)

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
    elif o == "-d":
        debug = True
        if debug:
            print("Set debug from command line")
    elif o == "-v":
        # Set verbose here and in all the modules
        verbose = True
        
        if debug:
            print("Set verbose from command line")
    elif o == "-h":
        usage()
        sys.exit(2)
    else:
        print("ERROR: unhandled option: ",o)
        usage()
        sys.exit(2)

# set up logging the way we want it
##if debug:
##  logging.basicConfig(format='%(asctime)s : %(levelname)s - %(message)s',level=logging.DEBUG)
##elif verbose:
##  logging.basicConfig(format='%(asctime)s : %(levelname)s - %(message)s',level=logging.INFO)
##else:
##  logging.basicConfig(format='%(asctime)s : %(levelname)s - %(message)s',level=logging.WARN)
##
##logging.info("bmxpush version %s starting up\n",version)

# setup our salesforce connection

sf = Salesforce(username=login,
                password=passwd,
                security_token=token,
                sandbox=True)

thistime = datetime.now()

userMap = {}
profileMap = {}
loginMap = {}

#userQuery = "select Id,Name FROM user where user.IsActive = 'true' and user.profile.name not in ('System Administrator','Support')"
userQuery = "select Id, Name, ProfileId FROM user where IsActive = true"

print userQuery
pdb.set_trace()

userResult = sf.query(userQuery)

userRset = userResult["records"]

for rec in userRset:
  userId = rec["Id"]
  userProfileId = rec["ProfileId"]
  userMap[userId] = userProfileId

  print userId,",",userProfileId

#print userMap

profileQuery = "select Id, Name FROM profile where Name in ('System Administrator','Support')"

print profileQuery
pdb.set_trace()

profileResult = sf.query(profileQuery)

profileRset = profileResult["records"]

for rec in profileRset:
  profileId = rec["Id"]
  profileMap[profileId] = rec["Name"]

  print profileId,",",profileId,", Name: ",profileMap[profileId]

#print profileMap

finalList = ()

loginQuery = "select Id, UserId, IsFrozen FROM UserLogin"

print loginQuery
pdb.set_trace()

loginResult = sf.query(loginQuery)

loginRset = loginResult["records"]

print "UserLoginId,UserId"

for rec in loginRset:
  loginId = rec["Id"]
  loginMap[loginId] = rec["UserId"]

  print loginId,",",loginMap[loginId]

# now build the csv file

print "\n-------------------------------------------------------------------------\n"
print "CSV values"

for key, value in loginMap.iteritems():
  if value in userMap:

    print key,",",value,"TRUE"
else:
  if debug:
    print "Skipping userId: ", value


thistime =  datetime.now()  
print "\nbmxpush ended at  at ",thistime.strftime("%Y-%m-%d %H:%M:%S"), "\n"

end_time = time.time()
elapsed = end_time - begin_time

print "Total time: ", str(timedelta(seconds=elapsed))
