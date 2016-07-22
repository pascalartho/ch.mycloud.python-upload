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
# Last revised: July 22, 2016
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

def numberRJust(number, referenceNumber):
  return str(number).rjust(len(str(referenceNumber)))

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
  print "Encoded Filename:  %s" % (encodedString)
  print "Filename:          %s" % (localFilePath)
  print "Filesize in MB:    %s" % (str(fileSizeInMB(localFilePath, 3)))
  
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
  result = requests.post(postQuery, headers=headers, data=dataFile)
  print "Successful Upload: %s [HTTP Status %s]" % (str(r.status_code == requests.codes.ok), str(result.status_code))
  if (result.status_code == 200):
    return True
  return False

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
failedUploadedFiles = 0
skippedFiles = 0

# foreach file to upload
for localFP in files:
  print "Start Upload %s of %s" % (numberRJust(counter, numberOfFiles), numberOfFiles)
  mycloudFP = mycloudFolder + localFP
  if (checkFileExist(localFP, mycloudFP) == False):
    try:
      if (uploadFile(localFP, mycloudFP) == True):
        uploadedFiles += 1
      else:
        failedUploadedFiles += 1
    except requests.ConnectionError as e:
      print "Oops! There was a connection error. Ensure connectivity to remote host and try again..."
      print e
    except requests.exceptions.Timeout as e:
      # Maybe set up for a retry, or continue in a retry loop
      print e
    except requests.exceptions.TooManyRedirects:
      # Tell the user their URL was bad and try a different one
      print e
    except requests.exceptions.RequestException as e:
      print e
  else:
    skippedFiles += 1
  counter += 1

# Debug information
print "Number of Files:                 %s" % (numberRJust(counter, numberOfFiles))
print "Number of uploaded Files:        %s" % (numberRJust(uploadedFiles, numberOfFiles))
print "Number of failed uploaded Files: %s" % (numberRJust(failedUploadedFiles, numberOfFiles))
print "Number of skipped Files:         %s" % (numberRJust(skippedFiles, numberOfFiles))
