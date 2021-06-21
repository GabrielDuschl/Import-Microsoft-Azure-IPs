#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import urllib
import json
from urllib import urlopen
import pprint
import time
import subprocess
import os
import socket

import datetime
from datetime import datetime


#title:                 :importMicrosoftIPs.py
#description            :this script will receive IPs via JSON format and send it via Rest API to Barracuda CC to create a new Network Object
#author                 :Gabriel Duschl
#email                  :Gabriel.Duschl@kapsch.net
#date                   :02.06.2021
#version                :1.6
#usage                  :execute python script in Barracuda SSH
#notes                  :paste URL with IPs in JSON format

netName = "MsAzureIPs" #network object name
directory = "logs" #name directory
os.chdir("/etc/jobs/")  #Workingdirectory
now = datetime.now() #get current time
datetime = now.strftime("%Y-%m-%d|%H:%M") #store time
logname = "log_" + datetime + ".txt" #file name with output


#check if directory "logs" exists 
if not os.path.exists(directory):
    os.makedirs(directory)
       
#create log file
log = open("logs/log_" + datetime +".txt", "w")
log.write("Starting Script ")
log.write(datetime+"\n")
        

#Downloading latest version 
with open('shell.sh', 'w') as shell:
        shell.write('''
                    content=$(curl -L https://www.microsoft.com/en-us/download/confirmation.aspx?id=56519)
                    touch output.txt
                    echo $content | tee output.txt
                    ''')

#executing shell script to get Microsoft IPs
subprocess.call(["chmod", "+x", "shell.sh"])
try:
    os.system("sh shell.sh > log")
except IOError:
    log.write("Error occured - invalid URL\n")
    exit()
subprocess.call(["rm", "shell.sh", "-f"])
subprocess.call(["rm", "log", "-f"])


with open('output.txt','r') as file:
        htmlCode = file.read()

#find download url in html code
start = htmlCode.find('https://download.microsoft.com/download')
end = htmlCode.find('ServiceTags_Public_')
print("Starting URL")
print(start)
print("Ending URL")
end = end + 32
print(end)

url = htmlCode[start:end]
log.write(url + "\n")
subprocess.call(["rm", "output.txt", "-f"])


log.write("Start Downloading Microsoft Azure IPs \n")

try:
    testfile = urllib.URLopener()
    #Link with URL in JSON Format
    testfile.retrieve(url, "AzureIPs.json")
    time.sleep(1.5)
    log.write("Successfully received Microsoft Azure IPs \n")
except IOError:
    log.write("URL ungültig\n")
    log.write("Link in testfile.tetrieve überprüfen\n")  
    log.write("Exit Script\n")
    exit()


with open('AzureIPs.json','r') as json_file:
        data = json.load(json_file)

#get Objects with regionID = 17 (northeurope)
file = open("AzureListe.txt","w")
pfx = sum( [ x['properties']['addressPrefixes'] for x in data['values'] if x['properties']['regionId']==17 ],[])
print("Anzahl der Elemente: ")
print(str(pfx))
pprint.pprint(pfx, file)
file.close()

#print objects in empty line 
y = open("AzureFinal.txt", "w")
with open("AzureListe.txt") as fp:
        Lines = fp.readlines()
        for line in Lines:
                string = len(line)
                string = string - 3
                y.write(line[3:string] + "\n")

y.close()

with open("AzureFinal.txt") as result:
	uniqlines = set(result.readlines())
	with open("output.json", "w") as rmdup:
		rmdup.writelines(set(uniqlines))
		
#FINISHED
   
  
		
print("Start building Shell Script...")
time.sleep(1)

with open("output.json") as t:
        llines = t.readlines()
		
post_file= """   { "included": [  """

#IP addresses from AzureFinal.txt
for line in llines:
        post_file+=""" { "entry": { "ip": """+'"'+line[0:len(line)-1] +'" } },\n'

#last row
post_file=post_file[0:len(post_file)-2]
post_file+="],"
post_file += """
				"name": " """+ netName
post_file += """ ", 
				"type": "generic"
				
					
				}

			 """

with open("payload.json", "w") as j:
	j.write(post_file)
  
#get directory path  
cPath = os.getcwd()
print("Directory: " + cPath)
    
#get ip address
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print("IP Address: " + local_ip)
    
#Shell Script - Enter IP Adress and Authorization
time.sleep(1)
with open ('shell.sh', 'w') as shell:
		shell.write('''
		
					curl -k --request PUT --http1.0 \\
						--url 'https://193.186.11.151:8443/rest/cc/v1/config/global/firewall/objects/networks/MsAzureIPs?envelope=true' \\
						--header 'Authorization: Basic cmVzdGFkbWluOktiY3Bhc3N3MHJk' \\
						--header 'Content-Type: application/json' \\
						--header 'accept: */*' \\
						--data "@''')
                    
        
f = open('shell.sh', 'a+')
f.write(cPath)
f.write('/payload.json"')
f.close()                    
					
#change file permission					
subprocess.call(["chmod", "+x", "shell.sh"])
log.write("...done \n")
log.write("Executing Shell Script \n")
log.write("This can take up to one minute \n")

#Executing Shell Script
try:
    os.system("sh shell.sh")
    log.write("code: 200\n")
    log.write("message: OK\n")
except: 
    log.write("An error occurred while executing the shell script \n")
    exit()
    
#Deleting Files older than 14 days
current_time = time.time()
daysToDelete = 14
directory = '/logs/'

for dirpath,_,filenames in os.walk(directory):
    for f in filenames:
        fileWithPath = os.path.abspath(os.path.join(dirpath, f))
        creation_time = os.path.getctime(fileWithPath)
        print("file available:",fileWithPath)
        if (current_time - creation_time) // (24 * 3600) >= daysToDelete:
            os.unlink(fileWithPath)
            print('{} removed'.format(fileWithPath))
            print("\n")
        else:
            print('{} not removed'.format(fileWithPath))    
    
    
#Deleting Files
log.write("Deleting redundante files... \n")
subprocess.call(["rm", "shell.sh", "-f"])
subprocess.call(["rm", "payload.json", "-f"])   
subprocess.call(["rm", "AzureFinal.txt", "-f"])  
subprocess.call(["rm", "AzureListe.txt", "-f"])  
subprocess.call(["rm", "AzureIPs.json", "-f"])
subprocess.call(["rm", "output.json", "-f"])
log.write("...done \n")
log.write("---FINISHED---\n")
