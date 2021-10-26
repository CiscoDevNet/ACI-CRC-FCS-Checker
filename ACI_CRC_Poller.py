'''
###########################################################################
Copyright (c) 2021 Cisco systems

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

###########################################################################

Version: v1.0
Created on: 28th Sep, 2021

Supported OS Platforms: Windows, MAC
Script Tested on: 
    Windows-10 64Bit
    MAC Bigsur

Authors:
    Aditya Kesarwani adkesarw@cisco.com
    Devi S devs2@cisco.com
    Kallol Bosu kbosu@cisco.com
    Krishna Nagavelu knagavol@cisco.com
    Ranganatha Raju ranraju@cisco.com
    Richita Gajjar rgajjar@cisco.com
    Sathvika Kotha sathkoth@cisco.com
    Savinder Singh savsingh@cisco.com
    Solomon Sudhakar sosudhak@cisco.com

'''


import stdiomask  # To hide the password with astesrisk
import paramiko
from datetime import datetime, timedelta
import sys
import os
from termcolor import colored
from time import time, sleep
from paramiko.ssh_exception import AuthenticationException, SSHException

# Folder where the files are to be stored
LOCAL_PATH = ""
ssh = paramiko.SSHClient()

flag1 = 0  # To track whether the CRC Errors exist in each run
flag2 = 0  # To track whether the FCS Errors exist in each run
# To track whether the user likes to run the script even no errors are observed.
flag3 = 0


class MaxexceedError(Exception):
    pass


class PastTimeError(Exception):
    pass

class InvalidFileFormatError(Exception):
    pass



# Function to establish connection to APIC
def connect_apic(ip_address, admin_username, admin_password):
    print("Trying to connect to APIC")
    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(hostname=ip_address, port=int(22), allow_agent=False, username=admin_username,
                    password=admin_password)
        print("Connection established to the APIC")
    except AuthenticationException:
        print(colored("Authentication failed, please verify your credentials:",'yellow'))
        print(colored("Connection to the APIC failed !!!",'yellow'))
        exit()
    except:
        print(colored("Connection to the APIC failed !!!",'yellow'))
        print(colored("Verify the domain is up and re-run the script",'yellow'))
        exit()


#Function to execute CRC MOQuery and stores the non-zero CRC error interfaces
def crc_execute(outFileName):
    global flag1
    flag1 = 0
    crc_command = "moquery -c rmonEtherStats -f 'rmon.EtherStats.cRCAlignErrors>" + \
        '"'+"1"+'"'+"'"+" | egrep '^dn|cRCAlignErrors'"

    stdin, stdout, stderr = ssh.exec_command(crc_command)
    out = stdout.readlines()
    if len(out) == 0:  # If there are no CRC error occurred
        flag1 = 1
        return
    outFile = open(outFileName, "w")
    outFile.writelines("#CRC Output\n")
    outFile.writelines(out)
    outFile.close()

#Function to execute FCS MOQuery and stores the non-zero FCS error interfaces
def fcs_execute(outFileName):
    global flag1, flag2
    flag2 = 0
    fcs_command = "moquery -c rmonDot3Stats -f 'rmon.Dot3Stats.fCSErrors>" + \
        '"'+"1"+'"'+"'"+" | egrep '^dn|fCSErrors'"
    stdin, stdout, stderr = ssh.exec_command(fcs_command)
    out = stdout.readlines()
    if len(out) == 0 and flag1 == 1:  # If both CRC and FCS are not occurred
        flag2 = 1
        return
    if len(out) != 0:
        outFile = open(outFileName, "a")
        outFile.writelines("#FCS Output\n")
        outFile.writelines(out)
        outFile.close()

