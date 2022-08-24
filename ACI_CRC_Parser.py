'''
###########################################################################
Copyright (c) 2021 Cisco and/or its affiliates

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


import os
import stdiomask  # To hide the password with astesrisk
from tabulate import tabulate
#from os import get_terminal_size
#import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates as md
from termcolor import colored
import pandas as pd
import paramiko
import re
import sys
import time
from paramiko.ssh_exception import AuthenticationException, SSHException

os.system('color')  # To enable color to the terminal of OS

table = pd.DataFrame()  # Creating an empty dataframe
#size = get_terminal_size()
# find the width of the user's terminal window

#width = pd.util.terminal.get_terminal_size()
#pd.set_option('display.width', size.columns)

ssh = paramiko.SSHClient()

# Folder where the files are stored
LOCAL_PATH = ""

# Intializing empty names for CRC  and FCS Columns for using it later

crc = ""
fcs = ""
crc_diff = ""
fcs_diff = ""
date_list = []  # Initializing the empty list to store the date values
sorted_files = []  # Initializing the empty list to store sorted files

# Function to establish connection to APIC


class InvalidRangeError(Exception):
    pass


class InvalidInterface(Exception):
    pass


class InvalidFileFormatError(Exception):
    pass

#Function to establish connection to apic
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


def compare_the_output(file1, file2):
    global table
    create_table_columns(file1, file2)
    parse_file1(file1)
    parse_file2(file2)
    assign_node()
    assign_neighbors()
    assign_type()
    print("__________________________________________________________")
    print("The script execution has completed")
    print("___________________________________________________________")
    print("The data is by default sorted according to FCS Difference")
    print("------------------------------------------------------------")
    print()
    print(colored("Interface where FCS Difference is non-zero, are the source of CRC. Rest interfaces are forwarding the same.",'yellow'))
    print(colored("Check L1 and/or MTU for the interfaces, where FCS Difference is non-zero. Or Contact Cisco TAC",'yellow'))
    print("Interfaces with only CRC increments usually carry stomped packets")
    print()
    table = table.sort_values(fcs_diff, ascending=False)
    print(tabulate(table,
                   headers=table.columns.tolist(), tablefmt='pretty', showindex=False))

    while(True):
        print("--------------------------------------------------------------------------------")
        print("Please select any number below to sort the data further or to view granular data of an interface")
        print("1.Sort the data further ")
        print("2.View the granular data of an interface")
        print("3.Exit")
        num = int(input("Input the number:"))
        if(num == 1):
            sort_options()
        if(num == 2):
            granular_view()
        if(num == 3):
            sys.exit()

#Function to create the table structure
def create_table_columns(file1, file2):
    date_time1 = file1[8:21]
    date_time2 = file2[8:21]
    global crc, fcs, crc_diff, fcs_diff
    crc = date_time1+"\n"+"CRC"
    fcs = date_time1+"\n"+"FCS"
    crc_diff = date_time2+"\n"+"CRC_Diff"
    fcs_diff = date_time2+"\n"+"FCS_diff"
    column_names = ['POD_ID', 'NODE_ID', 'NODE_NAME',
                    'NODE_ROLE', 'INTERFACE', crc, crc_diff, fcs, fcs_diff, 'NEIGHBOR','ERROR SOURCE']
    # Assigning the column to the dataframe
    for col in column_names:
        table[col] = pd.Series([], dtype='object')

#Function to parse the first selected file
def parse_file1(file1):
    fp = open(LOCAL_PATH+file1, "r")
    file1_list = fp.readlines()
    if file1_list[0].startswith("#CRC"):
        for i in range(1, len(file1_list), 2):
            # This condition is to break the loop if its finds FCS Errors or there is no CRC output in the file
            if file1_list[i].startswith("#FCS"):
                break
            if len(file1_list[i].strip()) == 0:
                break
            try:
                val = int(re.sub(r"[\n\t]*", "", file1_list[i].split(":")[1]))
                key = (re.sub(r"[\n\t]*", "",
                              file1_list[i+1].split(":")[1])).lstrip()
            except:
                print(colored(
                    "!!!Please ensure the moquery collected are in proper format,please re-run poller script!!!", "yellow"))
                sys.exit(0)
            if "phys" in key:
                pod_id = re.search('pod-\d*', key).group().split('-')[1]
                node_id = re.search('node-\d*', key).group().split('-')[1]
                interface = (
                    re.search('phys-\[\w*/\d*(/\d*)?\]', key).group().split('-')[1]).replace("[", "")
                interface = interface.replace("]", "")
                total_rows = table.shape[0]
                table.loc[total_rows, 'POD_ID'] = pod_id
                table.loc[total_rows, 'NODE_ID'] = node_id
                table.loc[total_rows, 'INTERFACE'] = interface
                table.loc[total_rows, crc] = val

    if file1_list[0].startswith("#FCS") or file1_list[i].startswith("#FCS"):
        # If file starts with FCS Output without CRC Errors
        if file1_list[0].startswith("#FCS"):
            start = 1
        # If FCS output follows CRC Output
        elif file1_list[i].startswith("#FCS"):
            start = i+1

        for k in range(start, len(file1_list), 2):

            if len(file1_list[k].strip()) == 0:
                break
            try:
                val = int(
                    re.sub(r"[\n\t]*", "", file1_list[k+1].split(":")[1]))
                key = (re.sub(r"[\n\t]*", "",
                              file1_list[k].split(":")[1])).lstrip()
            except:
                print(colored(
                    "!!!Please ensure the moquery collected are in proper format,please re-run poller script!!!", "yellow"))
                sys.exit(0)
            if "phys" in key:
                interface = (
                    re.search('phys-\[\w*/\d*(/\d*)?\]', key).group().split('-')[1]).replace("[", "")
                interface = interface.replace("]", "")
                pod_id = re.search('pod-\d*', key).group().split('-')[1]
                node_id = re.search('node-\d*', key).group().split('-')[1]
                index = table.loc[(table.POD_ID == pod_id) & (table.NODE_ID == node_id)
                                  & (table.INTERFACE == interface)]
                if index.empty:  # If there are no CRC and FCS occurred, initial table formation starts only in this part
                    # Get the total number of rows to append new row
                    total_rows = table.shape[0]
                    table.loc[total_rows, 'POD_ID'] = pod_id
                    table.loc[total_rows, 'NODE_ID'] = node_id
                    table.loc[total_rows, 'INTERFACE'] = interface
                    table.loc[total_rows, crc] = 0
                    table.loc[total_rows, fcs] = val
                else:
                    index = table.loc[(table.POD_ID == pod_id) & (table.NODE_ID == node_id)
                                      & (table.INTERFACE == interface)].index[0]
                    table.loc[index, fcs] = val

#Function to parse the second input file
def parse_file2(file2):
    fp = open(LOCAL_PATH+file2, "r")
    file2_list = fp.readlines()
    if file2_list[0].startswith("#CRC"):
        for i in range(1, len(file2_list), 2):
            # This condition is to break the loop if its finds FCS Errors or there is no CRC output in the file
            if file2_list[i].startswith("#FCS"):
                break
            if len(file2_list[i].strip()) == 0:
                break
            try:
                val = int(re.sub(r"[\n\t]*", "", file2_list[i].split(":")[1]))
                key = (re.sub(r"[\n\t]*", "",
                              file2_list[i+1].split(":")[1])).lstrip()
            except:
                print(colored(
                    "!!!Please ensure the moquery collected are in proper format,please re-run poller script!!!", "yellow"))
                sys.exit(0)
            if "phys" in key:
                pod_id = re.search('pod-\d*', key).group().split('-')[1]
                node_id = re.search('node-\d*', key).group().split('-')[1]
                interface = (
                    re.search('phys-\[\w*/\d*(/\d*)?\]', key).group().split('-')[1]).replace("[", "")
                interface = interface.replace("]", "")
                index = table.loc[(table.POD_ID == pod_id) & (table.NODE_ID == node_id)
                                  & (table.INTERFACE == interface)]
                if index.empty:  # If there are no CRC and FCS occurred in the particular interface, the interface is added to the table only here
                    # Get the total number of rows to append new row
                    total_rows = table.shape[0]
                    table.loc[total_rows, 'POD_ID'] = pod_id
                    table.loc[total_rows, 'NODE_ID'] = node_id
                    table.loc[total_rows, 'INTERFACE'] = interface
                    table.loc[total_rows, crc] = 0
                    table.loc[total_rows, fcs] = 0
                    table.loc[total_rows, crc_diff] = val - \
                        table.loc[total_rows, crc]
                else:
                    index = table.loc[(table.POD_ID == pod_id) & (table.NODE_ID == node_id)
                                      & (table.INTERFACE == interface)].index[0]

                    table.loc[index, crc_diff] = val-table.loc[index, crc]

    if file2_list[0].startswith("#FCS") or file2_list[i].startswith("#FCS"):
        if file2_list[0].startswith("#FCS"):
            start = 1
        elif file2_list[i].startswith("#FCS"):
            start = i+1
        for k in range(start, len(file2_list), 2):
            if len(file2_list[k].strip()) == 0:
                break
            try:
                val = int(
                    re.sub(r"[\n\t]*", "", file2_list[k+1].split(":")[1]))
                key = (re.sub(r"[\n\t]*", "",
                              file2_list[k].split(":")[1])).lstrip()
            except:
                print(colored(
                    "!!!Please ensure the moquery collected are in proper format,please re-run poller script!!!", "yellow"))
                sys.exit(0)
            if "phys" in key:
                interface = (
                    re.search('phys-\[\w*/\d*(/\d*)?\]', key).group().split('-')[1]).replace("[", "")
                interface = interface.replace("]", "")
                pod_id = re.search('pod-\d*', key).group().split('-')[1]
                node_id = re.search('node-\d*', key).group().split('-')[1]
                index = table.loc[(table.POD_ID == pod_id) & (table.NODE_ID == node_id)
                                  & (table.INTERFACE == interface)]
                if index.empty:  # If there are no CRC and FCS occurred in the particular interface, the interface is added to the table only here
                    # Get the total number of rows to append new row
                    total_rows = table.shape[0]
                    table.loc[total_rows, 'POD_ID'] = pod_id
                    table.loc[total_rows, 'NODE_ID'] = node_id
                    table.loc[total_rows, 'INTERFACE'] = interface
                    table.loc[total_rows, crc] = 0
                    table.loc[total_rows, fcs] = 0
                    table.loc[total_rows, crc_diff] = 0
                    table.loc[total_rows, fcs_diff] = val
                else:
                    index = table.loc[(table.POD_ID == pod_id) & (table.NODE_ID == node_id)
                                      & (table.INTERFACE == interface)].index[0]

                    table.loc[index, fcs_diff] = val-table.loc[index, fcs]

#Function to fetch the node name and role
def assign_node():
    try:
        for k in range(0, table.shape[0]):
            node_query = "moquery -c fabricNode -f 'fabric.Node.id==" + \
                '"'+table.loc[k, 'NODE_ID']+'"'+"'"+' | egrep "id|name|role"'
            stdin, stdout, stderr = ssh.exec_command(node_query)
            out = stdout.readlines()
            name = (re.sub(r"[\n\t]*", "",
                           out[1].split(":")[1])).lstrip()
            role = (re.sub(r"[\n\t]*", "",
                           out[3].split(":")[1])).lstrip()
            table.loc[k, 'NODE_NAME'] = name
            table.loc[k, 'NODE_ROLE'] = role
    except:
        print(colored(
            "!!!Please ensure the files are collected from the same APIC as provided in input for this script!!!", "yellow"))
        sys.exit(0)
        

#Function to execute the LLDP/CP neighbor moquery and fill the table
def assign_neighbors():
    global table
    table = table.fillna(0)
    for k in range(0, table.shape[0]):
        if table.loc[k, crc_diff] != 0 or table.loc[k, fcs_diff] != 0:
            lldp_dn = "topology/pod-"+table.loc[k, 'POD_ID']+"/node-" + \
                table.loc[k, 'NODE_ID']+"/sys/lldp/inst/if-[" + \
                table.loc[k, 'INTERFACE']+"]/adj-1"
            lldp_command = "moquery -c lldpAdjEp -f 'lldp.AdjEp.dn==" + \
                '"'+lldp_dn+'"'+"'"+"| egrep '^dn|portIdV|sysName'"
            stdin, stdout, stderr = ssh.exec_command(lldp_command)
            out_lldp = stdout.readlines()
            if len(out_lldp) != 0:
                if table.loc[k, crc_diff] != 0 and table.loc[k, fcs_diff] != 0:
                    table.loc[k, 'NEIGHBOR'] = colored("System:"+(re.sub(r"[\n\t]*", "", out_lldp[2].split(
                        ":")[1])).lstrip()+","+"Interface:"+(re.sub(r"[\n\t]*", "", out_lldp[1].split(":")[1])).lstrip(), 'yellow')
                else:
                    table.loc[k, 'NEIGHBOR'] = "System:"+(re.sub(r"[\n\t]*", "", out_lldp[2].split(
                        ":")[1])).lstrip()+","+"Interface:"+(re.sub(r"[\n\t]*", "", out_lldp[1].split(":")[1])).lstrip()
            else:
                cdp_dn = "topology/pod-"+table.loc[k, 'POD_ID']+"/node-" + \
                    table.loc[k, 'NODE_ID']+"/sys/cdp/inst/if-[" + \
                    table.loc[k, 'INTERFACE']+"]/adj-1"
                cdp_command = "moquery -c cdpAdjEp -f 'cdp.AdjEp.dn==" + \
                    '"'+cdp_dn+'"'+"'"+"| egrep '^dn|devId|portId'"
                stdin, stdout, stderr = ssh.exec_command(cdp_command)
                out_cdp = stdout.readlines()
                if len(out_cdp) != 0:
                    if table.loc[k, crc_diff] != 0 and table.loc[k, fcs_diff] != 0:
                        table.loc[k, 'NEIGHBOR'] = colored("System:"+(re.sub(r"[\n\t]*", "", out_cdp[0].split(
                            ":")[1])).lstrip()+","+"Interface:"+(re.sub(r"[\n\t]*", "", out_cdp[2].split(":")[1])).lstrip(), 'yellow')
                    else:
                        table.loc[k, 'NEIGHBOR'] = "System:"+(re.sub(r"[\n\t]*", "", out_cdp[0].split(
                            ":")[1])).lstrip()+","+"Interface:"+(re.sub(r"[\n\t]*", "", out_cdp[2].split(":")[1])).lstrip()
                else:
                    if table.loc[k, crc_diff] != 0 and table.loc[k, fcs_diff] != 0:
                        table.loc[k,
                                  'NEIGHBOR'] = colored("No LLDP /CDP neighbours found please check physically where this interface connects", 'yellow')
                    else:
                        table.loc[k,
                                  'NEIGHBOR'] = "No LLDP /CDP neighbours found please check physically where this interface connects"
        else:
            table.loc[k, 'NEIGHBOR'] = ""

#Function to fill the error source column
def assign_type():
    global table
    for k in range(0, table.shape[0]):
        if table.loc[k, fcs_diff] != 0:
            table.loc[k,'ERROR SOURCE']='Local'
        elif table.loc[k, crc_diff] != 0 and table.loc[k, fcs_diff] == 0:
            table.loc[k,'ERROR SOURCE']='Stomp'
        else:
            table.loc[k,'ERROR SOURCE']='Historic'


#Function to sort the table further
def sort_options():
    global table
    while(True):
        print("----------------------------------------------------------------")
        print("Please select any number below to sort the data further or to exit")
        print("1.Sort by the column in descending order", crc)
        print("2.Sort by the column in descending order ", crc_diff)
        print("3.Sort by the column in descending order ", fcs)
        print("4.Sort by the column in descending order", fcs_diff)
        print('5.Exit')
        num = int(input('Input the number: '))
        if num == 1:
            table = table.sort_values(crc, ascending=False)
            print(tabulate(table,
                           headers=table.columns.tolist(), tablefmt='pretty', showindex=False))
        if num == 2:
            table = table.sort_values(crc_diff, ascending=False)
            print(tabulate(table,
                           headers=table.columns.tolist(), tablefmt='pretty', showindex=False))
        if num == 3:
            table = table.sort_values(fcs, ascending=False)
            print(tabulate(table,
                           headers=table.columns.tolist(), tablefmt='pretty', showindex=False))
        if num == 4:
            table = table.sort_values(fcs_diff, ascending=False)
            print(tabulate(table,
                           headers=table.columns.tolist(), tablefmt='pretty', showindex=False))
        if num == 5:
            return

#Function to view the granular data of the interfaces
def granular_view():
    inp = 1
    global date_list
    global sorted_files
    while(inp == 1):
        flag = 0
        print("---------------------------------------------------------------------------")
        try:
            interface = input(
                "Enter an interface for which you need granular data(POD_ID-NODE_ID-INTERFACE  Example:1-101-eth1/5): ")
            print(
                "----------------------------------------------------------------------")
            # Check whether the user gave the input in specified format
            if not(bool(re.match("\d+-\d+-eth\d+/\d+", interface))):
                raise InvalidInterface
        except InvalidInterface:
            print(colored("!!!Please enter the interface value in the specified format (POD_ID-NODE_ID-INTERFACE  Example:1-101-eth1/5)!!! ",'yellow'))
            continue
        except KeyboardInterrupt:
                print()
                inp=int(input("Do you want to terminate the program, 1-yes, 0-no (0/1):"))
                if inp==1:
                    sys.exit()
                else:
                    continue
        while(True):
            print("You have CRC and FCS data in the below date range")
            for date_index in range(0, len(date_list)):
                print(str(date_index+1)+"."+str(datetime.strptime(date_list[date_index], '%Y%m%d').date()))
            try:
                date = int(input(
                    "Enter the date for which you need granular data(any number from the above list range(1-"+str(len(date_list))+")): "))
                if date < 1 or date > len(date_list):
                    raise InvalidRangeError
            except InvalidRangeError:
                print("-------------------------------------------------------------")
                print(colored("!!!!Invalid format/value,Please enter any number from the above listed (1-" +
                      str(len(date_list))+")) ",'yellow'))
                print("--------------------------------------------------------------")
                continue
            except KeyboardInterrupt:
                print()
                inp=int(input("Do you want to terminate the program, 1-yes, 0-no (0/1):"))
                if inp==1:
                    sys.exit()
                else:
                    continue
            else:
                break
        filename = str(date_list[date-1])
        df = pd.DataFrame(columns=['Time', 'CRC', 'FCS'])
        row_num = 0
        pod_id = interface.split('-')[0]
        node_id = interface.split('-')[1]
        phy_int = interface.split('-')[2]
        find_dn_crc = "topology/pod-"+pod_id+"/node-"+node_id + \
            "/sys/phys-["+phy_int.lower()+"]/dbgEtherStats"
        find_dn_fcs = "topology/pod-"+pod_id+"/node-"+node_id + \
            "/sys/phys-["+phy_int.lower()+"]/dbgDot3Stats"
        for file in sorted_files:
            if file[0:8] == filename:
                flag = 1  # To check whether a file exists for the given date
                time_val = file[8:]
                time_val = time_val[0]+time_val[1] + \
                    ":"+time_val[2]+time_val[3]
                df.loc[row_num, 'Time'] = time_val
                fp = open(LOCAL_PATH+'CRC_FCS_' +
                          file[0:8]+'_'+file[8:]+'.txt', "r")
                lines = fp.readlines()
                # Below flags to track FCS and CRC Errors
                flag_fcs = 0
                flag_crc = 0
                for i in range(0, len(lines)):
                    if find_dn_crc in lines[i]:
                        flag_crc = 1
                        y_crc = int(
                            re.sub(r"[\n\t]*", "", lines[i-1].split(":")[1]))
                        break
                for i in range(0, len(lines)):
                    if find_dn_fcs in lines[i]:
                        flag_fcs = 1
                        y_fcs = int(
                            re.sub(r"[\n\t]*", "", lines[i+1].split(":")[1]))
                        break
                if(flag_crc == 0 and flag_fcs == 1):
                    df.loc[row_num, 'CRC'] = 0
                    df.loc[row_num, 'FCS'] = y_fcs
                elif(flag_crc == 1 and flag_fcs == 0):
                    df.loc[row_num, 'CRC'] = y_crc
                    df.loc[row_num, 'FCS'] = 0
                elif(flag_crc == 0 and flag_fcs == 0):
                    df.loc[row_num, 'CRC'] = 0
                    df.loc[row_num, 'FCS'] = 0
                else:
                    df.loc[row_num, 'CRC'] = y_crc
                    df.loc[row_num, 'FCS'] = y_fcs
            row_num = row_num+1
        if flag == 1:
            print(tabulate(df, headers=df.columns.tolist(),
                           tablefmt='pretty', showindex=False))
        else:
            print("----------------------------------------------------")
            print("No files found for the given date")
            # Below are the dates available
        print("----------------------------------------------------------------")
        inp = int(input(
            "Do you want to continue viewing the granular data(0/1), 1-yes, 0-no:"))

# Getting the required inputs
ip_address = input("Enter the IP address or DNS Name of APIC: ")
print("__________________________________________________________")
admin_username = input("Enter the username: ")
print("___________________________________________________________")
admin_password = stdiomask.getpass("Enter the password: ")
connect_apic(ip_address, admin_username, admin_password)
print("_____________________________________________________________")
print("Please enter the folder where files are stored")
print("Please make sure we have at least two files exists in the directory where you have saved data ")

#####Checking whether the entered file format is valid ###########################
while(True):
  print("_____________________________________________________________")
  print("VALID folder format:")
  
  print("EXAMPLE:")
  print("Windows-> C:\\Users\Admin\Desktop\ACI\\")
  print("MAC -> /Users/admin/Desktop/ACI/")
  print("--------------------------------------------------------------------------------------------")
  print("PLEASE NOTE that data collection and script execution might get impacted if folder format is not as above")
  print("--------------------------------------------------------------------------------------------------------")
  try:
   LOCAL_PATH = input(
    "Enter the absolute path of the folder where the files are stored:")
   
   if sys.platform.startswith('win') and not(LOCAL_PATH.endswith('\\')):
       raise InvalidFileFormatError
   if sys.platform.startswith('darwin') and not(LOCAL_PATH.endswith('/')):
       raise InvalidFileFormatError
   files = [file for file in os.listdir(LOCAL_PATH) if file.startswith('CRC_FCS')]
  except InvalidFileFormatError:
   print(colored("!!!Invalid folder format, please enter valid path",'yellow'))
  except KeyboardInterrupt:
                print()
                inp=int(input("Do you want to terminate the program, 1-yes, 0-no (0/1):"))
                if inp==1:
                    sys.exit()
                else:
                    continue
  except:
   print(colored("!!!The system cannot find the path specified, please check the folder format or the folder exists",'yellow'))
  else:
   break
       
#########Condition to check if no files are found ########################
if len(files) == 0:
    print(colored("!!!Please validate the folder path or run script-1 to gather CRC_FCS data!!!",'yellow'))
    ssh.close()
    sys.exit()
else:
    print("___________________________________________________________")
    print("You have CRC and FCS for the below date range")


    index = 1
    date_list = []
    #Sorting the files based on date&time
    sorted_files = sorted(
        [int(file.split('_')[2]+(file.split('_')[3].split('.')[0])) for file in files])
    sorted_files = [str(x) for x in sorted_files]
    for file in sorted_files:
        date = file[0:8]
        if date not in date_list:
            print(str(index)+"."+str(datetime.strptime(date, '%Y%m%d').date()))
            date_list.append(date)
            index = index+1
    
    ###########If multiple dates are avilable asking the user to select start and end date, else fetch from the same date########
    if(len(date_list) > 1):
        print("------------------------------------------------------------------")
        print("If you want data for same start and end date, enter the same value in below two inputs")
        while(True):
            print("------------------------------------------------------------")
            try:
                start = int(
                    input("Enter the start date(any number from the above listed (1-"+str(len(date_list))+")): "))
                end = int(
                    input("Enter the end date(any number from the above listed (1-"+str(len(date_list))+")): "))
                if((start >= 1 and start <= len(date_list)) and (end >= 1 and end <= len(date_list))):
                    break
                else:
                    raise InvalidRangeError
            except InvalidRangeError:
                print(colored("Invalid format/value,Please enter any number from the above listed (1-" +
                      str(len(date_list))+")): ",'yellow'))
            except KeyboardInterrupt:
                print()
                inp=int(input("Do you want to terminate the program, 1-yes, 0-no (0/1):"))
                if inp==1:
                    sys.exit()
                else:
                    continue
            except:
                print(colored("Invalid format,Please enter any number from the above listed (1-" +
                      str(len(date_list))+")): ",'yellow'))

            else:
                break
        if start > end:
            start, end = end, start

        print("__________________________________________________________")
        print("Fetching first file of " +
              date_list[start-1]+" and end file of "+date_list[end-1])
    else:
        print("Fetching first and last file of the same date "+date_list[0])

    if(len(sorted_files) == 1):
        start_file = "CRC_FCS_" +sorted_files[0][0:8]+"_"+sorted_files[0][8:]+".txt"
        end_file = start_file = "CRC_FCS_" +sorted_files[0][0:8]+"_"+sorted_files[0][8:]+".txt"
    else:
        if len(date_list)==1: 
            start_files=[x for x in sorted_files if x[0:8]==date_list[0]]
            end_files=[x for x in sorted_files if x[0:8]==date_list[0]]
            start_file="CRC_FCS_" + start_files[0][0:8]+"_"+start_files[0][8:]+".txt"
            end_file="CRC_FCS_" + end_files[-1][0:8]+"_"+end_files[-1][8:]+".txt"
        else:
        ##Getting the first file of start date and last file of end date
            start_files=[x for x in sorted_files if x[0:8]==date_list[start-1]]
            end_files=[x for x in sorted_files if x[0:8]==date_list[end-1]]
            start_file="CRC_FCS_" + start_files[0][0:8]+"_"+start_files[0][8:]+".txt"
            end_file="CRC_FCS_" + end_files[-1][0:8]+"_"+end_files[-1][8:]+".txt"

    print(start_file)
    print(end_file)

    print("__________________________________________________________")
    print("The script is executing.....")
    # Function to compare and parse the selected files
    compare_the_output(start_file, end_file)
    ssh.close()
    sys.exit()
