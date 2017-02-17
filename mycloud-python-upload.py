##########################################################################
# ch.mycloud.python-upload - Upload files to mycloud.ch using python
##########################################################################
# Copyright (C) 2016 Pascal Artho - All Rights Reserved
#
# Usage: python ./mycloud-python-upload.py
#
# Preparation:
# - install python requests
# - set parameters
#
# Last revised: August 13, 2016
##########################################################################

import base64
from datetime import datetime
import ConfigParser
import json
import os
import os.path
import requests
import time

# if needed set "defaultencoding" to "utf-8" usin the following commands:
# import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')

os.chdir(os.path.dirname(os.path.abspath(__file__)))
settings = ConfigParser.ConfigParser()
settings.read('config.ini')

##########################################################################
# Parameters
##########################################################################
accessToken = settings.get('default', 'accessToken')
localFolder = settings.get('default', 'localFolder')
mycloudFolder = settings.get('default', 'mycloudFolder')
maxFileSizeInMB = settings.getint('default', 'maxFileSizeInMB')
numberOfRetries = settings.getint('default', 'numberOfRetries')
##########################################################################

print "Access Token:      %s" % (accessToken)
print "Local Folder:      %s" % (localFolder)
print "MyCloud Folder:    %s" % (mycloudFolder)
print "MaxFileSize in MB: %s" % (maxFileSizeInMB)
print "Number of Retries: %s" % (numberOfRetries)

def ticks(dt):
  return (dt - datetime(1, 1, 1)).total_seconds() * 10000000

def numberRJust(number, referenceNumber):
  return str(number).rjust(len(str(referenceNumber)))

def checkFileSize(localFilePath):
  # if fileSizeInMB is bigger than maxFileSizeInMB skip file
  if (fileSizeInMB(localFilePath, 3) > maxFileSizeInMB):
    return False
  return True

def checkFileExist(localFilePath, mycloudFilePath):
  #print "localFilePath:      " + localFilePath.decode('utf-8')
  #print "mycloudFilePath:    " + mycloudFilePath.decode('utf-8')
  localFileSize = os.path.getsize(localFilePath.decode('utf-8'))
  #print "localFileSize:      " + str(localFileSize)
  localFileTime = os.path.getmtime(localFilePath.decode('utf-8'))
  #print "localFileTime:      " + str(localFileTime)
  localFileTimeTicks = ticks(datetime.utcfromtimestamp(localFileTime))
  #print "localFileTimeTicks: " + str(localFileTimeTicks)
  
  for item in data:
    itemPath = str(item.get('Path').encode('utf-8'))
    if (itemPath.decode('utf-8') != mycloudFilePath.decode('utf-8')):
      continue
    if ('Length' in item):
      itemSize = long(item.get('Length'))
      if (itemSize != localFileSize):
        continue
    else:
      if (localFileSize != 0):
        continue
    #itemTicks = long(item.get('ModificationTimeTicks'))
    # if (itemTicks != localFileTimeTicks):
    #   continue
    data.remove(item)
    return True
  return False

def fileSizeInMB(filePath, decimals):
  fileSize = os.path.getsize(filePath.decode('utf-8'))
  fileSizeInMB = float(fileSize) / (1024 * 1024)
  return round(fileSizeInMB, decimals)

def encodeString(path):
  # Standard base64 encoder
  encodedString = base64.b64encode(path)
  
  # Remove any trailing '='
  encodedString = encodedString.split('=')[0]
  
  # 62nd char of encoding
  encodedString = encodedString.replace('+', '-')
  
  # 63rd char of encoding
  encodedString = encodedString.replace('/', '_')
  return encodedString