#Function to call the MOquery function for the specified time
def store_the_moquery(end_time):
    global flag3
    while(True):
        print("The script is executing ........................")
        now = datetime.today()
        outFileName = LOCAL_PATH+"CRC_FCS_"+str(now.year) + \
            str('{:02d}'.format(now.month))+str('{:02d}'.format(now.day))+"_" + \
            str('{:02d}'.format(now.hour)) + \
            str('{:02d}'.format(now.minute))+".txt"
        # Execute the query
        crc_execute(outFileName)
        fcs_execute(outFileName)
        if flag2 == 1 and flag3 == 0:  # If both the moquery is empty
            flag3 = 1
            user_query = input(
                "No errors in the Fabric, do you still want to run the script(y/n):")
            if user_query.lower() == "y":
                print(
                    "Script will only generate files if errors are generated in given time range of script execution")
            else:
                sys.exit()
        else:
            if(end_time < datetime.today()):
                break
            sleep(60*5)


# Getting the required inputs
ip_address = input("Enter the IP address or DNS Name of APIC: ")
print("__________________________________________________________")
admin_username = input("Enter the username: ")
print("___________________________________________________________")
admin_password = stdiomask.getpass("Enter the password: ")
connect_apic(ip_address, admin_username, admin_password)
print("___________________________________________________________")
print("Please enter the folder where files have to be stored")

#####Checking whether the entered file format is valid ###########################
while(True):
  print("_____________________________________________________________")
  print("VALID folder format:")
  print("EXAMPLE:")
  print("Windows-> C:\\Users\Admin\Desktop\ACI\\")
  print("MAC -> /User/admin/Desktop/ACI/")
  print("---------------------------------------------------------------------------------------------------")
  print("PLEASE NOTE that data collection and script execution might get impacted if folder format is not as below")
  print("--------------------------------------------------------------------------------------------------------")
  try:
   LOCAL_PATH = input(
    "Enter the absolute path of the folder where the files have to be stored:")
   
   if sys.platform.startswith('win') and not(LOCAL_PATH.endswith('\\')):
       raise InvalidFileFormatError
   if sys.platform.startswith('darwin') and not(LOCAL_PATH.endswith('/')):
       raise InvalidFileFormatError
   files = [file for file in os.listdir(LOCAL_PATH)] ###Just to check whether the script able to resolve folder name
  except InvalidFileFormatError:
   print(colored("!!!Invalid file format, please enter valid path",'yellow'))
  except:
   print(colored("!!!The system cannot find the path specified, please check the folder format or the folder exists",'yellow'))
  else:
   break

print("----------------------------------------------------------------")
now = datetime.today()
max_range = datetime.today()+timedelta(7)
while(True):
    end_time = input(
        "Enter the End Time until which the script runs(in the format of yyyy-mm-dd hh:mm, current time:"+str(now.year)+"-"+str('{:02d}'.format(now.month))+"-"+str('{:02d}'.format(now.day))+" "+str('{:02d}'.format(now.hour))+":"+str('{:02d}'.format(now.minute))+"....  maximum upto "+str(max_range.year)+"-"+str('{:02d}'.format(max_range.month))+"-"+str('{:02d}'.format(max_range.day))+" "+str('{:02d}'.format(max_range.hour))+":"+str('{:02d}'.format(max_range.minute))+"): ")
    print("___________________________________________________________")
    try:
        # Extracting date, hour and minute from the input
        date_tuple = tuple([int(x) for x in end_time[:10].split('-')]) + \
            tuple([int(x) for x in end_time[11:].split(':')])
        endtimeobj = datetime(*date_tuple)
        if(endtimeobj < datetime.today()):
            raise PastTimeError
        if(endtimeobj > max_range):
            raise MaxexceedError
    except PastTimeError:
        print("The entered time is already passed")
    except MaxexceedError:
        print("The entered time range exceeds than max range")
        user_query = input(
            "Do you want to continue with the maximum showed range(y/n):")
        if user_query.lower() == "y":
            endtimeobj = max_range
            break
        else:
            continue
    except KeyboardInterrupt:
                print()
                inp=int(input("Do you want to terminate the program, 1-yes, 0-no (0/1):"))
                if inp==1:
                    sys.exit()
                else:
                    continue

    except:
        print(colored("!!!!Invalid time format",'yellow'))
        print(colored("!!!!Please enter in the format of yyyy-mm-dd hh:mm",'yellow'))
        print("-------------------------------------")

    else:
        break

store_the_moquery(endtimeobj)
ssh.close()
sys.exit()
