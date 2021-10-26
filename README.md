# ACI-FCS-CRC Checker


**Overview:**  
The purpose of this script is to capture ports generating CRC or FCS errors in ACI domain.  
ACI switches run in cut-through switching mode. Whenever switch receives corrupt frame, it stomps the packet and keeps forwarding it.  
If the error gets generated in ACI itself, then it stomps the packet; as well adds FCS Error counter.  
If interface only has CRC counters, then it could be because of stomped packets and is usually not the source of error.  
Reference Document on ACI CRC+FCS Error Troubleshooting: https://techzone.cisco.com/t5/Application-Centric/Troubleshooting-CRC-and-Input-Output-Errors-on-ACI/ta-p/1321321  

---

**Prerequisites on client machine from where script will be executed:**  

1. Python3  
2. Network access to ACI Domain  
3. ACI_CRC_requirements.txt attached to be installed in client machine.  
  
        Follow below steps to install requirements.txt:  
        1. Download requirements.txt  
        2. Open terminal window  
        3. Navigate to folder where requirements.txt is located and run below command:  
            #pip install -r ACI_CRC_requirements.txt  


---

**Script tested on:**  

*  Windows-10 64Bit  
*  MAC Bigsur  

  

---

**Execution:**

FCS and CRC counter detail needs to be collected at periodic interval to see if errors are historic or live.  

Script execution is divided in two parts where,  
1.	script-1(Poller) will collect CRC+FCS error data in files every five minutes for maximum upto seven days of duration.  
2.	script-2(Parser) will analyse these outputs and give tabular output listing interfaces which are source of Error, as well interfaces which are just forwarding the stomped packets. It will also display LLDP neighbour of the interfaces having FCS and/or CRC increments.
    Additionally, one can also review more granular data on specific interface by giving relevant inputs.  

_Make sure you have all the pre-requisites installed in system_


**Execution sequence:**  

**Script-1:**  

    Execute " ACI_CRC_Poller.py" to collect CRC+FCS errors in domain.  
        
    Inputs:
        1. ACI Domain IP /FQDN, Username and password
        2. Path to the folder where you want to save files  
                VALID folder format:  
                EXAMPLE:  
                    Windows-> C:\Users\Admin\Desktop\ACI\   
                    MAC -> /Users/admin/Desktop/ACI/  
    **PLEASE NOTE that data collection and script execution might get impacted if folder format is not as above. Also make sure that folder where you want to save files already exists**  
            
        3. Duration for which you want to run the script:  
                Maximum allowed duration is upto seven days 
                Minimum valid duration is 5minutes. Even if user enters duration lesser than 5-minutes, script will run for 5-minutes and collect data in two files at the interval of 5-minutes.  
    **Script collects FCS+CRC error every five minutes and saves data to files at the path specified in earlier input. It will collect data for the duration given in this input**  
    
    	
**Script-2:**  
_Keep your terminal sesssion font resolution to 100% for proper tabular output view_

    "ACI_CRC_Parser.py" will analyse the data and give you tabular output with interfaces having error.  
    Interfaces which are source of the error are highlighted in yellow colour.  
    Script-2 execution can be started once we have at-least two files to compare data.
    i.e. script-2 execution can be started atleast after 10 minutes of script-1 execution.  
      
    Inputs:  
        1. ACI Domain IP /FQDN, Username and password
        2. Path where files are stored as a part of script-1 execution

    ** If you have data only for one day, then it will automatically process the data and start generating tabular output.  
    Otherwise, it will display the date range for which you have CRC+FCS data collected and ask you input as below**  
        
        3. Enter Start date and end date
          
    **AT THIS STAGE SCRIPT WILL GIVE YOU INITIAL TABULAR OUTPUT WITH INTERFACES HAVING NON_ZERO CRC+FCS DIFFERENCE.  
    TABLE WILL BE SORTED IN DESCENDING ORDER OF FCS DIFFERENCE.  
    ALSO IT WILL DISPLAY LLDP /CDP NEIGHBOUR INTERFACE.  
    LAST COLUMN WILL UPDATE ERROR TYPE AS  
        LOCAL: INTERFACES WHICH ARE SOURCE OF ERROR.  
        STOMP: INTERFACES WHICH ARE JUST FORWARDING STOMPED PACKETS.  
        HISTORIC: INTERFACES WHERE ERRORS ARE HISTORIC AND ARE NOT OF CONCERN.  
          
      
    ** After displaying initial calculations, it gives further data sorting options, as well more granular output options. 
      
     By default, data is sorted in descending order of FCS Difference.  
     Further table sorting options are by CRC_Difference, Initial_CRC or Initial_FCS value.  
        4. Enter relevant input for data sorting or granular data execution
            
    In case of more granular output, script will ask for:
            4a. Interface for which you want more granular data  
            4b. Date for which you want granular data to be displayed  
    **Granular output will display absolute CRC and FCS values at various time interval for all the time-stamps when data was collected on that particular day**

---
            

**Contributors:** 
- Aditya Kesarwani <adkesarw@cisco.com>
- Devi S <devs2@cisco.com>
- Kallol Bosu <kbosu@cisco.com>
- Krishna Nagavelu <knagavol@cisco.com>
- Ranganatha Raju <ranraju@cisco.com>
- Richita Gajjar <rgajjar@cisco.com>
- Sathvika Kotha <sathkoth@cisco.com>
- Savinder Singh <savsingh@cisco.com>
- Solomon Sudhakar <sosudhak@cisco.com>  
  
**Company:**  
- Cisco Systems, Inc.  

**Version:**  
- v1.0  

**Date:**  
- 28th Sep, 2021  

**Disclaimer:**  
- Code provided as-is.  No warranty implied or included.  Use the code for production at your own risk.