def uploadFile(localFilePath, mycloudFilePath):
  # date of file
  localFileTime = os.path.getmtime(localFilePath.decode('utf-8'))
  #print "localFileTime:      " + str(localFileTime)
  dateOfFile = datetime.utcfromtimestamp(localFileTime).strftime("%a, %d %b %Y %H:%M:%S")
  
  encodedString = encodeString(mycloudFilePath)
  
  # Debug information
  print "Start Upload Time: %s" % (datetime.now())
  print "Encoded Filename:  %s" % (encodedString)
  print "Filename:          %s" % (localFilePath.decode('utf-8'))
  print "Filesize in MB:    %s" % (str(fileSizeInMB(localFilePath, 3)))
  
  # define headers for HTTP Post request
  headers = {}
  headers['Content-Type'] = 'application/octet-stream'
  headers['Content-Disposition'] = 'attachment; modification-date="'+ dateOfFile + ' GMT"; filename="'+ localFilePath + '"'
  headers['User-Agent'] = 'mycloud.ch - python uploader'
  headers['Authorization'] = 'Bearer ' + accessToken
  headers['Connection'] = 'keep-alive'
  
  dataFile = open(localFilePath.decode('utf-8'), 'rb')
  postQuery = "https://storage.prod.mdl.swisscom.ch/object/?p=%s" % (encodedString)
  
  try:
    # Upload file using python requests
    # if needed add "verify=False" to perform "insecure" SSL connections and transfers
    # result = requests.post(postQuery, headers=headers, data=dataFile, verify=False)
    result = requests.post(postQuery, headers=headers, data=dataFile)
    print "Successful Upload: %s [HTTP Status %s]" % (str(result.status_code == requests.codes.ok), str(result.status_code))
    if (result.status_code == 200):
      return True
    return False
  except requests.ConnectionError as e:
    print "Oops! There was a connection error. Ensure connectivity to remote host and try again..."
    print e
    return False
  except requests.exceptions.Timeout as e:
    # Maybe set up for a retry, or continue in a retry loop
    print "Oops! There was a timeout error. Ensure connectivity to remote host and try again..."
    print e
    return False
  except requests.exceptions.TooManyRedirects as e:
    # Tell the user their URL was bad and try a different one
    print "Oops! There were too many redirects. Try a different URL ..."
    print e
    return False
  except requests.exceptions.RequestException as e:
    print e
    return False

def printHashmap(hashmap):
  for key, value in sorted(hashmap.items()):
    print "  - %s (%s MB)" % (key.decode('utf-8'), value)

# change current directory
os.chdir(localFolder)

encodedString = encodeString(mycloudFolder)

# get current list of uploaded files
headers = {}
headers['User-Agent'] = 'mycloud.ch - python uploader'
headers['Authorization'] = 'Bearer ' + accessToken

getQuery = "https://storage.prod.mdl.swisscom.ch/sync/list/?p=%s" % (encodedString)
# if needed add "verify=False" to perform "insecure" SSL connections and transfers
# resultGet = requests.get(getQuery, headers=headers, verify=False)
resultGet = requests.get(getQuery, headers=headers)
if (resultGet.status_code != 200):
  print "Oops! The accessToken is not correct. Get a new accessToken and try again..."
  quit()

array = resultGet.text
# save current list of uploaded files in array
data = json.loads(array)

# find files for upload
files = list()
for dirpath, dirnames, filenames in os.walk(u"."):
  for filename in [f for f in filenames]:
    file = str(os.path.join(dirpath.encode('utf-8'), filename.encode('utf-8')))
    file = file.replace("\\", '/')
    if (file.startswith(".//")):
      file = file.replace(".//", '', 1)
    if (file.startswith("./")):
      file = file.replace("./", '', 1)
    files.append(file)

# sort files for upload
files.sort()

# count files for upload
numberOfFiles = len(files)

# define progress counter
counter = 1
uploadedFiles = {}
failedUploadedFiles = {}
skippedFiles = {}
skippedFilesSize = {}

try:
  # foreach file to upload
  for localFP in files:
    print "Start Upload %s of %s" % (numberRJust(counter, numberOfFiles), numberOfFiles)
    mycloudFP = mycloudFolder + localFP
    fileSize = fileSizeInMB(localFP, 3)
    if (checkFileExist(localFP, mycloudFP) == False):
      if (checkFileSize(localFP) == True):
        uploadcompleted = False
        numberOfTries = 0
        while (uploadcompleted == False and numberOfTries < numberOfRetries):
          uploadcompleted = uploadFile(localFP, mycloudFP)
          numberOfTries += 1
        if (uploadcompleted):
          uploadedFiles[localFP] = fileSize
        else:
          failedUploadedFiles[localFP] = fileSize
      else:
        skippedFilesSize[localFP] = fileSize
    else:
      skippedFiles[localFP] = fileSize
    counter += 1
except KeyboardInterrupt, e:
  print "\n##############################"
  print "Abort upload to mycloud.ch ..."
  print "##############################\n"

# Debug information
print "Number of Files:                             %s" % (numberRJust(numberOfFiles, numberOfFiles))
print "Number of uploaded Files:                    %s (%s MB)" % (numberRJust(len(uploadedFiles), numberOfFiles), sum(uploadedFiles.values()))
print "Number of failed uploaded Files:             %s (%s MB)" % (numberRJust(len(failedUploadedFiles), numberOfFiles), sum(failedUploadedFiles.values()))
printHashmap(failedUploadedFiles)
print "Number of skipped Files (already existing):  %s (%s MB)" % (numberRJust(len(skippedFiles), numberOfFiles), sum(skippedFiles.values()))
print "Number of skipped Files (too big to upload): %s (> %s MB, %s MB)" % (numberRJust(len(skippedFilesSize), numberOfFiles), maxFileSizeInMB, sum(skippedFilesSize.values()))
printHashmap(skippedFilesSize)
