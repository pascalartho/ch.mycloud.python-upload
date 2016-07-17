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
# Last revised: July 17, 2016
##########################################################################

import base64
from datetime import datetime
import json
import os
import os.path
import requests
import time

##########################################################################
# Parameters
##########################################################################
accessToken = ""
localFolder = "/home/ubuntu/mycloud/"
mycloudFolder = "/Drive/pythonUpload/"
##########################################################################

def ticks(dt):
  return (dt - datetime(1, 1, 1)).total_seconds() * 10000000

def checkFileExist(localFilePath, mycloudFilePath):
  #print "localFilePath:      " + localFilePath
  #print "mycloudFilePath:    " + mycloudFilePath
  localFileSize = os.path.getsize(localFilePath)
  #print "localFileSize:      " + str(localFileSize)
  localFileTime = os.path.getmtime(localFilePath)
  #print "localFileTime:      " + str(localFileTime)
  localFileTimeTicks = ticks(datetime.utcfromtimestamp(localFileTime))
  #print "localFileTimeTicks: " + str(localFileTimeTicks)
  for item in data:
    itemPath = str(item.get('Path'))
    if (itemPath != mycloudFilePath):
      continue
    if ('Lenght' in item):
      itemSize = long(item.get('Length'))
      if (itemSize != localFileSize):
        continue
    #itemTicks = long(item.get('ModificationTimeTicks'))
    # if (itemTicks != localFileTimeTicks):
    #   continue
    return True
  return False

def fileSizeInMB(filePath, decimals):
  fileSize = os.path.getsize(filePath)
  fileSizeInMB = float(fileSize) / (1024 * 1024)
  return round(fileSizeInMB, decimals)

def uploadFile(localFilePath, mycloudFilePath):
  # date of file
  localFileTime = os.path.getmtime(localFilePath)
  #print "localFileTime:      " + str(localFileTime)
  dateOfFile = datetime.utcfromtimestamp(localFileTime).strftime("%a, %d %b %Y %H:%M:%S")
  
  # Standard base64 encoder
  encodedString = base64.b64encode(mycloudFilePath)
  
  # Remove any trailing '='
  encodedString = encodedString.split('=')[0]
  
  # 62nd char of encoding
  encodedString = encodedString.replace('+', '-')
  
  # 63rd char of encoding
  encodedString = encodedString.replace('/', '_')
  
  # Debug information
  print "Encoded Filename: " + encodedString
  print "Filename:         " + localFilePath
  print "Filesize in MB:   " + str(fileSizeInMB(localFilePath, 3))
  
  # define headers for HTTP Post request
  headers = {}
  headers['Content-Type'] = 'application/octet-stream'
  headers['Content-Disposition'] = 'attachment; modification-date="'+ dateOfFile + ' GMT"; filename="'+ localFilePath + '"'
  headers['User-Agent'] = 'mycloud.ch - python uploader'
  
  dataFile = open(localFilePath, 'rb')
  postQuery = "https://storage.prod.mdl.swisscom.ch/object/?p=%s&access_token=%s" % (encodedString, accessToken)
  
  # Upload file using python requests
  # if needed add "verify=False" to perform "insecure" SSL connections and transfers
  # requests.post(postQuery, headers=headers, data=dataFile, verify=False)
  requests.post(postQuery, headers=headers, data=dataFile)

# change current directory
os.chdir(localFolder)

# get current list of uploaded files
getQuery = "https://storage.prod.mdl.swisscom.ch/sync/list/%s?access_token=%s" % (mycloudFolder, accessToken)
# if needed add "verify=False" to perform "insecure" SSL connections and transfers
# r = requests.get(getQuery, verify=False)
r = requests.get(getQuery)
array = r.text
# save current list of uploaded files in array
data = json.loads(array)

# find files for upload
files = list()
for dirpath, dirnames, filenames in os.walk("."):
  for filename in [f for f in filenames]:
    file = str(os.path.join(dirpath, filename))
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
counter = 0
uploadedFiles = 0
skippedFiles = 0

# foreach file to upload
for localFP in files:
  print "Start Upload %s of %s" % (counter, numberOfFiles)
  mycloudFP = mycloudFolder + localFP
  if (checkFileExist(localFP, mycloudFP) == False):
    uploadFile(localFP, mycloudFP)
    uploadedFiles += 1
  else:
    skippedFiles += 1
  counter += 1

# Debug information
print "Number of Files: %s" % (counter)
print "Number of uploaded Files: %s" % (uploadedFiles)
print "Number of skipped Files: %s" % (skippedFiles)
