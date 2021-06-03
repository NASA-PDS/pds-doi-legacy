#------------------------------                                                                                                 
# Create XLS to identify if PDS4 Product LIDVID is registered                                                                                                     
#  -- scan XML Product labels in directory
#       -- retrieve:
#            <logical_identifier>urn:nasa:pds:maven.anc</logical_identifier>
#            <version_id>1.10</version_id>
#       -- create URL to scrape Registry web page for LIDVID
#            -- compare registered LIDVID against Product-LIDVID
#  -- write results to XLS
#------------------------------                                                                                                 
#                                                                                                                               
# Revision:                                                                                                                     
#  20171121 - V1: initial version 
#  20190201 - updated from: DOI_LIDVID_is_registered_20190401.py 
#               -- updated to reflect the IAD2 scema
#               -- preserve original IAD1 format
#               -- allow user to specify in which format the XML DOI label is to be written
#  20190418 - updated to add new parameter in Config file: 
#  20191216 - updated to add new <publisher> parameter in Config file
#  20200121 - added code that uses:
#                       -- openpyxl is a Python library to read/write Excel 2010 xlsx/xlsm/xltx/xltm files.
#------------------------------                                                                                                 

#------------------------------                                                                                                 
# Import the Python libraries                                                                                                   
#------------------------------                                                                                                 
import sys                                                                                                                      
import os                                                                                                                       
import shutil                                                                                                                   
import re

import pdsparser

from xml.etree import ElementTree                                                                                               
from lxml import etree as ET
from lxml import html

import requests
from urllib2 import urlopen, URLError
from bs4 import BeautifulSoup

from optparse import OptionParser                                                                                               
from time import gmtime,strftime                                                                                                
from datetime import datetime                                                                                                   

import xlrd
from xlrd.sheet import ctype_text
import xlwt, xlsxwriter

from xlutils.copy import copy

#------------------------------                                                                                                 
# Change to the current working directory                                                                                       
#   which is where the script resides                                                                                           
#------------------------------                                                                                                 
pathname = os.path.dirname(sys.argv[0])                                                                                         
os.chdir(pathname)                                                                                                              
print "running in directory: " + os.getcwd()                                                                                    


#------------------------------
#------------------------------
def GetConfigFileMetaData(filename):
#------------------------------
#------------------------------

    if (not os.path.exists(filename)):
        print "exiting: configuration file not found - " + filename
        sys.exit()

    else:
        #------------------------------
        # Read the metadata in the configuration file
        #------------------------------
        with open(filename, 'rt') as f:
            tree = ElementTree.parse(f)
            doc  = tree.getroot()

        #------------------------------
        # Get the number of options in the config file
        #   <options numOptions="12">
        #------------------------------
        numOptions = tree.getroot().attrib.get("numOptions")
        #print "numOptions = '" + numOptions + "'"

        #------------------------------
        # Populate the dictionary with the options
        #------------------------------
        dict_configList = {}
        dict_configList = dict((e.tag, e.text) for e in doc)

        if (int(numOptions) == len(dict_configList)):
            print "dict_configList: found correct number of options in dictionary: '" + numOptions + "'"
        else:
            print "exiting: dict_configList -- number of options ('" + numOptions + "') doesn't match elements in dictionary: '" + str(len(dict_configList)) + "'"
            sys.exit()

#      for eachElement in dict_configList:
#         print "dict_configList." + eachElement + " == '" + dict_configList.get(eachElement) + "'"

        #------------------------------
        # Populate the dictionary with the fixed_attribute options
        #------------------------------
        e = doc.find("fixed_attributes")
        numOptions = e.attrib.get("numOptions")

        dict_fixedList = {}

        for e in doc.find('fixed_attributes'):
            dict_fixedList[e.tag] = e.text             

        if (int(numOptions) == len(dict_fixedList)):
            print "dict_fixedList: found correct number of options in dictionary: '" + numOptions + "'"
        else:
            print "exiting: dict_fixedList -- number of options ('" + numOptions + "') doesn't match elements in dictionary: '" + str(len(dict_fixedList)) + "'"
            sys.exit()

#      for eachElement in dict_fixedList:
#         print "dict_fixedList." + eachElement + " == '" + dict_fixedList.get(eachElement) + "'"

    return dict_configList, dict_fixedList 


#------------------------------
#------------------------------
def Return_XML_AttrValue(dict_fixedList, xmlText, attr_xpath):
#------------------------------
#------------------------------

    pds_uri = dict_fixedList.get("pds_uri")

    #util.WriteDebugInfo(f_debug,debug_flag,"Append","Return_XML_AttrValue.xmlText: " + xmlText + "\n")
    util.WriteDebugInfo(f_debug,debug_flag,"Append","Return_XML_AttrValue.attr_xpath: " + attr_xpath + "\n")

    #------------------------------
    # Populate the xml attribute with the specified value
    #------------------------------
    from lxml import etree
    doc = ET.fromstring(xmlText)

    elm = doc.xpath(attr_xpath, namespaces={'pds': pds_uri})[0]
    elm_current_value = elm.text

    #------------------------------
    # Return the buffer
    #------------------------------
    return elm_current_value                                                                                                

#------------------------------
def Return_AttrValue_using_xPath(f_debug, debug_flag, root, attr_xpath, stateOptReq):
#------------------------------
# 20170513: initial version; replacement for: Return_XML_AttrValue    
#------------------------------

    util.WriteDebugInfo(f_debug,debug_flag,"Append","Return_AttrValue_using_xPath.attr_xpath: " + attr_xpath + " as (" + stateOptReq + ")\n")

    #------------------------------
    # Populate the xml attribute with the specified value
    #------------------------------
    try:
        elm = root.xpath(attr_xpath, namespaces=dict_namespaces)[0]
        elm_current_value = elm.text
        util.WriteDebugInfo(f_debug,debug_flag,"Append","Return_AttrValue_using_xPath.elm_current_value: " + elm_current_value + "\n")
        
    except:
        if (stateOptReq == "optional"):
            elm_current_value = None
            util.WriteDebugInfo(f_debug,debug_flag,"Append","Return_AttrValue_using_xPath.elm_current_value (optional attribute): None\n")
            
        elif (stateOptReq == "required"):
            print ("Return_AttrValue_using_xPath.elm_current_value (required attribute): not Found -- exiting\n")
            sys.exit()
        else:
            util.WriteDebugInfo(f_debug,debug_flag,"Append","WARNING: Return_AttrValue_using_xPath.attr_xpath: " + attr_xpath + " was not found Prod_XML\n")
            
            print ("Return_AttrValue_using_xPath.stateOptReq -- invalid value of: '" + stateOptReq + "'\n")
            sys.exit()
            
    #------------------------------
    # Return the value of the xPath attribute
    #------------------------------
    return elm_current_value


#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Populate_DOI_XML_with_values(dict_fixedList, xmlText, attr_xpath, value):                                      
#------------------------------      
# 20171207 -- DOI XML doesn't use namespace
#------------------------------                                                                                                 

    util.WriteDebugInfo(f_debug,debug_flag,"Append","Populate_DOI_XML_with_values.xmlText: " + xmlText + "\n")                                
    util.WriteDebugInfo(f_debug,debug_flag,"Append","Populate_DOI_XML_with_values.attr_xpath: " + attr_xpath + "\n")                           
    util.WriteDebugInfo(f_debug,debug_flag,"Append","Populate_DOI_XML_with_values.value: " + value + "\n")                           

    #------------------------------                                                                                             
    # Populate the xml attribute with the specified value                                                                       
    #------------------------------                                                                                             
    from lxml import etree                                                                                                      
    doc = ET.fromstring(xmlText)                                                                                             

    #elm = doc.xpath(attr_xpath, namespaces={'pds': pds_uri})[0] 
    
    #doi_xPath = "/records/record[1]/title[1]"
    elm = doc.xpath(attr_xpath)[0]                                                              
    #elm_current_value = elm.text                                                                                               

    elm.text = value                                                                                                            

    sOutText = ET.tostring(doc)                                                                                              

    #------------------------------                                                                                             
    # Return the buffer                                                                                                         
    #------------------------------                                                                                             
    return sOutText                                                                                                             


#------------------------------
#------------------------------
def Return_DOI_date(f_debug, debug_flag, prodDate):
#------------------------------
# 20171207 -- prodDate -- date in: <modification_date>2015-07-14</modification_date>
#              doiDate -- date formatted as: 'yyyy-mm-dd'
# 20200431 -- not used / referenced
#------------------------------

    doiDate = datetime.strptime(prodDate, '%Y-%m-%d').strftime('%m/%d/%Y') 

    return doiDate


#------------------------------                                                                                                 
#------------------------------                                                                                                 
def ReturnRelativePathAndFileName(rootPath, pathName):                                                                          
#------------------------------                                                                                                 
#-------------------------                                                                                                      

    RelPath = ""                                                                                                                
    FileName = ""                                                                                                               

    #------------------------------                                                                                             
    # establish the path for the working directory                                                                              
    #  -- C:\\test\test.xml                                                                                                     
    #------------------------------                                                                                             
    util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.rootPath: " + rootPath + "\n")                          

    #------------------------------                                                                                             
    # Remove the working directory from the Path&FileName                                                                       
    #   --- residual is either just a filename or child subdirectories and a filename                                           
    #------------------------------                                                                                             
    a = pathName.replace(rootPath, "")                                                                                          
    util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.a: " + a + "\n")                                        

    #------------------------------                                                                                             
    # Check is there are 1 or more child directories                                                                            
    #------------------------------                                                                                             
    if (chr(92) in a):                                                                                                          
        fields = a.split(chr(92))                                                                                               

        iFields = len(fields)                                                                                                   
        util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.iFields: " + str(iFields) + "\n")                   

        if (iFields == 2):                                                                                                      
            util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.iFields == 2\n")                                
            RelPath = ""                                                                                                        
            FileName = fields[1]                                                                                                
        elif (iFields == 3):                                                                                                    
            util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.iFields == 3\n")                                
            RelPath = fields[1]                                                                                                 
            FileName = fields[2]                                                                                                
        elif (iFields > 3):                                                                                                     
            util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.iFields > 3\n")                                 
            FileName = fields[iFields-1]                                                                                        
            RelPath = fields[1] + chr(92)                                                                                       

            iCount  = 0                                                                                                         

            for eachField in fields:                                                                                            
                if (iCount > 1) and (iCount < iFields-1):                                                                       
                    RelPath += fields[iCount]                                                                                   

                    util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.iCount: " + str(iCount) + "\n")         
                    util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.RelPath: " + RelPath + "\n")            

                    #------------------------------                                                                             
                    # No trailing file delimiter                                                                                
                    #------------------------------                                                                             
                    if (iCount < (iFields-2)):                                                                                  
                        RelPath += chr(92)                                                                                      

                iCount += 1                                                                                                     

    else:                                                                                                                       
        RelPath = ""                                                                                                            
        FileName = a                                                                                                            

    util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.RelPath: " + RelPath + "\n")                            
    util.WriteDebugInfo(f_debug,debug_flag,"Append","ReturnRelativePathAndFileName.FileName: " + FileName + "\n")                          

    return RelPath, FileName                                                                                                    

#------------------------------                                                                                                 
#------------------------------                                                                                                 
def parse_table(table):
#------------------------------                                                                                                 
# Source:
#   -- https://codereview.stackexchange.com/questions/60769/scrape-an-html-table-with-python
#------------------------------  
    
    #------------------------------                                                                                     
    # Get metadata from table                                                                                                
    #   -- return results as List
    #------------------------------                                                                                     

    return [
        [cell.get_text().strip() for cell in row.find_all(['th', 'td'])]
           for row in table.find_all('tr')
    ]



#------------------------------
#------------------------------
def CreateResultsDir_and_File(f_debug, debug_flag, appBasePath):
#------------------------------
#------------------------------

    #------------------------------
    # Create the file that logs the Processing History
    #   --- create a new file each time script is executed
    #   --- open the file in 'append' mode as the script continually appends data to the file
    #------------------------------
    #------------------------------
    # Create an output directory for the Processed XML files to reside
    #------------------------------
    dir = os.path.join(appBasePath,"aaaResultsFiles")
    
    if not os.path.exists(dir):
        os.makedirs(dir)
    
    sInventoryName = "aaProcessingLog_" + strftime("%Y%m%d", gmtime()) + ".txt"
    InventoryPathName = os.path.join(dir, sInventoryName)
    
    if not os.path.isfile(InventoryPathName):
        f_inventory = open(InventoryPathName,"a")
    else:
        count = 0
        while (os.path.isfile(InventoryPathName)):
            count += 1
            sInventoryName = "aaProcessingLog_" + strftime("%Y%m%d", gmtime()) + "-" + str(count) + ".txt"
            InventoryPathName = os.path.join(dir, sInventoryName)
            
    #------------------------------
    # Open & Initialize the RESULTS file
    #------------------------------
    f_results = open(InventoryPathName,"a")
    
    f_results.write("Main_Initialize\n")
    f_results.write(">> processing started at: " + str(datetime.now()) + "\n\n")
        
    return f_results, InventoryPathName


#------------------------------
#------------------------------
def Return_nonDuplicate_FileName(f_debug, debug_flag, DOI_directory_PathName, sInventoryName):
#------------------------------
#------------------------------

    fileDestination = os.path.join(DOI_directory_PathName, sInventoryName)                                                               

    #------------------------------
    # Ensure the file (to be created)  does not already exist
    #------------------------------    
    if not os.path.isdir(InventoryPathName):
        os.makedirs(InventoryPathName)                                                                                                        

    else:        
        count = 0
        while (os.path.exists(fileDestination)):
            count += 1
            sInventoryName_test = sInventoryName + "-" + str(count)
            InventoryPathName = os.path.join(DOI_directory_PathName, sInventoryName_test)
        
            if not os.path.exists(InventoryPathName):
                break
        
    return InventoryPathName


#------------------------------
#------------------------------
def CreateDOI_Dir(f_debug, debug_flag, appBasePath):
#------------------------------
#------------------------------

    #------------------------------
    # Create the file that logs the Processing History
    #   --- create a new file each time script is executed
    #   --- open the file in 'append' mode as the script continually appends data to the file
    #------------------------------
    #------------------------------
    # Create an output directory for the Processed XML files to reside
    #------------------------------
    dir = os.path.join(appBasePath,"aaaDOI_GeneratedFiles")

    sInventoryName = "aaDOI_files_" + strftime("%Y%m%d", gmtime())
    InventoryPathName = os.path.join(dir, sInventoryName)
    
    if not os.path.isdir(InventoryPathName):
        os.makedirs(InventoryPathName)                                                                                                        

    else:        
        count = 0
        while (os.path.exists(InventoryPathName)):
            count += 1
            sInventoryName = "aaDOI_files_" + strftime("%Y%m%d", gmtime()) + "-" + str(count)
            InventoryPathName = os.path.join(dir, sInventoryName)
        
            if not os.path.exists(InventoryPathName):
                os.makedirs(InventoryPathName) 
                break
        
    return InventoryPathName


#------------------------------                                                                                                 
def Process_IAD2_ODL_DataSet_metadata(dict_fixedList, dict_configList, dict_ConditionData, dict_odl, FileName, eachFile):                                              
#------------------------------                                                                                                 
# 20200602: initial version
# 20200630: changed from: "https://pds.jpl.nasa.gov" >> "https://pds.nasa.gov"
# 20210408:- added code to capture and report if ODL doesn't have  ["DATA_SET_TERSE_DESC"] as description
#------------------------------                                                                                                 
    
    #------------------------------
    # Read the IM Test_Case manifest file
    #   -- for each <test_case>; get dictionary of metadata
    #
    #  dict{0: (tuple),
    #       1: (tuple)}
    #
    # intialize the items in the dictionary to defaults:
    #
    #------------------------------
    #  dict_ConditionData[FileName]["title"]
    #  dict_ConditionData[FileName]["accession_number"]
    #  dict_ConditionData[FileName]["publication_date"]
    #  dict_ConditionData[FileName]["description"]
    #  dict_ConditionData[FileName]["site_url"]
    #  dict_ConditionData[FileName]["product_type"]
    #  dict_ConditionData[FileName]["product_type_specific"]
    #  dict_ConditionData[FileName]["date_record_added"]
    #  dict_ConditionData[FileName]["authors"]
    #  dict_ConditionData[FileName]["contributors"] 
    #  dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"]
    #  dict_ConditionData[FileName]["keywords"]
    #------------------------------          
    dict_ConditionData[FileName] = {}
    
    dict_ConditionData[FileName]["title"] = ""
    dict_ConditionData[FileName]["accession_number"] = ""
    dict_ConditionData[FileName]["publication_date"] = ""
    dict_ConditionData[FileName]["description"] = ""
    dict_ConditionData[FileName]["site_url"] = ""
    dict_ConditionData[FileName]["product_type"] = ""
    dict_ConditionData[FileName]["product_type_specific"] = ""
    dict_ConditionData[FileName]["date_record_added"] = ""
    dict_ConditionData[FileName]["authors"] = ""
    dict_ConditionData[FileName]["contributors"]  = ""
    dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"] = ""
    dict_ConditionData[FileName]["keywords"] = ""

    util.WriteDebugInfo(f_debug,debug_flag,"Append","MAIN.Process_IAD2_ODL_metadata\n")                                         
    print " -- processing PDS3 DataSet label file: " + eachFile
    
    #------------------------------
    # Initialize the various URIs 
    #------------------------------ 
    sString = dict_odl["DATA_SET"]["DATA_SET_INFORMATION"]["DATA_SET_NAME"]
    sString = sString.replace("\n", "").replace("  ", "")

    dict_ConditionData[FileName]["title"] = sString
    dict_ConditionData[FileName]["accession_number"] =  dict_odl["DATA_SET"]["DATA_SET_ID"]
    dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"] = dict_odl["DATA_SET"]["DATA_SET_ID"]

    PubDate_value = str(dict_odl["DATA_SET"]["DATA_SET_INFORMATION"]["DATA_SET_RELEASE_DATE"])
    lenPubDate = len(PubDate_value)
    
    #------------------------------
    # <publication_date> is year only
    #------------------------------
    if (lenPubDate == 4):
        PubDate_value = PubDate_value + "-01-01"
    else:
        #------------------------------
        # <publication_date> -- <publication_date>
        #      -- check for yyyy-doy or yyyy-mm-dd
        #      -- attempt to convert the date in XML label to OSTI format (yyyy-mm-dd)
       #------------------------------
        PubDate_value = util.Return_StringDateTime_from_AnyStringDateTime(PubDate_value, "%Y-%m-%d")
                
    dict_ConditionData[FileName]["publication_date"] = PubDate_value                                             
    dict_ConditionData[FileName]["date_record_added"] = str(datetime.now().strftime("%Y-%m-%d"))   
    
    try:
        dict_ConditionData[FileName]["description"] =  dict_odl["DATA_SET"]["DATA_SET_INFORMATION"]["DATA_SET_TERSE_DESC"]
    except:
        dict_ConditionData[FileName]["description"] =  "Null"
        list_ODL_no_DS_Terse.append (eachFile)
        
    #dict_ConditionData[FileName]["site_url"] = "https://pds.jpl.nasa.gov/ds-view/pds/viewDataset.jsp?dsid=" + dict_odl["DATA_SET"]["DATA_SET_ID"]
    dict_ConditionData[FileName]["site_url"] = "https://pds.nasa.gov/ds-view/pds/viewDataset.jsp?dsid=" + dict_odl["DATA_SET"]["DATA_SET_ID"]
    dict_ConditionData[FileName]["product_type"] = "Collection"
    dict_ConditionData[FileName]["product_type_specific"] = "PDS3 DataSet Catalog"
    
    #------------------------------
    # <publisher> -- <author_list>
    #      -- convert multi-value to string:  "J.Smith; A.Raugh"
    #------------------------------
    list_sequence =  dict_odl["DATA_SET"]["DATA_SET_INFORMATION"]["PRODUCER_FULL_NAME"]
    dict_ConditionData[FileName]["authors"] = Return_String_from_ODL_Series(list_sequence)  
    
    dict_ConditionData[FileName]["contributors"]  = ""
    
    #------------------------------
    # Initialize the List of <keywords> value
    #------------------------------
    list_keyword_values = []

    list_sequence = dict_odl["DATA_SET"]["DATA_SET_TARGET"]["TARGET_NAME"]
    list_keyword_values.append(Return_String_from_ODL_Series(list_sequence) )

    list_sequence = dict_odl["DATA_SET"]["DATA_SET_HOST"]["INSTRUMENT_HOST_ID"]
    list_keyword_values.append(Return_String_from_ODL_Series(list_sequence) )

    list_sequence = dict_odl["DATA_SET"]["DATA_SET_HOST"]["INSTRUMENT_ID"]
    list_keyword_values.append(Return_String_from_ODL_Series(list_sequence) )

    list_sequence = dict_odl["DATA_SET"]["DATA_SET_REFERENCE_INFORMATION"]["REFERENCE_KEY_ID"]
    list_keyword_values.append(Return_String_from_ODL_Series(list_sequence) )

    #list_keyword_values.append(dict_odl["DATA_SET"]["DATA_SET_TARGET"]["TARGET_NAME"])
    #list_keyword_values.append(dict_odl["DATA_SET"]["DATA_SET_HOST"]["INSTRUMENT_HOST_ID"])
    #list_keyword_values.append(dict_odl["DATA_SET"]["DATA_SET_HOST"]["INSTRUMENT_ID"])
    #list_keyword_values.append(dict_odl["DATA_SET"]["DATA_SET_REFERENCE_INFORMATION"]["REFERENCE_KEY_ID"])

    dict_ConditionData[FileName]["keywords"] = Return_keyword_values(dict_configList, list_keyword_values)
        
    #------------------------------
    # Found all attributes, captured all metadata in Dictionary
    #------------------------------
    return dict_ConditionData, list_ODL_no_DS_Terse


#------------------------------                                                                                                 
def Return_String_from_ODL_Series(list_sequence):                                                  
#------------------------------                                                                                                 
# 20200617: initial version
#------------------------------                                                                                                 

    sString = list_sequence
    
    if (isinstance(list_sequence, list)):
        sString = "; ".join(str(x) for x in list_sequence)

    return sString


#------------------------------                                                                                                 
def Process_IAD2_ProductLabel_metadata(dict_fixedList, dict_configList, dict_ConditionData, eachFile, FileName):                                              
#------------------------------                                                                                                 
# 20200310: initial version
# 20200414: modified dict_ConditionData to capture fill list of <authors> & <contributors>
# 20210202L modified url from "pds.jpl.nasa.gov" to "pds.nasa.gov"
#------------------------------                                                                                                 

    pds_uri    = dict_fixedList.get("pds_uri")
    pds_uri_string = "{" + pds_uri + "}"

    #------------------------------
    # Read the IM Test_Case manifest file
    #   -- for each <test_case>; get dictionary of metadata
    #
    #  dict{0: (tuple),
    #       1: (tuple)}
    #
    # intialize the items in the dictionary to defaults:
    #
    #------------------------------
    #  dict_ConditionData[FileName]["title"]
    #  dict_ConditionData[FileName]["accession_number"]
    #  dict_ConditionData[FileName]["publication_date"]
    #  dict_ConditionData[FileName]["description"]
    #  dict_ConditionData[FileName]["site_url"]
    #  dict_ConditionData[FileName]["product_type"]
    #  dict_ConditionData[FileName]["product_type_specific"]
    #  dict_ConditionData[FileName]["date_record_added"]
    #  dict_ConditionData[FileName]["authors"]
    #  dict_ConditionData[FileName]["contributors"] 
    #  dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"]
    #  dict_ConditionData[FileName]["keywords"]
    #------------------------------          
    dict_ConditionData[FileName] = {}
    
    dict_ConditionData[FileName]["title"] = ""
    dict_ConditionData[FileName]["accession_number"] = ""
    dict_ConditionData[FileName]["publication_date"] = ""
    dict_ConditionData[FileName]["description"] = ""
    dict_ConditionData[FileName]["site_url"] = ""
    dict_ConditionData[FileName]["product_type"] = ""
    dict_ConditionData[FileName]["product_type_specific"] = ""
    dict_ConditionData[FileName]["date_record_added"] = ""
    dict_ConditionData[FileName]["authors"] = ""
    dict_ConditionData[FileName]["contributors"]  = ""
    dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"] = ""
    dict_ConditionData[FileName]["keywords"] = ""

    util.WriteDebugInfo(f_debug,debug_flag,"Append","MAIN.Process_IAD2_ProductLabel_metadata\n")                                         
    print " -- processing Product label file: " + eachFile
    
    ##------------------------------
    ## Read the XML label
    ##   -- generate a DICT of the identified namespaces in the XML preamble
    ##         -- etree XML parser errors if encounters 'Null' namespace; so delete from DICT
    ##------------------------------
    #global dict_namespaces
    #dict_namespaces = xmlUtil.return_NameSpaceDictionary(f_debug, debug_flag, eachFile)
    
    #------------------------------
    # Open the XML label 
    #   --  ElementTree supports 'findall' using dict_namespaces and designation of instances
    #   -- etree doesn't support designation of instances
    #         -- eg: ".//pds:File_Area_Observational[1]/pds:Table_Delimited[1]/pds:Record_Delimited/pds:maximum_record_length"
    #------------------------------
    try:  
        tree = ET.parse(eachFile)
        xmlProd_root = tree.getroot()
        
    except ET.ParseError as err:
        sString = "  -- ABORT: the xml 'Product label; file (%s) could not be parsed\n" % (eachFile)                
        print (sString)
        sString = "      -- %s\n" % (err)
        print (sString)
        sys.exit()
        
    else:                      
        #------------------------------
        #------------------------------
        # Iterate over each <test_case> specified in the TC Manifest file
        #    -- for each <test_case>; use the metadata to:
        #         -- create a PDS4 XML label 
        #         -- modify the 'template' using the xpath and value_settings
        #         -- create the XML output label file
        #
        # Each TestCase consists of the following metadata:
        #   -- test_case name: unique identifier of the <test_case>
        #   -- state: isValid | notValid; indicates if values in test-case are either valid or not
        #   -- <conditions>; values must be paired:
        #        -- xpath: xPath of XML attribute to be modified 
        #        -- value_set: Value or set of values to overwrite value in xPath
        #   -- inFile: XML template to use for modifying metadata
        #   -- outFile: PDS4 XML file to be written as TestCase
        #
        #------------------------------
        #------------------------------

        #------------------------------
        # Initialize the various URIs 
        #------------------------------ 
        objIdentArea_uri  = pds_uri_string + "Identification_Area"
        objBundle_uri     = pds_uri_string + "Bundle"
        objCollection_uri = pds_uri_string + "Collection"
        isBundle          = False
        isCollection      = False

        objLID_uri       = pds_uri_string + "logical_identifier"
        objVID_uri       = pds_uri_string + "version_id"                                                    
        objTitle_uri     = pds_uri_string + "title"
        objProdClass_uri = pds_uri_string + "product_class" 
        objPubYear_uri   = pds_uri_string + "publication_year"
        objPubDate_uri   = pds_uri_string + "modification_date"
        objDescript_uri  = pds_uri_string + "description" 
        objAuthList_uri  = pds_uri_string + "author_list" 
        objEditorList_uri  = pds_uri_string + "editor_list" 
        
        #------------------------------
        # Initialize the Class and Attribute URIs for discovering <keywords>
        #------------------------------ 
        objInvestigArea_uri    = pds_uri_string + "Investigation_Area"
        objCitationInfo_uri    = pds_uri_string + "Citation_Information"
        objObsSysCompArea_uri  = pds_uri_string + "Observing_System_Component"
        objTargetIdentArea_uri = pds_uri_string + "Target_Identification" 
        objPrimResSumArea_uri  = pds_uri_string + "Primary_Result_Summary" 
        objSciFacetsArea_uri   = pds_uri_string + "Science_Facets" 
                
        objName_uri      = pds_uri_string + "name"
        objProcLevel_uri = pds_uri_string + "processing_level"
        objDomain_uri    = pds_uri_string + "domain"
        objDiscpName     = pds_uri_string + "discipline_name"
        objFacet1        = pds_uri_string + "facet1"
        objFacet2        = pds_uri_string + "facet2"
        
        #------------------------------
        # Initialize the List of <keywords> value
        #------------------------------
        list_keyword_values = []
        #sString = Return_keyword_values(dict_configList, list_keyword_values)
        #list_keyword_values.append(sString)
        
        #------------------------------
        # Walk the XML looking for <child> elements
        #------------------------------        
        for event, element in ET.iterparse(eachFile, events=("start", "end")):
            #print("%5s, %4s, %s" % (event, element.tag, element.text))

            #------------------------------
            # <Identification_Area>
            #------------------------------
            if (element.tag == objIdentArea_uri):
                if (event == "start"):
                    inIdentArea = True
                           
            #------------------------------
            # <logical_identifier>
            #------------------------------
            if (element.tag == objLID_uri):
                if (event == "start"):
                    LID_value = element.text
    
                    #------------------------------                                                                                     
                    # Convert LID to URL for <site_url>                                                                                       
                    #------------------------------                                                                                     
                    LID_url_value = LID_value.replace(":", "%3A")

            #------------------------------
            # <version_id> -- <product_nos>
            #  -- use <version_id> in <Identification_Area>
            #  -- DO NOT use <version_id> in <Modification_Detail>
            #------------------------------
            if (element.tag == objVID_uri):
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                    
                    if (parentNode.tag == objIdentArea_uri):
                        VID_value = element.text                    
                    
                        #dict_ConditionData[FileName]["product_nos"] = LID_value + "::" + VID_value
                        dict_ConditionData[FileName]["accession_number"]  = LID_value + "::" + VID_value                                                
                        dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"]  = LID_value + "::" + VID_value
                    
            #------------------------------
            # <title> -- <title>
            #------------------------------
            if (element.tag == objTitle_uri):
                if (event == "start"):
                    Title_value = element.text
                    dict_ConditionData[FileName]["title"] = Title_value                                                        

            #------------------------------
            # <product_class> -- <product_type>: Collection | Dataset
            #                 -- <site_url>
            #------------------------------
            if (element.tag == objProdClass_uri):
                if (event == "start"):
                    ProdClass_value = element.text
                    
                    if ("Bundle" in ProdClass_value):
                        isBundle = True
                        #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=" + LID_url_value + "&amp;version=" + VID_value
                        #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=" + LID_url_value + "&version=" + VID_value
                        url_value = "https://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=" + LID_url_value + "&version=" + VID_value

                        dict_ConditionData[FileName]["product_type"] = "Collection"
                        dict_ConditionData[FileName]["product_type_specific"] = "PDS4 Bundle"
                        dict_ConditionData[FileName]["site_url"] = url_value
                        
                        
                    elif ("Collection" in ProdClass_value):                        
                        isCollection = True
                        #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=" + LID_url_value + "&amp;version=" + VID_value
                        #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=" + LID_url_value + "&version=" + VID_value
                        url_value = "https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=" + LID_url_value + "&version=" + VID_value

                        dict_ConditionData[FileName]["product_type"] = "Dataset"
                        dict_ConditionData[FileName]["product_type_specific"] = "PDS4 Collection"
                        dict_ConditionData[FileName]["site_url"] = url_value

                    elif ("Document" in ProdClass_value):                        
                        #print "<product_class> in Product XML label is Document (which is not yet supported): " + ProdClass_value
                        #sys.exit()

                        #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewDocument.jsp?identifier=" + LID_url_value + "&version=" + VID_value
                        url_value = "https://pds.nasa.gov/ds-view/pds/viewDocument.jsp?identifier=" + LID_url_value + "&version=" + VID_value

                        dict_ConditionData[FileName]["product_type"] = "Text"
                        dict_ConditionData[FileName]["product_type_specific"] = "PDS4 Document"
                        dict_ConditionData[FileName]["site_url"] = url_value

                    else:
                        print "ERROR: Process_IAD2_ProductLabel_metadata -- <product_class> in Product XML label not Collection or Bundle or Document: " + ProdClass_value
                        sys.exit()
                                                            
            #------------------------------
            # <publication_year>  -- <publication_date>
            #   -- convert: yyyy to yyyy to yyyy-mm-dd
            #
            #  Convert any stringDateTime to stringDateTime using 'format'
            #      -- stringDateTime == date | date_time
            #
            #  %a   Weekday as locale's abbreviated name.	(e.g., Sun, Mon, ..., Sat) (en_US)
            #  %A	  Weekday as locale's full name.		(e.g., Sunday, Monday, ..., Saturday) (en_US)
            #  %w	  Weekday as a decimal number, where 0 is Sunday and 6 is Saturday. 	(e.g., 0, 1, 2, 3, 4, 5, 6)
            #  %d	  Day of the month as a zero-padded decimal number.		(e.g., 01, 02, ..., 31)
            #  %b	  Month as locale's abbreviated name.		(e.g., Jan, Feb, ..., Dec) (en_US)
            #  %B	  Month as locale's full name.		(e.g., January, February, ..., December) (en_US)
            #  %m	  Month as a zero-padded decimal number.		(e.g., 01, 02, ..., 12)
            #  %y   Year without century as a zero-padded decimal number.		(e.g., 01, 02, ..., 99)
            #  %Y   Year with century as a decimal number.		(e.g., 0001, 0002, ..., 9999)
            #  %H   Hour (24-hour clock) as a zero-padded decimal number.		(e.g., 01, 02, ..., 23)
            #  %I   Hour (12-hour clock) as a zero-padded decimal number.		(e.g., 01, 02, ..., 12)
            #  %p   Locale's equivalent of either AM or PM.		(e.g., AM, PM) (en_US)
            #  %M   Minute as a zero-padded decimal number.		(e.g., 01, 02, ..., 59)
            #  %S   Second as a zero-padded decimal number.		(e.g., 01, 02, ... , 59)
            #  %f   Microsecond as a decimal number, zero-padded on the left.		(e.g., 000000, 000001, ... 999999)
            #  %z   UTC offset in the form of (+/-) HHMM[SS] (empty string if the object is naive).	(empty), 	(e.g., +0000, -0400, +1030)
            #  %Z   Time zone name (empty string if the object is naive).	(empty), 	(e.g., UTC, IST, CST)
            #  %j   Day of the year as a zero-padded decimal number.		(e.g., 001, 002, ..., 366)
            #  %U   Week number of the year (Sunday as the first day of the week) as a zero padded decimal number.
            #  %W   Week number of the year (Monday as the first day of the week) as a decimal number.
            #  %c   Locale's appropriate date and time representation.		(e.g., Tue Aug 16 21:30:00 1988) (en_US)
            #  %x   Locale's appropriate date representation.		(e.g., 08/16/88)(None)
            #  %X   Locale's appropriate time representation.		(e.g., 21:30:00) (en_US)
            #  %%	  A literal "%" character.	(e.g., %)   
            #------------------------------            
            if (element.tag == objPubYear_uri) or (element.tag == objPubDate_uri):
                if (event == "start"):
                    PubDate_value = element.text.strip()
                    lenPubDate = len(PubDate_value)
                    
                    if (lenPubDate == 4):
                        PubDate_value = PubDate_value + "-01-01"
                    else:
                        #------------------------------
                        # <publication_date> -- <publication_date>
                        #      -- attempt to convert the date in XML label to OSTI format (yyyy-mm-dd)
                        #------------------------------
                        PubDate_value = util.Return_StringDateTime_from_AnyStringDateTime(PubDate_value, "%Y-%m-%d")
                        
                        #dt_PubDate = parse(PubDate_value)                   
                        #PubDate_value = dt_PubDate.strftime("%Y-%m-%d")
                        
                    dict_ConditionData[FileName]["publication_date"] = PubDate_value                                             
                    dict_ConditionData[FileName]["date_record_added"] = str(datetime.now().strftime("%Y-%m-%d"))   
                    
            #------------------------------
            # <description> -- <Identification_Area/Citation_Information/description>
            #------------------------------
            if (element.tag == objDescript_uri):
                #------------------------------
                # Get the <xpath> value
                #  -- use <description> in <Bundle> or <Collection>
                #------------------------------
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                
                    if (parentNode.tag == objCitationInfo_uri):                   
                        Descript_value = element.text
                        #Descript_value = word_wrap(Descript_value, width=85, ind1=15, ind2=15, prefix='')
                        
                        dict_ConditionData[FileName]["description"] = Descript_value                                                        

            #------------------------------
            # <author_list> -- <Identification_Area/Citation_Information/author_list>
            #   -- if <author_list> is populated with metadata; add as: <authors>
            #------------------------------
            if (element.tag == objAuthList_uri): 
                #------------------------------
                # Get the <xpath> value
                #  -- use <description> in <Bundle> or <Collection>
                #------------------------------
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                
                    #------------------------------
                    # Parse <author_list>
                    #  -- split author by ';' then split by ',' to get <author_last_name> & <author_first_name>
                    #
                    #  <author_list>French, R. G.; McGhee-French, C. A.; Gordon, M. K.</author_list>
                    #------------------------------                                
                    if (parentNode.tag == objCitationInfo_uri):                   
                        author_list = element.text
                        dict_ConditionData[FileName]["authors"] = author_list
                                                            
            #------------------------------
            # <editor_list> -- <Identification_Area/Citation_Information/editor_list>
            #   -- if <editor_list> is populated with metadata; add as: <contributors>
            #------------------------------
            if (element.tag == objEditorList_uri):
                #------------------------------
                # Get the <xpath> value
                #  -- use <description> in <Bundle> or <Collection>
                #------------------------------
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                
                    #------------------------------
                    # Parse <author_list>
                    #  -- split author by ';' then split by ',' to get <author_last_name> & <author_first_name>
                    #
                    #  <author_list>French, R. G.; McGhee-French, C. A.; Gordon, M. K.</author_list>
                    #------------------------------                                
                    if (parentNode.tag == objCitationInfo_uri):                   
                        editor_list = element.text
                        dict_ConditionData[FileName]["contributors"] = editor_list
                        
                        #dict_ConditionData[FileName]["contributors/contributor/last_name"] = "1-last-name"
                        #dict_ConditionData[FileName]["contributors/contributor/first_name"] = "1-first-name"
                         
                        #if (";" in editor_list):                             
                            #items = editor_list.split(";")
                            
                            #for i in range(len(items)):
                                #items2 = items[i].split(",")

                                #if (i == 0):            
                                    #dict_ConditionData[FileName]["contributors/contributor/last_name"] = items2[0]
                                    #dict_ConditionData[FileName]["contributors/contributor/first_name"] = items2[1]
                                ##else:
                                    ##------------------------------
                                    ## If applicable, add the additional metadata from <author_list>
                                    ##      -- split author by ';' then split by ',' to get <author_last_name> & <author_first_name>
                                    ##
                                    ##  <author_list>French, R. G.; McGhee-French, C. A.; Gordon, M. K.</author_list>
                                    ##
                                    ##  Note that for each addition, the <author> class must be added as "sibling_next"
                                    ##------------------------------                                
                                    ##insert_XML_elements (dict_namespaces, xml_namespace, xmlRoot, parentNode, classAtt_type, SibChild_type, ElementName, ElamentValue)                                
                                    ##dict_ConditionData[FileName]["contributor/last_name"] = items2[0]
                                    ##dict_ConditionData[FileName]["contributor/first_name"] = items2[1]
                        #else:
                            #items2 = editor_list.split(",")

                            #dict_ConditionData[FileName]["contributors/contributor/last_name"] = items2[0]
                            #dict_ConditionData[FileName]["contributors/contributor/first_name"] = items2[1]                            
            #------------------------------
            # <keywords>.name
            #   -- parent is: <Investigation_Area>
            #                 <Observing_System_Component>
            #                 <Target_Identification>
            #------------------------------
            if (element.tag == objName_uri):
                #------------------------------
                # Get the <xpath> value
                #  -- use <name> in any of the above named Parent objects
                #------------------------------
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                
                    if (parentNode.tag == objInvestigArea_uri) or (parentNode.tag == objObsSysCompArea_uri) or (parentNode.tag == objTargetIdentArea_uri):                   
                        keyword_value = element.text
                        
                        # only check for the presence of keyword_value                        
                        if (not (keyword_value in list_keyword_values)):
                            list_keyword_values.append(keyword_value)
                            dict_ConditionData[FileName]["keywords"] = Return_keyword_values(dict_configList, list_keyword_values)
                            
            #------------------------------
            # <keywords>.processing_level
            #   -- parent is: <Primary_Result_Summary>

            #------------------------------
            if (element.tag == objProcLevel_uri):
                #------------------------------
                # Get the <xpath> value
                #  -- use <name> in any of the above named Parent objects
                #------------------------------
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                
                    if (parentNode.tag == objPrimResSumArea_uri):                   
                        keyword_value = element.text
                        
                        if (not (keyword_value in list_keyword_values)):
                            list_keyword_values.append(keyword_value)
                            dict_ConditionData[FileName]["keywords"] = Return_keyword_values(dict_configList, list_keyword_values)
                                            
            #------------------------------
            # <keywords>.science_facets
            #   -- parent is: <Science_Facets>
            #------------------------------
            if (element.tag == objDomain_uri) or (element.tag == objDiscpName) or (element.tag == objFacet1) or (element.tag == objFacet2):
                #------------------------------
                # Get the <xpath> value
                #  -- use <name> in any of the above named Parent objects
                #------------------------------
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                
                    if (parentNode.tag == objSciFacetsArea_uri):                   
                        keyword_value = element.text
                        
                        if (not (keyword_value in list_keyword_values)):
                            list_keyword_values.append(keyword_value)
                            dict_ConditionData[FileName]["keywords"] = Return_keyword_values(dict_configList, list_keyword_values)

    #------------------------------
    # Found all attributes, captured all metadata in Dictionary
    #------------------------------
    return dict_ConditionData


#------------------------------                                                                                                 
def Process_legacy_IAD_ProductLabel_metadata(dict_fixedList, dict_ConditionData, eachFile, FileName):                                              
#------------------------------                                                                                                 
# 20171207: updated version that walks the Product XML label
#              to locate the attributes of interest 
# 20171212: added code to capture <keyword> values in: list_keyword_values
# 20190418: added code for <creators> using: Identification_Area/Citation_Information/author_list
# 20200129: modified dict_ConditionData to be indexed by [fileName]
# 20200303: added code to capture <related_resource> 
#  NOT USED
#------------------------------                                                                                                 

    pds_uri    = dict_fixedList.get("pds_uri")
    pds_uri_string = "{" + pds_uri + "}"

    #------------------------------
    # Read the IM Test_Case manifest file
    #   -- for each <test_case>; get dictionary of metadata
    #
    #  dict{0: (tuple),
    #       1: (tuple)}
    #
    # intialize the items in the dictionary to defaults:
    #
    #------------------------------
    #  dict_ConditionData[FileName]["title"]
    #  dict_ConditionData[FileName]["publication_date"]
    #  dict_ConditionData[FileName]["site_url"]
    #  dict_ConditionData[FileName]["product_type"]
    #  dict_ConditionData[FileName]["product_type_specific"]
    #  dict_ConditionData[FileName]["product_nos"]
    #  dict_ConditionData[FileName]["related_resource"]
    #  dict_ConditionData[FileName]["description"]
    #  dict_ConditionData[FileName]["creators"] 
    #------------------------------          
    dict_ConditionData[FileName] = {}
    
    dict_ConditionData[FileName]["title"] = ""    
    dict_ConditionData[FileName]["publication_date"] = ""
    dict_ConditionData[FileName]["site_url"] = ""
    dict_ConditionData[FileName]["product_type"] = ""
    dict_ConditionData[FileName]["product_type_specific"] = ""
    dict_ConditionData[FileName]["product_nos"] = ""
    dict_ConditionData[FileName]["related_resource"]    
    dict_ConditionData[FileName]["description"] = ""
    dict_ConditionData[FileName]["creators"] = ""

    util.WriteDebugInfo(f_debug,debug_flag,"Append","MAIN.Process_ProductLabel_metadata2\n")                                         
    #print " -- processing Product label file: " + eachFile
    
    #------------------------------
    # Read the XML label
    #   -- generate a DICT of the identified namespaces in the XML preamble
    #         -- etree XML parser errors if encounters 'Null' namespace; so delete from DICT
    #------------------------------
    global dict_namespaces
    dict_namespaces = Return_NameSpaceDictionary(f_debug, debug_flag, eachFile)
            
    #------------------------------
    # Open the XML label 
    #   --  ElementTree supports 'findall' using dict_namespaces and designation of instances
    #   -- etree doesn't support designation of instances
    #         -- eg: ".//pds:File_Area_Observational[1]/pds:Table_Delimited[1]/pds:Record_Delimited/pds:maximum_record_length"
    #------------------------------
    try:  
        tree = ET.parse(eachFile)
        xmlProd_root = tree.getroot()
        
    except ET.ParseError as err:
        sString = "  -- ABORT: the xml 'Product label; file (%s) could not be parsed\n" % (eachFile)                
        print (sString)
        sString = "      -- %s\n" % (err)
        print (sString)
        sys.exit()
        
    else:                      
        #------------------------------
        #------------------------------
        # Iterate over each <test_case> specified in the TC Manifest file
        #    -- for each <test_case>; use the metadata to:
        #         -- create a PDS4 XML label 
        #         -- modify the 'template' using the xpath and value_settings
        #         -- create the XML output label file
        #
        # Each TestCase consists of the following metadata:
        #   -- test_case name: unique identifier of the <test_case>
        #   -- state: isValid | notValid; indicates if values in test-case are either valid or not
        #   -- <conditions>; values must be paired:
        #        -- xpath: xPath of XML attribute to be modified 
        #        -- value_set: Value or set of values to overwrite value in xPath
        #   -- inFile: XML template to use for modifying metadata
        #   -- outFile: PDS4 XML file to be written as TestCase
        #
        #------------------------------
        #------------------------------

        #------------------------------
        # Initialize the various URIs 
        #------------------------------ 
        objIdentArea_uri  = pds_uri_string + "Identification_Area"
        objBundle_uri     = pds_uri_string + "Bundle"
        objCollection_uri = pds_uri_string + "Collection"
        isBundle          = False
        isCollection      = False

        objLID_uri       = pds_uri_string + "logical_identifier"
        objVID_uri       = pds_uri_string + "version_id"                                                    
        objTitle_uri     = pds_uri_string + "title"
        objProdClass_uri = pds_uri_string + "product_class" 
        objPubYear_uri   = pds_uri_string + "publication_year"
        objPubDate_uri   = pds_uri_string + "modification_date"
        objDescript_uri  = pds_uri_string + "description" 
        objAuthList_uri  = pds_uri_string + "author_list" 
        
        #------------------------------
        # Initialize the Class and Attribute URIs for discovering <keywords>
        #------------------------------ 
        objInvestigArea_uri    = pds_uri_string + "Investigation_Area"
        objCitationInfo_uri    = pds_uri_string + "Citation_Information"
        objObsSysCompArea_uri  = pds_uri_string + "Observing_System_Component"
        objTargetIdentArea_uri = pds_uri_string + "Target_Identification" 
        objPrimResSumArea_uri  = pds_uri_string + "Primary_Result_Summary" 
        objSciFacetsArea_uri   = pds_uri_string + "Science_Facets" 
                
        objName_uri      = pds_uri_string + "name"
        objProcLevel_uri = pds_uri_string + "processing_level"
        objDomain_uri    = pds_uri_string + "domain"
        objDiscpName     = pds_uri_string + "discipline_name"
        objFacet1        = pds_uri_string + "facet1"
        objFacet2        = pds_uri_string + "facet2"
        
        #------------------------------
        # Initialize the List of <keywords> value
        #------------------------------
        list_keyword_values = []
        
        #------------------------------
        # Initialize the <publication_date> value
        #   -- use maximum date value
        #------------------------------
        savePubDate_value = ""
        
        #------------------------------
        # Walk the XML looking for <child> elements
        #------------------------------
        
        for event, element in ET.iterparse(eachFile, events=("start", "end")):
            print("%5s, %4s, %s" % (event, element.tag, element.text))

            #------------------------------
            # <Identification_Area>
            #------------------------------
            if (element.tag == objIdentArea_uri):
                if (event == "start"):
                    inIdentArea = True
                           
            #------------------------------
            # <logical_identifier>
            #------------------------------
            if (element.tag == objLID_uri):
                if (event == "start"):
                    LID_value = element.text
    
                    #------------------------------                                                                                     
                    # Convert LID to URL for <site_url>                                                                                       
                    #------------------------------                                                                                     
                    LID_url_value = LID_value.replace(":", "%3A")

            #------------------------------
            # <version_id> -- <product_nos>
            #  -- use <version_id> in <Identification_Area>
            #  -- DO NOT use <version_id> in <Modification_Detail>
            #------------------------------
            if (element.tag == objVID_uri):
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                    
                    if (parentNode.tag == objIdentArea_uri):
                        VID_value = element.text                    
                    
                        dict_ConditionData[FileName]["product_nos"] = LID_value + "::" + VID_value
                        dict_ConditionData[FileName]["related_resource"] = LID_value + "::" + VID_value
                    
            #------------------------------
            # <title> -- <title>
            #------------------------------
            if (element.tag == objTitle_uri):
                if (event == "start"):
                    Title_value = element.text
                    dict_ConditionData[FileName]["title"] = Title_value                                                        

            #------------------------------
            # <product_class> -- <product_type>: Collection | Dataset
            #                 -- <site_url>
            #------------------------------
            if (element.tag == objProdClass_uri):
                if (event == "start"):
                    ProdClass_value = element.text
                    
                    if ("Bundle" in ProdClass_value):
                        isBundle = True
                        #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=" + LID_url_value + "&amp;version=" + VID_value
                        #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=" + LID_url_value + "&version=" + VID_value
                        url_value = "https://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=" + LID_url_value + "&version=" + VID_value

                        dict_ConditionData[FileName]["product_type"] = "Collection"
                        dict_ConditionData[FileName]["product_type_specific"] = "PDS4 Bundle"
                        dict_ConditionData[FileName]["site_url"] = url_value
                        
                        
                    elif ("Collection" in ProdClass_value):                        
                        isCollection = True
                        #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=" + LID_url_value + "&amp;version=" + VID_value
                        #url_value = "https://pds.jpl.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=" + LID_url_value + "&version=" + VID_value
                        url_value = "https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=" + LID_url_value + "&version=" + VID_value

                        dict_ConditionData[FileName]["product_type"] = "Dataset"
                        dict_ConditionData[FileName]["product_type_specific"] = "PDS4 Collection"
                        dict_ConditionData[FileName]["site_url"] = url_value

                    elif ("Document" in ProdClass_value):                        
                        print "ERROR: Process_IAD2_ProductLabel_metadata -- <product_class> in Product XML label is Document (which is not yet supported): " + ProdClass_value
                        sys.exit()

                    else:
                        #print "<product_class> in Product XML label not Collection or Bundle: " + ProdClass_value
                        print "ERROR: Process_IAD2_ProductLabel_metadata -- <product_class> in Product XML label not Collection or Bundle or Document: " + ProdClass_value
                        sys.exit()
                                                            
            #------------------------------
            # <publication_year>  -- <publication_date>
            # <modification_date> -- <publication_date>
            #
            # -- convert: dd/mm/yyyy to yyyy to yyyy-mm-dd
            #------------------------------
            if (element.tag == objPubYear_uri) or (element.tag == objPubDate_uri):
                if (event == "start"):
                    PubDate_value = element.text
                    lenPubDate = len(PubDate_value)
                    
                    if (lenPubDate == 4):
                        PubDate_value = PubDate_value + "-01-01"
                    else:
                        PubDate_value = str(datetime.now().year) + "-01-01"
                        
                    #if (PubDate_value > savePubDate_value):
                        #savePubDate_value = PubDate_value
                        
                    #PubDate_value = Return_DOI_date(f_debug, debug_flag, PubDate_value)
                    dict_ConditionData[FileName]["publication_date"] = PubDate_value                                             
        
            #------------------------------
            # <description> -- <Identification_Area/Citation_Information/description>
            #------------------------------
            if (element.tag == objDescript_uri):
                #------------------------------
                # Get the <xpath> value
                #  -- use <description> in <Bundle> or <Collection>
                #------------------------------
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                
                    if (parentNode.tag == objCitationInfo_uri):                   
                        Descript_value = element.text
                        #Descript_value = word_wrap(Descript_value, width=85, ind1=15, ind2=15, prefix='')
                        
                        dict_ConditionData[FileName]["description"] = Descript_value                                                        

            #------------------------------
            # <creators> -- <Identification_Area/Citation_Information/author_list>
            #------------------------------
            if (element.tag == objAuthList_uri):
                #------------------------------
                # Get the <xpath> value
                #  -- use <description> in <Bundle> or <Collection>
                #------------------------------
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                
                    if (parentNode.tag == objCitationInfo_uri):                   
                        Creators_value = element.text
                         
                        dict_ConditionData[FileName]["creators"] = Creators_value                                                        

            #------------------------------
            # <keywords>.name
            #   -- parent is: <Investigation_Area>
            #                 <Observing_System_Component>
            #                 <Target_Identification>
            #------------------------------
            if (element.tag == objName_uri):
                #------------------------------
                # Get the <xpath> value
                #  -- use <name> in any of the above named Parent objects
                #------------------------------
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                
                    if (parentNode.tag == objInvestigArea_uri) or (parentNode.tag == objObsSysCompArea_uri) or (parentNode.tag == objTargetIdentArea_uri):                   
                        keyword_value = element.text
                        
                        # only check for the presence of keyword_value                        
                        if (not (keyword_value in list_keyword_values)):
                            list_keyword_values.append(keyword_value)
                               
            #------------------------------
            # <keywords>.processing_level
            #   -- parent is: <Primary_Result_Summary>

            #------------------------------
            if (element.tag == objProcLevel_uri):
                #------------------------------
                # Get the <xpath> value
                #  -- use <name> in any of the above named Parent objects
                #------------------------------
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                
                    if (parentNode.tag == objPrimResSumArea_uri):                   
                        keyword_value = element.text
                        
                        if (not (keyword_value in list_keyword_values)):
                            list_keyword_values.append(keyword_value)
                                            
            #------------------------------
            # <keywords>.science_facets
            #   -- parent is: <Science_Facets>
            #------------------------------
            if (element.tag == objDomain_uri) or (element.tag == objDiscpName) or (element.tag == objFacet1) or (element.tag == objFacet2):
                #------------------------------
                # Get the <xpath> value
                #  -- use <name> in any of the above named Parent objects
                #------------------------------
                if (event == "start"):
                    parentNode = next(element.iterancestors())
                
                    if (parentNode.tag == objSciFacetsArea_uri):                   
                        keyword_value = element.text
                        
                        if (not (keyword_value in list_keyword_values)):
                            list_keyword_values.append(keyword_value)

        #------------------------------
        # Found all attributes, captured all metadata in Dictionary
        #------------------------------
        return dict_ConditionData, list_keyword_values
        

#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Process_author_contributor_list(xmlDOI_Text, FileName, dict_value, actionType) :                                              
#------------------------------                                                                                                 
# 20200416 -- new method to process <author> & <editor) list 
#                        -- parse <author> & <contributo> list to capture instances of authors & contributors:
#                              --  <author_list>Berg, O.E.; Williams, D.R.</author_list>
#                              --  <editor_list>Williams, D.R.; McLaughlin, S.A.</editor_list>
#                        -- split <xxx_list> by ';' then split by ',' to get <xxx_last_name> & <xxx_first_name>
#
#  Repeat for each instance:      
#    <authors>
#       <author>
#            <email/>
#            <first_name> A.</first_name>
#            <last_name>Davies</last_name>
#            <affiliations/>
#       </author>
#    </authors>    
#    
#    <contributors>
#       <contributor>
#            <email/>
#            <first_name>D.R.</first_name>
#            <last_name>Williams</last_name>
#            <contributor_type/>
#            <affiliations>
#                <affiliation/>
#            </affiliations>
#        </contributor>    
#    </contributors>
#------------------------------                                                                                                 

    #------------------------------                                                                                                 
    # Begin replacing the metadata in the DOI file with that in Product Label                                                                                 
    #------------------------------
         
    #------------------------------
    # Ascertain the number of instances in either <author_list> or <contributor_list>
    #   -- ascertain values for <last_name> and <first_name>
    #   -- <contributor_type> is static as "Editor"
    #------------------------------    
    list_type =  dict_value.get(actionType)
    
    if (not list_type == "") and (not list_type == "NULL") and (not list_type == "N/A"): 
        items = []
        
        if (";" in list_type):                             
            items = list_type.split(";")
            
        else:
            items = [list_type]
                    
        for i in range(0, len(items)):
            if ("," in items[i]):
                #------------------------------    
                # --  <author_list>Berg, O.E.; Williams, D.R.</author_list>                
                #------------------------------    
                items2 = items[i].split(",")
            
                last_name_value =  items2[0].strip()
                first_name_value = items2[1].strip()
                editor_value = "Editor"
                
            elif (" " in items[i]):
                #------------------------------    
                # Most likely PDS3 <publisher_name> as:
                # --  <author_list>O.E. Berg</author_list>                
                # --  <author_list>Berg, O.E.</author_list>                
                # --  <author_list>Berg, O.E. III</author_list>    
                # -- <author_list>"JUDITH D. FURMAN"</author_list>
                #------------------------------                    
                if ("," in items[i]):
                    items2 = items[i].split(",")
                
                    last_name_value =  items2[0].strip()                    
                    first_name_value = items2[1].strip()
                    
                elif (" " in items[i]):
                    items2 = items[i].split(" ")
                
                    if (len(items2) ==2):  # --  <author_list>O.E. Berg</author_list>                
                        first_name_value = items2[0].strip()
                        last_name_value =  items2[1].strip()
    
                    elif (len(items2) == 3):   # -- <author_list>"JUDITH D. FURMAN"</author_list>
                        first_name_value = items2[0].strip() + " " +  items2[1].strip()
                        last_name_value =  items2[2].strip()
     
                    else:
                        a = len(items2)
                        last_name_value =  items2[a-1].strip()
                        first_name_value = ""
                        
                        for z in range(0, a-1):                           
                            first_name_value += items2[z].strip() + " "                                              
                       
                editor_value = "Editor"

                #------------------------------
                # Log the <author> or <contributor> last_name and first_name values for each FileName
                #------------------------------
                util.WriteLogInfo(f_log,"Append","Process_author_contributor_list - " + FileName + "\n")                                                      
                util.WriteLogInfo(f_log,"Append","    - <last_name>" + last_name_value + "\n")                                                      
                util.WriteLogInfo(f_log,"Append","    - <first_name>" + first_name_value + "\n")                                                      
             
            #------------------------------
            # Create a List to hold instances of a Dictionary that in turn contains the metadata for creating each element in <author> or <contributor>
            #------------------------------
            list_element_types = []
            dict_element_values = {}
            #list_of_dict_elements = ["parentNode", "xml_namespace", "classAtt_type", "SibChild_type", "ElementName", "ElementValue", "value"]
            
            if (actionType == "authors"):
                # Begin defining the metadata for each element in <authors> to be added:
                #
                #  <email\>
                #  <first_name> A.</first_name>
                #  <last_name>Davies</last_name>
                #  <affiliations/>
                #------------------------------                
                parent_auth_contr_xpath   =  "./authors[1]"
                parent_element_xpath  =  "./authors[1]/author[" + str(i+1) + "]"

                # add: <author> as Class to 1st instance of <author>
                dict_element_values = {"parentNode": parent_auth_contr_xpath , "xml_namespace": None, "classAtt_type": "class", "SibChild_type": "child_next",  "ElementName": "author", "ElementValue": None}
                list_element_types.append(dict_element_values)
                
                # add: <email> as Attribute to 2nd instance of parent class <author>
                dict_element_values = {"parentNode":  parent_element_xpath, "xml_namespace": None, "classAtt_type": "attribute", "SibChild_type": "child_next",  "ElementName": "email", "ElementValue": None}
                list_element_types.append(dict_element_values)
        
                # add: <first_name> as Attribute to 2nd instance of parent class <author>
                dict_element_values = {"parentNode":  parent_element_xpath, "xml_namespace": None, "classAtt_type": "attribute", "SibChild_type": "child_next",  "ElementName": "first_name", "ElementValue": first_name_value}
                list_element_types.append(dict_element_values)
        
                # add: <last_name> as Attribute to 2nd instance of parent class <author>
                dict_element_values = {"parentNode":  parent_element_xpath, "xml_namespace": None, "classAtt_type": "attribute", "SibChild_type": "child_next",  "ElementName": "last_name", "ElementValue": last_name_value}
                list_element_types.append(dict_element_values)
        
                # add: <affiliations> as Attribute to 2nd instance of parent class <author>
                dict_element_values = {"parentNode": parent_element_xpath , "xml_namespace": None, "classAtt_type": "class", "SibChild_type": "child_next",  "ElementName": "affiliations", "ElementValue": None}
                list_element_types.append(dict_element_values)    

            elif (actionType == "contributors"):    
                #------------------------------
                # Begin defining the metadata for each element in <contributors> to be added:
                #
                #  <email\>
                #  <first_name> A.</first_name>
                #  <last_name>Davies</last_name>
                #  <contributor_type/>
                #  <affiliations/>
                #------------------------------
                parent_auth_contr_xpath   =  "./contributors[1]"
                parent_element_xpath  =  "./contributors[1]/contributor[" + str(i+1) + "]"
                
                # add: <contributor> as Class to 1st instance of <contributors>
                dict_element_values = {"parentNode": parent_auth_contr_xpath , "xml_namespace": None, "classAtt_type": "class", "SibChild_type": "child_next",  "ElementName": "contributor", "ElementValue": None}
                list_element_types.append(dict_element_values)
        
                # add: <email> as Attribute to 2nd instance of parent class <contributor>
                dict_element_values = {"parentNode":  parent_element_xpath, "xml_namespace": None, "classAtt_type": "attribute", "SibChild_type": "child_next",  "ElementName": "email", "ElementValue": None}
                list_element_types.append(dict_element_values)
        
                # add: <first_name> as Attribute to 2nd instance of parent class <contributor>
                dict_element_values = {"parentNode":  parent_element_xpath, "xml_namespace": None, "classAtt_type": "attribute", "SibChild_type": "child_next",  "ElementName": "first_name", "ElementValue": first_name_value}
                list_element_types.append(dict_element_values)
        
                # add: <last_name> as Attribute to 2nd instance of parent class <contributor>
                dict_element_values = {"parentNode":  parent_element_xpath, "xml_namespace": None, "classAtt_type": "attribute", "SibChild_type": "child_next",  "ElementName": "last_name", "ElementValue": last_name_value}
                list_element_types.append(dict_element_values)
        
                # add: <contributor_type> as Attribute to 2nd instance of parent class <contributor>
                dict_element_values = {"parentNode":  parent_element_xpath, "xml_namespace": None, "classAtt_type": "attribute", "SibChild_type": "child_next",  "ElementName": "contributor_type", "ElementValue": editor_value}
                list_element_types.append(dict_element_values)
                
                # add: <affiliations> as Attribute to 2nd instance of parent class <contributor>
                dict_element_values = {"parentNode": parent_element_xpath , "xml_namespace": None, "classAtt_type": "class", "SibChild_type": "child_next",  "ElementName": "affiliations", "ElementValue": "None"}
                list_element_types.append(dict_element_values)    

            else:
                print "Process_author_contributor_list: invalid type: %s\n" % (actionType)                                                                                
                sys.exit()
            
            #------------------------------
            #  Capture the everchanging xmlTree
            #------------------------------                  
            xmlDOI_tree = ET.fromstring(xmlDOI_Text)
                                                
            #------------------------------
            # Capture / Insert the single <author> or <contributor> instance defined above 
            #------------------------------                  
            for x in list_element_types:                                                
                parentNode = x.get("parentNode")             
                xml_namespace = x.get("xml_namespace")
                classAtt_type = x.get("classAtt_type")
                SibChild_type = x.get("SibChild_type")
                ElementName = x.get("ElementName")
                ElementValue = x.get("ElementValue")
                #value = x.get("value")

                #------------------------------
                # Capture / Update the tree with the new insertions
                #------------------------------                  
                xmlDOI_tree, xmlDOI_Text = xmlUtil.insert_xml_elements_2(dict_namespaces, xml_namespace, xmlDOI_tree, parentNode, classAtt_type, SibChild_type, ElementName, ElementValue)   
                util.WriteDebugInfo(f_debug,debug_flag,"Append","Process_author_contributor_list.xmlDOI_Text: " + xmlDOI_Text + "\n")                                                   

    #------------------------------
    #------------------------------
    #  Update/ insert the Node as a <contributor>
    #------------------------------  
    #------------------------------
    if (actionType == "contributors"):              list_element_types = []
        dict_element_values = {}
    
        #------------------------------
        #  Capture the everchanging xmlTree
        #------------------------------                  
        xmlDOI_tree = ET.fromstring(xmlDOI_Text)
        
        nodeName_value =  dict_configList.get("publisher")                                                                                    
        contrib_type_value = "DataCurator"
        
        if (list_type == ""): 
            i = "1"
        
        else:
            i = str(len(items)+1)
            
        #------------------------------
        # Begin defining the metadata for each element in <contributors> to be added:
        #
        #  <full_name> Atmospheres Node</full_name>
        #  <contributor_type>DataCurator</contributor_type>
        #  <affiliations/>
        #------------------------------
        parent_auth_contr_xpath   =  "./contributors[1]"
        parent_element_xpath  =  "./contributors[1]/contributor[" + i + "]"
        
        # add: <contributor> as Class to 1st instance of <contributors>
        dict_element_values = {"parentNode": parent_auth_contr_xpath , "xml_namespace": None, "classAtt_type": "class", "SibChild_type": "child_next",  "ElementName": "contributor", "ElementValue": None}
        list_element_types.append(dict_element_values)
    
        # add: <full_name> as Attribute to 2nd instance of parent class <contributor>
        dict_element_values = {"parentNode":  parent_element_xpath, "xml_namespace": None, "classAtt_type": "attribute", "SibChild_type": "child_next",  "ElementName": "full_name", "ElementValue": nodeName_value}
        list_element_types.append(dict_element_values)
    
        # add: <contributor_type> as Attribute to 2nd instance of parent class <contributor>
        dict_element_values = {"parentNode":  parent_element_xpath, "xml_namespace": None, "classAtt_type": "attribute", "SibChild_type": "child_next",  "ElementName": "contributor_type", "ElementValue": contrib_type_value}
        list_element_types.append(dict_element_values)
        
        # add: <affiliations> as Attribute to 2nd instance of parent class <contributor>
        dict_element_values = {"parentNode": parent_element_xpath , "xml_namespace": None, "classAtt_type": "class", "SibChild_type": "child_next",  "ElementName": "affiliations", "ElementValue": "None"}
        list_element_types.append(dict_element_values)    
        
        #------------------------------
        # Capture / Insert the single <author> or <contributor> instance defined above 
        #------------------------------                  
        for x in list_element_types:                                                
            parentNode = x.get("parentNode")             
            xml_namespace = x.get("xml_namespace")
            classAtt_type = x.get("classAtt_type")
            SibChild_type = x.get("SibChild_type")
            ElementName = x.get("ElementName")
            ElementValue = x.get("ElementValue")
            #value = x.get("value")
    
            #------------------------------
            # Capture / Update the tree with the new insertions
            #------------------------------                  
            xmlDOI_tree, xmlDOI_Text = xmlUtil.insert_xml_elements_2(dict_namespaces, xml_namespace, xmlDOI_tree, parentNode, classAtt_type, SibChild_type, ElementName, ElementValue)   
            util.WriteDebugInfo(f_debug,debug_flag,"Append","Process_author_contributor_list.xmlDOI_Text: " + xmlDOI_Text + "\n")                                                   

    xmlDOI_Text = pretty_print_xml(xmlDOI_Text)
    return xmlDOI_Text


#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Process_DOI_metadata(dict_configList, dict_fixedList, dict_ConditionData, dict_all_records, FileName, DOI_filepath):                                              
#------------------------------                                                                                                 
# 20190418 -- replaced code with: Return_keyword_values
# 20200410 -- commented code to populate <keyword> attribute; replaced with slot in dict_ConditionData
# 20200414: added code to insert xml <element> for <authors> and <contributors>
#------------------------------                                                                                                 

    #------------------------------
    # Open & Read the contents of the DOI XML label -- to be created / updated
    #   -- generate a DICT of the identified namespaces in the XML preamble
    #         -- etree XML parser errors if encounters 'Null' namespace; so delete from DICT
    #------------------------------
    try:
        f_DOI_file = open(DOI_filepath, mode='r+')
        xmlDOI_Text = f_DOI_file.read()     
        f_DOI_file.close()

        #f_template = open(DOI_filepath, mode='r')     
        #xmlDOI_tree = ET.parse(f_template)
        #f_template.close()
         
    except:
        print "DOI file (%s) not found for edit\n" % (DOI_filepath)                                                                       
        sys.exit()
        
    #------------------------------                                                                                                 
    # Begin replacing the metadata in the DOI file with that in Product Label                                                                                 
    #------------------------------
    #parent_xpath = "/records/record/"
    parent_xpath = "/record/"
        
    #------------------------------                                                                                                 
    # For each key/value in dictionary (that contains the values for the DOI label)
    #------------------------------  
    #------------------------------
    #  BEGIN - insert class and attribute under EXO namespace
    #     -- add <Alias_List> as child to <Discipline_Area>; appends after last child class
    #
    #          </exo:Planetary_System_Parameters>
    #          <exo:Alias_List>
    #                <exo:Alias>123</exo:Alias>
    #                <exo:Alias>456</exo:Alias>
    #           </exo:Alias_List>
    #    </Discipline_Area>    
    #------------------------------    
    dict_value = dict_ConditionData.get(FileName)
    
    for key, value in dict_value.items():
        attr_xpath = key

        if (attr_xpath == "authors") or (attr_xpath == "contributors"):            
            attr_xpath = parent_xpath + key
 
            #------------------------------                                                                                                 
            # Set the xpath for the ParentNode; 
            #    --  if is ParentNode is the <root node> then set xpath as "."
            #             -- can only use "child_next" as other actions are not supported
            #    --  if ParentNode is child to <root node>, then set xpath as child
            #
            # Set the xml_namespace as:
            #    -- "pds" if processing PDS Product
            #    -- None if ns is not applicable
            #------------------------------   
            xmlDOI_Text = Process_author_contributor_list(xmlDOI_Text, FileName, dict_value, key)            

        else:    
            attr_xpath = parent_xpath + key

            xmlDOI_Text = Populate_DOI_XML_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, value)                          
            util.WriteDebugInfo(f_debug,debug_flag,"Append","Process_DOI_metadata.xmlText: " + xmlDOI_Text + "\n")                                                   

    #------------------------------                                                                                                 
    # Add the <puiblisher> metadata defined in the Config file
    #    -- <keywords> using the items in list_keyword_values
    #  -- each value must be separated by semi-colon
    #------------------------------   
    publisher = dict_configList.get("publisher")       
    attr_xpath = parent_xpath + "publisher"
    
    xmlDOI_Text = Populate_DOI_XML_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, publisher)                          
    util.WriteDebugInfo(f_debug,debug_flag,"Append","Process_DOI_metadata.xmlText: " + xmlDOI_Text + "\n")                                                   

    #------------------------------                                                                                                 
    # Write the replacement metadata to each individual DOI file
    #   -- capture the contents of the individual DOI files and store in dictionary
    #          -- dict_all_records; indexed by filename
    #------------------------------    
    f_DOI_file = open(DOI_filepath, mode='wb')                
    f_DOI_file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    f_DOI_file.write("<records>\n")
    f_DOI_file.write("    " + xmlDOI_Text + "\n") 
    f_DOI_file.write("</records>\n") 
    f_DOI_file.close()                  

    dict_all_records[FileName] = xmlDOI_Text
        
    return dict_all_records

    
#------------------------------                                                                                                 
#------------------------------ 
def word_wrap(string, width=80, ind1=0, ind2=0, prefix=''):
#------------------------------                                                                                                 
#------------------------------         
    """ word wrapping function.
        string: the string to wrap
        width: the column number to wrap at
        prefix: prefix each line with this string (goes before any indentation)
        ind1: number of characters to indent the first line
        ind2: number of characters to indent the rest of the lines
    """
    string = prefix + ind1 * " " + string
    newstring = ""
    while len(string) > width:
        # find position of nearest whitespace char to the left of "width"
        marker = width - 1
        while not string[marker].isspace():
            marker = marker - 1

        # remove line from original string and add it to the new string
        newline = string[0:marker] + "\n"
        newstring = newstring + newline
        string = prefix + ind2 * " " + string[marker + 1:]

    return newstring + string


#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Return_keyword_values(dict_configList, list_keyword_values):                                              
#------------------------------                                                                                                 
# 20190418:  new method to reformat values for <keywords># 20200617:  added code to check for PDS3 Series -- {"SOLAR SYSTEM", "EARTH", "JUPITER"}
#------------------------------                                                                                                 

    keywords = ""
    
    #------------------------------                                                                                                 
    # Add the global keyword values in the Config file to those scraped from the Product label
    #    -- <keywords> using the items in list_keyword_values
    #  -- each value must be separated by semi-colon (e.g., "test1; test2")
    # 
    # global_keyword_values preceed values scraped from Product label
    #------------------------------   
    global_keywords = dict_configList.get("global_keyword_values", 'None')
    
    if (global_keywords is not None):
        if (";" in global_keywords):
            kv = global_keywords.split(";")
    
            for items in kv:
                if (not items == ""):
                    keywords += items + "; "                 
        else:
            if (not len(global_keywords) == 0):
                keywords = global_keywords
            else:
                keywords = "PDS; "
    else:
        keywords = ""
     
    #------------------------------                                                                                                 
    # Add the keyword values that were scraped from the Product label
    #    -- ensure no duplicate values between global and scraped
    #------------------------------   
    if (not len(list_keyword_values) == 0):        
        for items in list_keyword_values:
            if (not items == ""): 
                if (isinstance(items, list)):
                    list_keyword_values.remove(items)
                    for each in items:
                        list_keyword_values.append(each)
                        
                else:                    
                    if (items not in keywords):
                        if (keywords.endswith("; ")):
                            keywords += items    
                        else:
                            keywords += "; " + items        

    return keywords


#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Return_LIDVID_submitted(XML_path, dict_LIDVID_submitted):                                                                                                                    
#------------------------------  
# 20200121 -- added as new function; returns List of product LIDVIDs previously submitted
# 20200714 -- added check to ensure LDIVID provided in <identifier_value>
#------------------------------                                                                                                 
#                                                                                                                               

    #------------------------------                                                                                                 
    # dict_LIDVID_submitted -- DICTIONARY of:                                                                                                       
    #   -- indexed by LIDVID
    #   -- DICTIONARY of 'submitted' metadata:
    #       -- status: Registered | Reserved
    #       -- DOI (if previously submiited) | Null (if not-previously submitted)
    #       -- site_id (e.g., <id>1517614</id>)
    #
    # Note that 'reserved' records do NOT use <report_numbers> to store LIDVID
    #    -- LIDVID is stored in "related_identifiers/related_identifier/identifier_value"
    #------------------------------                                  

    #------------------------------  
    # Note that 'reserved' records do NOT have (as yet) a <report_numbers> 
    #    -- so need to account for these types of records
    #             -- only process where <record status="Registered"> or <record status="Pending">
    #------------------------------                              
    from lxml import etree
    
    if not os.path.exists(XML_path):                                                                                    
        print "Return_LIDVID_submitted - path in <OSTI_submitted_records> in Config.xml file was not found: " + XML_path + "\n"                                                           
        sys.exit()                                                                                                                 
    
    doc = ET.parse(XML_path)
    count_records = 0
    
    for e in doc.findall('.//record'): 
        list_attr = []
        count_records += 1
        
        status = e.attrib.get('status') 
        
        if (not status == 'Deactivated'):                
            if (status == 'Registered') or (status == 'Pending'):
                #------------------------------  
                # Note that for Registered records, LIDVID is stored in two different attributes depending on whether submitted as IAD or IAD2
                #    -- IAD   stores LIDVID in: <report_numbers>
                #    -- IAD2 stores LIDVID in: <related_identifiers/related_identifier/identifier_value>                
                #------------------------------                                              
                LIDVID = lxml_findtext_with_exception(e, 'related_identifiers/related_identifier/identifier_value', "lxml_findtext_with_exception: LIDVID not found")   # returns "Null" (text) if not found
                
                #------------------------------  
                # Note that for some Active records have a LID instead of a LIDVID 
                #    -- Iog those only having LID
                #------------------------------                                              
                if (not "::" in LIDVID):
                    util.WriteLogInfo(f_log,"Append","Return_LIDVID_submitted -- LIDVID not found in: 'related_identifiers/related_identifier/identifier_value': %s\n" % (LIDVID))                                                    
                    #print " ERROR: Return_LIDVID_submitted -- LIDVID not found in: 'related_identifiers/related_identifier/identifier_value': %s " % (LIDVID)
                    #sys.exit()
                    
                if (LIDVID == "Null"):
                    LIDVID = lxml_findtext_with_exception(e, 'report_numbers', "")   # returns "Null" (text) if not found                    
                    
                site_id = e.find('id').text
                doi = e.find('doi').text
            
            else:
                #------------------------------ 
                # Note that for Reserved records, LIDVID is stored in two different attributes depending on whether submitted as IAD or IAD2
                #    -- IAD   stores LIDVID in: <accession_number>
                #    -- IAD2 stores LIDVID in: <related_identifiers/related_identifier/identifier_value> 
                #                            <related_identifiers>
                #                                <related_identifier>
                #                                   <identifier_type>URL</identifier_type>
                #                                   <identifier_value>urn:nasa:pds:a12side_ccig_raw_arcsav::1.0</identifier_value>
                #
                # Note that not all 'reserved' records have recorded LIDVID in <related_identifiers/related_identifier/identifier_value>
                #    -- so Try and except
                #------------------------------                              
                LIDVID = lxml_findtext_with_exception(e, 'related_identifiers/related_identifier/identifier_value', "lxml_findtext_with_exception: LIDVID not found")

                if (not "::" in LIDVID):
                    util.WriteLogInfo(f_log,"Append","Return_LIDVID_submitted -- LIDVID not found in: 'related_identifiers/related_identifier/identifier_value': %s\n" % (LIDVID))                                                    
                    #print " ERROR: Return_LIDVID_submitted -- LIDVID not found in: 'related_identifiers/related_identifier/identifier_value': %s " % (LIDVID)
                    #print "    -- manually edit the submitted-records file and add info to <related_identifiers/>"
                    #sys.exit()
                        
                if (LIDVID == "Null"):
                    LIDVID = lxml_findtext_with_exception(e, 'accession_number', "")   # returns "Null" (text) if not found                    
                
                site_id = e.find('id').text
                doi = e.find('doi').text

            #------------------------------  
            # Record the above into a sub-Dictionary
            #------------------------------  
            dict_LIDVID_submitted[LIDVID] = {}

            dict_LIDVID_submitted[LIDVID]["status"] = status
            dict_LIDVID_submitted[LIDVID]["site_id"] = site_id
            dict_LIDVID_submitted[LIDVID]["doi"] = doi

    #------------------------------  
    # Record the processing of the dictionary
    #------------------------------  
    util.WriteLogInfo(f_log,"Append","Return_LIDVID_submitted - dict_LIDVID_submitted.count: " + str(count_records) + "\n")                                                      
    
    for key, elem in dict_LIDVID_submitted.items():
            util.WriteLogInfo(f_log,"Append","Return_LIDVID_submitted - dict_LIDVID_submitted[" + key + "] = " + str(elem) + "\n")                                                      
                
    return dict_LIDVID_submitted


#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Return_LIDVID_is_Registered(FileName, dict_ConditionData, dict_siteURL, dict_fileName_matched_status, prev_submitted, action_type):                                                                                                                    
#------------------------------  
# 20200121 -- added as new function; returns List of product LIDVIDs previously submitted
# 20210414 -- added code to identify LIDVID for {PD3 DataSets}
#------------------------------                                                                                                 
#                                                                                                                               

    #------------------------------                                                                                     
    # Save 'submitted' status for eachFile
    #   -- update status should 'registered' status change 
    #------------------------------                                                                                     
    if (prev_submitted == "DOI_previously_submitted"):
        dict_fileName_matched_status[FileName] = prev_submitted
        
    #------------------------------                                                                                     
    # Using URL, make SOUP
    #   -- try to scrape webpage
    #   -- save URL for debug info
    #------------------------------                                                                                     
    site_url = dict_ConditionData.get(FileName).get('site_url', 'None')   
    prod_LIDVID = dict_ConditionData.get(FileName).get("related_identifiers/related_identifier/identifier_value", 'None')
        
    try:
        dict_siteURL[FileName] = site_url
        
        if (site_url == "None") or (len(site_url) == 0):
            print 'Return_LIDVID_is_Registered: An error occured fetching site_url: %s' % (site_url)   
            return 1
 
        else:
             resp = urlopen(site_url)            
        
    except URLError as e:
        print 'Main: An error occured fetching %s \n %s' % (site_url, e.reason)   
        return 1
    
    soup = BeautifulSoup(resp.read(), "lxml")

    #------------------------------                                                                                     
    # For each TABLE, in webpage
    #   -- try to scrape <tr><td> constructs
    #------------------------------                                                                                     
    try:
        tables = soup.find_all('table')
        
        for i in tables:
            list_tableData = []
            
            #------------------------------                                                                                     
            # list[0] contains entire table structure -- so delete
            #------------------------------                                                                                     
            list_tableData = parse_table(i)
            del list_tableData[0]

            index = -1
            for items in list_tableData:
                index += 1
                break_loop = False
                
                if (index >0):                    
                    if (action_type == "PDS4") and ('IDENTIFIER' in items):
                        #print "identifier found @: " + str(index)
                        print "LIDVID is Registered: " + list_tableData[index][1]
    
                        prod_LIDVID = dict_ConditionData.get(FileName).get("related_identifiers/related_identifier/identifier_value", 'None')
                        
                        if (prod_LIDVID == list_tableData[index][1]):
                            list_TableData = ("LIDVID_in_siteURL-matched", prod_LIDVID, site_url, list_tableData[index][1])
                        else:
                            list_TableData = ("LIDVID_in_siteURL-not-matched", prod_LIDVID, site_url, list_tableData[index][1])

                        #------------------------------                                                                                                 
                        # dict_fileName_matched_status -- DICTIONARY of:                                                                                                       
                        #   -- indexed by fileName
                        #   -- List of 'submitted' metadata:
                        #       -- 'DOI_previously_submitted' | 'DOI_not_previously_submitted'  
                        #   -- List of 'registered' metadata:    
                        #       -- Product_LIDVID (specified in each file)  
                        #       -- Product_siteURL (ascertained from LIDVID)
                        #       -- table index @ siteURL (ascertained by scraping webpage)
                        #------------------------                                                                                                                               
                        dict_fileName_matched_status[FileName] = prev_submitted, list_TableData
                        break_loop = True
                        break
                        
                    elif (action_type == "PDS3-DS") and ("Data Set Information" in items):
                        #------------------------------                                                                                                 
                        # Locate ""Data Set Information" in  list_tableData[index]                                                                                                       
                        #   -- return position
                        #   -- next position contains LIDVID
                        #------------------------                                                                                                                               
                        pos = list_tableData[index].index("Data Set Information")                        
                        #print "identifier found @: " + str(index)
                        print "DataSet LIDVID is Registered: " + list_tableData[index][pos+1]
    
                        prod_LIDVID = dict_ConditionData.get(FileName).get("related_identifiers/related_identifier/identifier_value", 'None')
                        
                        if (prod_LIDVID in items):
                            list_TableData = ("LIDVID_in_siteURL-matched", prod_LIDVID, site_url, prod_LIDVID)
                        else:
                            list_TableData = ("LIDVID_in_siteURL-not-matched", prod_LIDVID, site_url, prod_LIDVID)

                        #------------------------------                                                                                                 
                        # dict_fileName_matched_status -- DICTIONARY of:                                                                                                       
                        #   -- indexed by fileName
                        #   -- List of 'submitted' metadata:
                        #       -- 'DOI_previously_submitted' | 'DOI_not_previously_submitted'  
                        #   -- List of 'registered' metadata:    
                        #       -- Product_LIDVID (specified in each file)  
                        #       -- Product_siteURL (ascertained from LIDVID)
                        #       -- table index @ siteURL (ascertained by scraping webpage)
                        #------------------------                                                                                                                               
                        dict_fileName_matched_status[FileName] = prev_submitted, list_TableData
                        break_loop = True
                        break
                            
                    else:
                        print "Return_LIDVID_is_Registered - ERROR: invalid action_type '%i'." % (action_type)                                                           
                        sys.exit()
                        
                
            if (break_loop):
                break           # break outer loop if inner loop detects value
            
    except:
        print "soup.find.all('table') -- not found in <site_url>: " + site_url
 
        list_TableData = ("LIDVID_in_siteURL-not-matched", prod_LIDVID, site_url, "ODL could not be parsed")
        dict_fileName_matched_status[FileName] = prev_submitted, list_TableData

    return dict_fileName_matched_status, dict_siteURL


#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Return_orphaned_DOI_from_XLS():                                                                                                                    
#------------------------------  
# 20200309 -- added as new function; creates reserved DOI XML label from XLS | XLSX
# 20200406 -- added code to create single DOI XML file (that contains the individual XML files)
# 20200430 -- added Node as <contributor>
# 20200515 -- added code to check for orphaned DOIs; use when creating
#------------------------------                                                                                                 
#                                                                                                                               

    doi_return = "Null"
    
    #------------------------------
    # Open the XLS workbook for orphaned DOIs
    #   -- grab the first sheet by index
    #------------------------------
    xls_filepath = dict_configList.get("orphaned_DOI_xls_filepath")
    
    xl_wb = xlrd.open_workbook(xls_filepath, f_log)
    xl_sheet = xl_wb.sheet_by_index(0)                

    num_cols = xl_sheet.ncols

    if (num_cols < 1):
        print "ERROR: expecting 1 column in XLS file; has '%i' columns." % (num_cols)                                                           
        Show_column_names_in_XLS(xl_sheet)      
        sys.exit()
    else:
        Show_column_names_in_XLS(xl_sheet)      

        #------------------------------
        # extract netadata from Columns and populate row-content
        #  -- 1st column 'DOI' is used to:
        #           -- Reserve -- reuse DOI in "Create" new Reserve record
        #------------------------------  
        for row_idx in range(1, xl_sheet.nrows):    # Iterate through rows; ignore 1st row
            doi_value = str(xl_sheet.cell(row_idx, 0).value)[:-2]
            
            if (not doi_value.startswith("reused:")):
                doi_return = doi_value            

                #------------------------------
                # Mark lidvid value as having been reused
                #  -- 1st column 'DOI' 
                #
                #  BIG NOTE: to 'update' cell and worksheet; need to install xlsWriter & xlwt
                #------------------------------
                sValue = "reused: " + doi_value
                
                xl_wb_copy = copy(xl_wb)
                #sheet_copy =  xl_wb_copy.sheet_by_index(0)     
                sheet_copy =  xl_wb_copy.get_sheet(0)     
                sheet_copy.write(row_idx, 0, sValue)
                xl_wb_copy.save(xls_filepath)                
                break
            
        return doi_return
    
    
#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Create_Reserved_DOI_from_XLS(appBasePath, dict_fixedList, dict_configList, dict_ConditionData):                                                                                                                    
#------------------------------  
# 20200309 -- added as new function; creates reserved DOI XML label from XLS | XLSX
# 20200406 -- added code to create single DOI XML file (that contains the individual XML files)
# 20200430 -- added Node as <contributor>
# 20200515 -- added code to check for orphaned DOIs; use when creating
#------------------------------                                                                                                 
#                                                                                                                               
    dbl_quote = chr(34)
    #parent_xpath = "/records/record/"
    parent_xpath = "/record/"

    #------------------------------
    # Open the DOI reserved XML label 
    #   -- ElementTree supports 'findall' using dict_namespaces and designation of instances
    #   -- etree doesn't support designation of instances
    #         -- eg: ".//pds:File_Area_Observational[1]/pds:Table_Delimited[1]/pds:Record_Delimited/pds:maximum_record_length"
    #------------------------------
    res_pathName = dict_configList.get("DOI_reserve_template")
   
    try:  
        tree = ET.parse(res_pathName)
        xmlProd_root = tree.getroot()
        
    except ET.ParseError as err:
        print ("  -- ABORT: the xml 'Reserved template label; file (%s) could not be parsed\n" % (res_pathName) )
        sys.exit()
        
    else:           
        #------------------------------                                                                                                 
        # dict_all_records -- DICTIONARY of:                                                                                                       
        #   -- indexed by [fileName]
        #       -- text of each individual DOI XML label 
        #------------------------                                                                                                       
        dict_all_records = {}
        
        #------------------------------                                                                                     
        # For every 'matched' result, create the DOI XML label file
        #   -- from the DOI template
        #------------------------------
        DOI_directory_PathName = CreateDOI_Dir(None, False, appBasePath)

        #------------------------------
        # XLS formatted as 7 columns:
        #   -- status - Reserved | Update:xxx; where xxx is <site_id>
        #   -- title
        #   -- publication_date (yyyy-mm-dd)
        #   -- product_type_specific - PDS4 Bundle | PDS4 Collection | PDS4 Document
        #   -- author_last_name
        #   -- author_first_name
        #   -- related_resource - LIDVID
        #------------------------------
    
        #------------------------------
        # Open the XLS workbook
        #   -- grab the first sheet by index
        #------------------------------
        xls_filepath = dict_configList.get("xls_reserve_filepath")
        
        xl_wb = xlrd.open_workbook(xls_filepath, f_log)
        xl_sheet = xl_wb.sheet_by_index(0)                
    
        num_cols = xl_sheet.ncols
        if (num_cols < 7):
            print "ERROR: expecting 7 columns in XLS file; has '%i' columns." % (num_cols)                                                           
            Show_column_names_in_XLS(xl_sheet)      
            sys.exit()
        else:
            Show_column_names_in_XLS(xl_sheet)      
    
            for row_idx in range(1, xl_sheet.nrows):    # Iterate through rows; ignore 1st row
                #------------------------------
                # extract netadata from Columns and populate row-content
                #  -- 1st column 'state' is used to either:
                #           -- Reserve -- "Create" new Reserve record
                #           -- Update:xxx -- "Update / Edit" previously submitted Reserved record using <site_id>
                #------------------------------
                #------------------------------
                # Generate a pseudo FileName using the LIDVID
                #    -- remove "urn:nasa:pds"
                #     -- replace "::" with "-"
                #------------------------------
                related_resource = xl_sheet.cell(row_idx, 6).value
                FileName = related_resource.replace("urn:nasa:pds:", "")
                FileName = FileName.replace("::", "_")

                print " -- processing Product label file: " + FileName
                
                dict_ConditionData[FileName] = {}
                                             
                dict_ConditionData[FileName]["title"] = xl_sheet.cell(row_idx, 1).value
                #--
                # Eventhough cell is shown to be 'text / unicode'; value is actually stored as datetime
                #    -- test for unicode; else datetime
                #--
                dict_ConditionData[FileName]["action"] = xl_sheet.cell(row_idx, 0).value
                
                if (type(xl_sheet.cell(row_idx, 2).value) == unicode):
                    dict_ConditionData[FileName]["publication_date"] = xl_sheet.cell(row_idx, 2).value
                else:   
                    pb_int = xl_sheet.cell(row_idx, 2).value
                    pb_datetime = datetime(*xlrd.xldate_as_tuple(pb_int, xl_wb.datemode))
                    dict_ConditionData[FileName]["publication_date"] = pb_datetime.strftime("%Y-%m-%d") 
                                
                #------------------------------                                                                                                 
                # setting <product_type> to Collection is Okay since reserve record metadata is temporary
                #------------------------------           
                dict_ConditionData[FileName]["product_type"] ="Collection"
                dict_ConditionData[FileName]["product_type_specific"]  =xl_sheet.cell(row_idx, 3).value
                dict_ConditionData[FileName]["authors/author/last_name"] = xl_sheet.cell(row_idx, 4).value
                dict_ConditionData[FileName]["authors/author/first_name"] = xl_sheet.cell(row_idx, 5).value
                dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"] = xl_sheet.cell(row_idx, 6).value

                #------------------------------                                                                                                 
                # Add Node as <contributor>
                #------------------------------           
                publisher = dict_configList.get("publisher")       
                
                dict_ConditionData[FileName]["contributors/contributor/full_name"]  = publisher
                dict_ConditionData[FileName]["contributors/contributor/contributor_type"]  = "DataCurator"
                                
                #------------------------------                                                                                                 
                # Begin replacing the metadata in the DOI template file with that in Product Label                                                                                 
                #------------------------------           
                try:
                    f_DOI_file = open(res_pathName, mode='r+')
                    xmlDOI_Text = f_DOI_file.read()     
                    f_DOI_file.close()
                              
                except:
                    print "DOI template file (%s) not found for edit\n" % (res_pathName)                                                                       
                    sys.exit()
                                
                #------------------------------                                                                                                 
                # For each key/value in dictionary (that contains the values for the DOI label)
                #     -- determine if the <action> is to either Create | Update the metadata; or to Deactivate the DOI
                #------------------------------  
                dict_value = dict_ConditionData.get(FileName)
                action_type = "C"
                write_file = False
                
                #------------------------------                                                                                                 
                # Ascertain the "status" of the record being processed;
                #     -- Reserve -- create new DOI record
                #     -- Update  -- update previously submitted DOI record
                #     -- Deactivate -- deactivate / hide previously submitted DOI
                #------------------------------  
                value = dict_value.get("action")

                if (value.startswith("Update:")) or (value.startswith("Reserve")) or (value.startswith("Deactivate:")):
                    write_file = True
                    
                    for key, value in dict_value.items():
                        if (key == "action"):
                            if (value.startswith("Reserve")):
                                #------------------------------                                                                                                 
                                # If creating new DOI; check if there are orphaned DOIs
                                #     -- reuse 1st available
                                #------------------------------  
                                orphaned_doi = Return_orphaned_DOI_from_XLS()

                                if (not orphaned_doi == "Null"):                                        
                                    action_type = "CO"
                                    attr_xpath = parent_xpath + "id"
                                    
                                    xmlDOI_Text = Populate_DOI_XML_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, orphaned_doi)                          
                                    util.WriteDebugInfo(f_debug,debug_flag,"Append","Process_DOI_metadata.xmlText: " + xmlDOI_Text + "\n") 
                                
                            if (value.startswith("Update:")):
                                #------------------------------                                                                                                 
                                # Only update <id> if action is to Update
                                #     -- do nothing for all other Use Cases
                                #------------------------------  
                                action_type = "U"
                                
                                items = value.split(":")
                                id_value = items[1]
                                    
                                attr_xpath = parent_xpath + "id"
                                
                                xmlDOI_Text = Populate_DOI_XML_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, id_value)                          
                                util.WriteDebugInfo(f_debug,debug_flag,"Append","Process_DOI_metadata.xmlText: " + xmlDOI_Text + "\n") 
                                
                        else:   
                            attr_xpath = parent_xpath + key
                            
                            xmlDOI_Text = Populate_DOI_XML_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, value)                          
                            util.WriteDebugInfo(f_debug,debug_flag,"Append","Process_DOI_metadata.xmlText: " + xmlDOI_Text + "\n")                                                   

                elif (value.startswith("Deactivate:")):   
                    write_file = True
                    action_type = "D"
                          
                else:
                    print "     -- Warning: Create_Reserved_DOI_from_XLS - unknown 'action' type: %s" % (value)

                #------------------------------                                                                                                 
                # Write the replacement metadata to each individual DOI file
                #   -- capture the contents of the individual DOI files and store in dictionary
                #          -- dict_all_records; indexed by filename
                #------------------------------    
                if (write_file):                                
                    sString = "DOI-" + action_type + "_reserved_" + FileName + ".xml"
                    sString = sString.replace(":", "_")
                    sString = sString.replace("/", "-")
                    DOI_filepath = os.path.join(DOI_directory_PathName,sString)
    
                    f_DOI_file = open(DOI_filepath, mode='wb')                
                    f_DOI_file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
                    f_DOI_file.write("<records>\n")
                    f_DOI_file.write("    " + xmlDOI_Text + "\n") 
                    f_DOI_file.write("</records>\n") 
                    f_DOI_file.close()                  
    
                    dict_all_records[sString] = xmlDOI_Text

    #------------------------------                                                                                                 
    # Write / capture the individual DOI files into a single DOI file
    #      -- also capture the contents of the individual DOI files into 
    #           a dictionary that will be used to generate a single DOI XML label
    #          -- dict_all_records; indexed by filename
    #------------------------------    
    sString = "DOI_reserved_all_records.xml"
    DOI_filepath = os.path.join(DOI_directory_PathName,sString)

    f_DOI_file = open(DOI_filepath, mode='wb')                
    f_DOI_file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    f_DOI_file.write("<records>\n")

    for key, value in dict_all_records.items():
        c = "="
        f_DOI_file.write( "\n    <!-- " + c*(len(key)) + " -->\n")       
        f_DOI_file.write("    <!-- " + key + " -->\n")                 
        f_DOI_file.write( "    <!-- " + c*(len(key)) + " -->\n")       
        f_DOI_file.write("    " + value + "\n") 
        
    f_DOI_file.write("</records>\n\n") 
    f_DOI_file.close()                  
                    
                
#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Create_Reserved_DOI_from_CSV(appBasePath, dict_fixedList, dict_ConditionData):                                                                                                                    
#------------------------------  
# 20200215 -- added as new function; creates reserved DOI XML label from CSV
# 20200301 -- deprecated and never to be used again; one time only for ingesting PPI submitted CSV
#------------------------------                                                                                                 
#                                                                                                                               
    dbl_quote = chr(34)
            
    #------------------------------
    # Open the DOI reserved XML label 
    #   --  ElementTree supports 'findall' using dict_namespaces and designation of instances
    #   -- etree doesn't support designation of instances
    #         -- eg: ".//pds:File_Area_Observational[1]/pds:Table_Delimited[1]/pds:Record_Delimited/pds:maximum_record_length"
    #------------------------------
    res_pathName = "E:\\Python_2.7.14\\aaaProjects\\DOI_LIDVID_is_Registered_20171120\\aaaDOI_templateFiles\\DOI_IAD2_reserved_template_20200205.xml"
    
    try:  
        tree = ET.parse(res_pathName)
        xmlProd_root = tree.getroot()
        
    except ET.ParseError as err:
        print ("  -- ABORT: the xml 'Reserved template label; file (%s) could not be parsed\n" % (res_pathName) )
        sys.exit()
        
    else:           
        #------------------------------  
        # Create the directory to store the DOI XML files that were 'DOI_not_previously_submitted' and 'LIDVID_in_siteURL-matched'
        #------------------------------  
        #------------------------------                                                                                     
        # For every 'matched' result, create the DOI XML label file
        #   -- from the DOI template
        #------------------------------
        DOI_directory_PathName = CreateDOI_Dir(None, False, appBasePath)
        
        #------------------------------    
        #------------------------------                                                                                     
        # Open CSV
        #    -- for each record, create DOI XML label using metadata in XLS
        #------------------------------  
        csv_pathName = "D:\\WINWORD\\Data_Prep_HandBook\\aaaVer_9_20130225\\DOI_20150505\\aaDOI_production_submitted_labels\\PPI_Maven_reserve_CSV_20200205\\MAVEN-OSTI_IAD_submitted_records-Release20-200215_edited2.csv"

        try:                                                                                                                        
            fd = open(csv_pathName,"rb")   
           
        except IOError:                                                                                                             
            print "Unable to open the CSV file in readmode:", csv_pathName                                                                  
            sys.exit()                                                                                                                  
        
        content = fd.readlines()                                                                                                    
        fd.close()                                                                                                                  
                
        #------------------------------                                                                                     
        # For each line in CSV
        #    -- for each record, create DOI XML label using metadata in XLS
        #------------------------------  
        lineCount = 0

        for eachLine in content:                                                                                                    
            lineCount += 1
            
            #------------------------------                                                                                     
            # Ignore 1st line 
           #------------------------------  
            if (lineCount > 2):                                                                    
                items = eachLine.split(",")

                #------------------------------
                # remove "urn:nasa:pds"
                # replace "::" with "-"
                #------------------------------
                FileName = items[2][13:]
                FileName = FileName.replace(";;", "-")
                
                dict_ConditionData[FileName] = {}
                
                d = items[4].split("/")    # '2/15/2020'
                if (len(d[0]) == 1):
                    d[0] = "0" + d[0]
                if (
                    len(d[1]) == 1):
                    d[1] = "0" + d[1]
                    
                doiDate = d[2] + "-" + d[1] + "-" + d[0]
                #doiDate = datetime.strptime(prodDate, '%Y-%m-%d').strftime('%m/%d/%Y') 
                              
                dict_ConditionData[FileName]["title"] = items[1]   
                dict_ConditionData[FileName]["publication_date"] = doiDate
                #dict_ConditionData[FileName]["site_url"] = items[5]
                dict_ConditionData[FileName]["product_type"] = items[6]
                dict_ConditionData[FileName]["product_type_specific"]  = items[7]
                #dict_ConditionData[FileName]["product_nos"] = items[4]
                #dict_ConditionData[FileName]["description"] = items[8]
                #dict_ConditionData[FileName]["creators"] = items[5]
                dict_ConditionData[FileName]["authors/author/last_name"] = items[8].replace(dbl_quote, "")
                dict_ConditionData[FileName]["authors/author/first_name"] = items[9].replace(dbl_quote, "")
            
                print " -- processing Product label file: " + FileName
                
                #------------------------------                                                                                                 
                # Begin replacing the metadata in the DOI file with that in Product Label                                                                                 
                #------------------------------           
                try:
                    f_DOI_file = open(res_pathName, mode='r+')
                    xmlDOI_Text = f_DOI_file.read()     
                    f_DOI_file.close()
                              
                except:
                    print "DOI template file (%s) not found for edit\n" % (res_pathName)                                                                       
                    sys.exit()
                
                parent_xpath = "/records/record/"
                    
                #------------------------------                                                                                                 
                # For each key/value in dictionary (that contains the values for the DOI label)
                #------------------------------  
                dict_value = dict_ConditionData.get(FileName)
                
                for key, value in dict_value.items():
                    attr_xpath = parent_xpath + key
                    
                    xmlDOI_Text = Populate_DOI_XML_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, value)                          
                    util.WriteDebugInfo(f_debug,debug_flag,"Append","Process_DOI_metadata.xmlText: " + xmlDOI_Text + "\n")                                                   
            
                ##------------------------------                                                                                                 
                ## Add the <puiblisher> metadata defined in the Config file
                ##    -- <keywords> using the items in list_keyword_values
                ##  -- each value must be separated by semi-colon
                ##------------------------------   
                #publisher = dict_configList.get("publisher")       
                #attr_xpath = "/records/record/publisher"
                
                #xmlDOI_Text = Populate_DOI_XML_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, publisher)                          
                #util.WriteDebugInfo(f_debug,debug_flag,"Append","Process_DOI_metadata.xmlText: " + xmlDOI_Text + "\n")                                                   
            
                ##------------------------------                                                                                                 
                ## Add the global keyword values in the Config file to those scraped from the Product label
                ##    -- <keywords> using the items in list_keyword_values
                ##  -- each value must be separated by semi-colon
                ##------------------------------   
                #keyword_values = Return_keyword_values(dict_configList, list_keyword_values)       
                #attr_xpath = "/records/record/keywords"
                
                #xmlDOI_Text = Populate_DOI_XML_with_values(dict_fixedList, xmlDOI_Text, attr_xpath, keyword_values)                          
                #util.WriteDebugInfo(f_debug,debug_flag,"Append","Process_DOI_metadata.xmlText: " + xmlDOI_Text + "\n")                                                   
                    
                #------------------------------                                                                                                 
                # Write the replacement metadata to the DOI file
                #------------------------------    
                sString = "PPI_DOI_reserved_" + FileName.replace("::", "-") + ".xml"
                sString = sString.replace(":", "_")
                DOI_filepath = os.path.join(DOI_directory_PathName,sString)

                f_DOI_file = open(DOI_filepath, mode='w')
                f_DOI_file.write(xmlDOI_Text)                                                                                                  
                f_DOI_file.close()                  
                
            #------------------------------                                                                                                 
            # Create a file that groups each DOI record into a single file -- that can singly be submitted
            #
            # <?xml version="1.0" encoding="UTF-8"?>
            # <records> 
            #   <record status="Reserved"> 
            #          ...
            #    </record> 
            #   <record status="Reserved"> 
            #          ...
            #    </record> 
            # </records>
            #------------------------------           
            sString = "aaa_DOI_aggregate_reserved.xml"
            DOI_aggregate_filepath = os.path.join(DOI_directory_PathName,sString)

            try:
                f_DOI_aggregate_file = open(DOI_aggregate_filepath, mode='w')
                xmlDOI_Text = f_DOI_file.read()     
                          
            except:
                print "DOI template file (%s) not found for edit\n" % (res_pathName)                                                                       
                sys.exit()

            f_DOI_aggregate_file.write("<?xml version='1.0' encoding='UTF-8'?>")
            f_DOI_aggregate_file.write("<records>")

            
            f_DOI_aggregate_file.write("</records>")   
            # add code here to write aggregate files
            f_DOI_aggregate_file.close()

#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Create_Registered_DOI_from_XML(appBasePath, dict_fixedList, dict_configList, dict_ConditionData, dict_LIDVID_submitted, dict_siteURL, dict_fileName_matched_status):                                                                                                                    
#------------------------------  
# 20200330 -- added as new function; creates active / registered DOI XML label from PDS4 product XML label
# 20201130 -- added new code to process PDS4 Document products
# 20210408 -- added new code to ensure LIDVID is found in "reserved" records
# 20210521 -- added new code to ensure the DOI file (to be created) is NOT a duplicate (i.e., is unque)
#------------------------------                                                                                                 
#                                                                                                                               
    dbl_quote = chr(34)
    parent_xpath = "/record/"

    #------------------------------                                                                                                 
    # dict_all_records -- DICTIONARY of:                                                                                                       
    #   -- indexed by [fileName]
    #       -- text of each individual DOI XML label 
    #------------------------                                                                                                       
    dict_all_records = {}

    #------------------------------                                                                                                 
    # dir_list: create a LIST of unique directories                                                                                 
    #     --- that contain files to be processed                                                                                    
    # file_list: create a LIST of files to be processed                                                                             
    # context_lid_list: create a LIST of the LIDs of each context product                                                           
    #     --- reference these using <Internal_Reference>                                                                            
    # member_entry_list: create a LIST of the LIDs, etc for each collection product                                                 
    #                                                                                                                               
    # For each directory:                                                                                                           
    #   -- identify the files in the directory and process                                                                          
    #------------------------                                                                                                       
    dir_list = []                                                                                                                   
    file_list = [] 

    #------------------------------                                                                                     
    # Keep count of  LIDVIDs previously submitted and not previously submitted
    #------------------------------        
    count_LIDVID_prev_submitted = 0
    count_LIDVID_not_prev_submitted = 0
    
    #------------------------------                                                                                                 
    # Walk the directory tree starting at the directory specified in                                                                
    # the above parameter                                                                                                           
    #  -- fetch values to populate table structure                                                                                  
    #------------------------  
    root_path = dict_configList.get("root_path")
    
    if not os.path.exists(root_path):                                                                                               
        print "ERROR - ROOT directory NOT found: " + root_path + "\n"                                                                       
        sys.exit()                                                                                                                  
    else:                                                                                                                           
        print "ROOT directory found -- processing PDS4 files in directory: " + root_path + "\n"                                          
    
    #------------------------------                                                                                                 
    # Create a tuple that holds file extensions                                                                                     
    #------------------------------                                                                                                 
    fileExtTuple = (dict_fixedList.get("source_fileExt").lower(), dict_fixedList.get("source_fileExt").upper())                   
    
    for root, dirs, files in os.walk(root_path): 
        #------------------------------                                                                                             
        # maintain a unique list of directories                                                                                     
        #------------------------------                                                                                             
        if (len(dir_list) == 0):                                                                                                    
            dir_list.append(dirs)                                                                                                         
        
        for f in files:                                                                                                             
            sString = os.path.join(root, f)                                                                                         
            if (sString.endswith(fileExtTuple)):                                                                                    
                #------------------------------                                                                                     
                # Ignore any 'collection' xml files                                                                                 
                #    -- each file should have 'collection' in the filename                                                          
                #------------------------------                                                                                     
                file_list.append(sString)                                                                                       
    
    
    #------------------------------                                                                                             
    # Get List of records previously submited for DOIs
    #    -- append to this List as files are processed
    #------------------------------         
    XML_path = dict_configList.get("OSTI_submitted_records") 
    
    dict_LIDVID_submitted = Return_LIDVID_submitted(XML_path, dict_LIDVID_submitted)
            
    for eachFile in file_list:       
        util.WriteDebugInfo(f_debug,debug_flag,"Append","MAIN.eachFile: " + eachFile + "\n")                                           
    
        RelPathName, FileName = ReturnRelativePathAndFileName(root_path, eachFile)                                          
        print "  processing file: " + RelPathName + chr(92) + FileName                                                      
    
        #------------------------------                                                                                     
        # Open the XML label                                                                                                
        #   -- read all of the text                                                                                         
        #   -- generate a DICT of the identified namespaces in the XML preamble
        #         -- etree XML parser errors if encounters 'Null' namespace; so delete from DICT
        #------------------------------
        global dict_namespaces
        dict_namespaces = xmlUtil.return_NameSpaceDictionary(f_debug, debug_flag, eachFile)
        
        #------------------------------                                                                                     
        # Using product LIDVID, ensure product has not been previously submitted
        #   -- scan XML file specified in config file: <OSTI_submitted_records>
        #           -- records already submitted to OSTI/IAD
        #------------------------------                                                                                     
        #dict_ConditionData, list_keyword_values = Process_legacy_IAD_ProductLabel_metadata(dict_fixedList, dict_ConditionData, eachFile, FileName)
        dict_ConditionData = Process_IAD2_ProductLabel_metadata(dict_fixedList, dict_configList, dict_ConditionData, eachFile, FileName)

        #------------------------------                                                                                     
        # Ensure LIDVID not previously submitted
        #------------------------------ 
        product_LIDVID = dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"]
                
        if (dict_LIDVID_submitted.get(product_LIDVID, None) == None):
            # 20210408 -- added this code to ensure "reserved" record is found
            print " ERROR: Create_Registered_DOI_from_XML -- LIDVID not found in: 'related_identifiers/related_identifier/identifier_value': %s " % (product_LIDVID)
            print "               -- manually edit the submitted-records file and add info to <related_identifiers/>"
            #sys.exit()
            
            count_LIDVID_not_prev_submitted += 1            
            prev_submitted = "DOI_not_previously_submitted"

            ###------------------------------                                                                                     
            ### Add product LIDVID to List of previously submitted products
            ###------------------------------ 
            ##dict_LIDVID_submitted[product_LIDVID]= 'Null'
            list_a = "Null"
             
        else:  
            count_LIDVID_prev_submitted += 1
            prev_submitted = "DOI_previously_submitted"
            
            a = dict_LIDVID_submitted.get(product_LIDVID)
            list_a = [ [k,v] for k,v in a.items() ]
            
        #print "dict_LIDVID_submitted[" + product_LIDVID + "] is '" + prev_submitted + "': " + str(dict_LIDVID_submitted.get(product_LIDVID).getitems())
        print "dict_LIDVID_submitted[" + product_LIDVID + "] is '" + prev_submitted + "': " + str(list_a)
                                                                                                 
        #------------------------------                                                                                     
        # Ensure LIDVID was previously registered
        #    -- store status of both submitted & registered
        #------------------------------ 
        dict_fileName_matched_status, dict_siteURL = Return_LIDVID_is_Registered(FileName, dict_ConditionData, dict_siteURL, dict_fileName_matched_status, prev_submitted, "PDS4")

    #------------------------------  
    # Record the processing of the dictionary
    #------------------------------  
    count_records = len(dict_ConditionData)
    util.WriteLogInfo(f_log,"Append","Process_IAD2_ProductLabel_metadata - dict_ConditionData.count: " + str(count_records) + "\n")                                                      
    
    for key, elem in dict_ConditionData.items():
            util.WriteLogInfo(f_log,"Append","Process_IAD2_ProductLabel_metadata - dict_ConditionData[" + key + "] = " + str(elem) + "\n")                                                      
    
    count_records = len(dict_fileName_matched_status)
    util.WriteLogInfo(f_log,"Append","Create_Registered_DOI_from_XML - dict_fileName_matched_status.count: " + str(count_records) + "\n")                                                      
    
    for key, elem in dict_fileName_matched_status.items():
            util.WriteLogInfo(f_log,"Append","Create_Registered_DOI_from_XML - dict_fileName_matched_status[" + key + "] = " + str(elem) + "\n")                                                      
                                   
    #------------------------------                                                                                     
    #------------------------------                                                                                     
    # Finished processing all of the XML files to be submitted for DOIs
    #     -- gathered all of the prcocessing results into: dict_fileName_matched_status
    #
    #------------------------------  
    # Create the directory to store the DOI XML files that were 'DOI_not_previously_submitted' and 'LIDVID_in_siteURL-matched'
    #------------------------------  
    #------------------------------                                                                                     
    # For every 'matched' result, create the DOI XML label file
    #   -- from the DOI template
    #------------------------------
    DOI_template_filepath = dict_configList.get("DOI_register_template")   
    DOI_directory_PathName = CreateDOI_Dir(f_debug, debug_flag, appBasePath)

    #------------------------------                                                                                     
    # Retrieve key, value for status in eachFile
    #   -- tuple_value[0] = 'DOI_previously_submitted' | 'DOI_not_previously_submitted'
    #   -- tuple_value[1] = tuple[1][0] = 'LIDVID_in_siteURL-matched' | 'LIDVID_in_siteURL-not-matched'
    #   -- tuple_value[2] = tuple[1][1] = product LIDVID
    #   -- tuple_value[3] = tuple[1][2] = table_data
    #                                   
    #------------------------------
    for key, tuple_value in sorted( dict_fileName_matched_status.items() ):

        #------------------------------                                                                                                 
        # For each key/value in dictionary (that contains the values for the DOI label)
        #     -- determine if the <action> is to either Create | Update the metadata; or to Deactivate the DOI
        #------------------------------  
        action_type = "C"
        
        #------------------------------                                                                                                 
        # Ascertain if the LIDVID in the PDS4 Product (being processed) has been Registered (or not)
        #          -- DOI_previously_submitted
        #          -- DOI_not_previously_submitted
        #------------------------------  
        if  (tuple_value[1][0] == 'LIDVID_in_siteURL-matched'):
        #if  (tuple_value[1][0] == 'LIDVID_in_siteURL-not-matched'):
 
            prodLabel_path = os.path.join(root, key)                                                                                         

            if (tuple_value[0] == 'DOI_previously_submitted'):        
                #------------------------------                                                                                     
                # action is to Update a Registered DOI record
                #      -- query by LIDVID to get metadata:
                #               -- If dict_metadata == None; PDS4 Product not found in registry
                #               -- If dict_metadata == "not None"; PDS4 Product found in registry; 
                #                       --  example: dict_LIDVID_submitted[urn:nasa:pds:uranus_occ_support:data::1.0] = ['Reserved', '1517664', '10.17189/1517664']
                #------------------------------
                dict_metadata = dict_LIDVID_submitted.get(tuple_value[1][1], 'None')
              
                if (dict_metadata is not None):
                    #------------------------------                                                                                 
                    #  the LIDVID in the PDS4 Product (being processed) has been Registered
                    #     -- PDS4 Product found in registry / has been Registered
                    #             -- retrieve <status> & <id> from previously registered DOI record
                    #------------------------------  
                    action = dict_metadata.get("status")       # either Registered or Reserved
                    id_value = dict_metadata.get("site_id")
                
                    if (action == "Reserved"):
                        action_type = "CR"
                        
                    elif (action == "Registered") or (action == "Pending") :
                        action_type = "CU"

                    else:
                        print "Create_Registered_DOI_from_XML: invalid action (" + tuple_value[0] + ") for LIDVID (" + tuple[1][1] + ") being Reserved."
                        sys.exit()

                    #------------------------------                                                                                     
                    # 20200409 - append <id> to set of metadata in dict_ConditionData
                    #                      -- this will modify the value in <id> to match the previously submitted / updated DOI record
                    #------------------------------
                    dict_metadata = dict_ConditionData.get(key)
                    dict_metadata["id"] = id_value
                    dict_ConditionData[key] = dict_metadata
                        
            
            elif (tuple_value[0] == 'DOI_not_previously_submitted'):
                  #------------------------------                                                                                     
                  # action is to Create a new DOI record
                  #      -- query by LIDVID to get metadata:
                  #               -- If dict_metadata == None; PDS4 Product not found in registry
                  #               -- If dict_metadata == "not None"; PDS4 Product found in registry; 
                  #                       --  example: dict_LIDVID_submitted[urn:nasa:pds:uranus_occ_support:data::1.0] = ['Reserved', '1517664', '10.17189/1517664']
                  #------------------------------
                  dict_metadata = dict_LIDVID_submitted.get(tuple_value[1][1], 'None')
                
                  if (dict_metadata is not None):
                      #------------------------------                                                                                 
                      #  the LIDVID in the PDS4 Product (being processed) has been Registered
                      #     -- PDS4 Product found in registry / has been Registered
                      #             -- set <id> to Null value
                      #------------------------------  
                      #------------------------------                                                                                     
                      # 20200409 - append <id> to set of metadata in dict_ConditionData
                      #                      -- this will modify the value in <id> to match the previously submitted / updated DOI record
                      #------------------------------
                      action_type = "C"
                      
                      dict_metadata = dict_ConditionData.get(key)
                      dict_metadata["id"] = ""
                      dict_ConditionData[key] = dict_metadata
                  
            else:
                print "Create_Registered_DOI_from_XML: invalid action (" + tuple_value[0] + ") for LIDVID (" + tuple[1][1] + ") being Registered."
                sys.exit()
                
                
            #------------------------------                                                                                     
            # Copy the DOI_template_file into the directory where DOI_generated_label files are
            #   -- save the DOI_template_file as the new DOI_generated_file 
            #         -- use the original name of the PDS4 Product XML label
            #
            # 20210521 - Ensure the DOI file (to be created) is unique
            #------------------------------
            sInventoryName = "DOI-" + action_type + "_registered_" + key            
            sInventoryName_unique = Return_nonDuplicate_FileName(f_debug, debug_flag, DOI_directory_PathName, sInventoryName)
                
            fileDestination = os.path.join(DOI_directory_PathName, sInventoryName_unique)                                                               
            fileSource = DOI_template_filepath                                                                                              
        
            shutil.copy2(fileSource, fileDestination)                                                                                   

            #------------------------------                                                                                     
            # Using the metadata in the PDS4 Product XML label
            #   -- add / modify the new DOI_generated_file with the metadata
            #------------------------------
            DOI_filepath = fileDestination
            
            #dict_ConditionData, list_keyword_values = Process_ProductLabel_metadata(dict_fixedList, prodLabel_path)            
            #dict_all_records = Process_DOI_metadata(dict_configList, dict_fixedList, dict_ConditionData, dict_all_records, key, list_keyword_values, DOI_filepath)
            dict_all_records = Process_DOI_metadata(dict_configList, dict_fixedList, dict_ConditionData, dict_all_records, key, DOI_filepath)


            #Return_LIDVID_submitted - dict_LIDVID_submitted[urn:nasa:pds:a12side_ccig_raw_arcsav::1.0] = ['Reserved', '1518439', '10.17189/1518439']


        elif ( tuple_value[0] == 'DOI_previously_submitted') and (tuple_value[1][0] == 'LIDVID_in_siteURL-not-matched' ): 
            siteID_lidvid = dict_ConditionData.get(key)["accession_number"]
 
            print "File (" + key + ") was ingested into the Registry; PDS4 Product LIDVID was 'previously submitted'; LIDVID in siteURL was not 'matched': "
            print "    -- Product LIDVID: "+str(dict_LIDVID_submitted.get(siteID_lidvid))
            print "    -- Registered / site_URL LIDVID: "+ tuple_value[1][1] 
            
        elif ( tuple_value[0] == 'DOI_not_previously_submitted') and (tuple_value[1][0] == 'LIDVID_in_siteURL-matched' ): 
            siteID_lidvid = dict_ConditionData.get(key)["accession_number"]            
            print "File (" + key + ") was not ingested into the Registry; PDS4 Product LIDVID was 'not previously submitted'; siteURL 'matched': " + tuple_value[1][1] 
            print "    -- Product LIDVID: "+ str(dict_LIDVID_submitted.get(siteID_lidvid))
            print "    -- Registered / site_URL LIDVID: "+ tuple_value[1][1] 

        elif ( tuple_value[0] == 'DOI_not_previously_submitted') and (tuple_value[1][0] == 'LIDVID_in_siteURL-not-matched' ):
            siteID_lidvid = dict_ConditionData.get(key)["accession_number"]

            print "File (" + key + ") was not ingested into the Registry; PDS4 Product LIDVID was 'not previously submitted'; siteURL was not 'matched': " + tuple_value[1][1] 
            print "    -- Product LIDVID: "+str(dict_LIDVID_submitted.get(siteID_lidvid))
            print "    -- Registered / site_URL LIDVID: "+ tuple_value[1][1] 


    #------------------------------                                                                                                 
    # Write / capture the individual DOI files into a single DOI file
    #      -- also capture the contents of the individual DOI files into 
    #           a dictionary that will be used to generate a single DOI XML label
    #          -- dict_all_records; indexed by filename
    #------------------------------    
    sString = "DOI_registered_all_records.xml"
    DOI_filepath = os.path.join(DOI_directory_PathName,sString)

    f_DOI_file = open(DOI_filepath, mode='wb')                
    f_DOI_file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    f_DOI_file.write("<records>\n")

    for key, value in dict_all_records.items():        
        c = "="
        f_DOI_file.write( "\n    <!-- " + c*(len(key)) + " -->\n")       
        f_DOI_file.write("    <!-- " + key + " -->\n")                 
        f_DOI_file.write( "    <!-- " + c*(len(key)) + " -->\n")       
        f_DOI_file.write("    " + value + "\n") 
        
    f_DOI_file.write("</records>\n\n") 
    f_DOI_file.close()                  



#------------------------------
#------------------------------
def Show_column_names_in_XLS(xl_sheet):
#------------------------------
#------------------------------

    #------------------------------
    # Using 'Open' the XLS workbook & sheet
    #   -- grab the names of the columns
    #------------------------------
    row = xl_sheet.row(0)  # 1st row
    print(60*'-' + 'n(Column #) value [type]n' + 60*'-')
    for idx, cell_obj in enumerate(row):
        cell_type_str = ctype_text.get(cell_obj.ctype, 'unknown type')
        print('(%s) %s [%s]' % (idx, cell_obj.value, cell_type_str, ))


#------------------------------                                                                                                 
#------------------------------                                                                                                 
def lxml_findtext_with_exception(element, xpath, message):                                                                                                                        
#------------------------------  
#------------------------------                                                                                                 
# 20200330 -- new method to find attributes.text
#     -- split out msg if not found
#------------------------------                                                                                                 
#                                                                                                                               
    ret = (element.findtext(xpath))
    
    if not ret:
        #raise ValueError(message)
        ret = "Null"
    else:
        ret = ret.strip()
        
    return ret
        

#------------------------------
#------------------------------
def pretty_print_xml(xmlText):    
#------------------------------
# 20191023 - inserts node at end; namespace = "ns0"
#------------------------------

    indent = "    "
    indent_index = 1
    
    open_regEx = "^" + '<[ =":_a-zA-Z0-9]+>(.*)' + "$" 
    close_regEx = "^" + '(.*)</[:_a-zA-Z0-9]+>' + "$"
    
    #------------------------------                                                                                             
    # Pretty print the XML                                                                                                                 
    #  -- inserting elements into XML modifies the XML and screws up the indentation                                                               
    #       -- modify the XML to be more visually friendly                                                                 
    #              -- only modify the 'text' that follows the preamble
    #                   --  the 'text' the follow the XSD specifications
    #------------------------------                                                                                             
    #sBuffer = xmlText.split('.xsd">')                                                                                           

    #if (not(len(sBuffer) == 2)):                                                                                                
        #print "exiting: pretty_print_xml.xmlText: preamble in XML 'text' doesn't contain '.xsd'"                        
        #sys.exit()                                                                                                              
    #else:                                                                                                                       
        #sBuffer[0] += '.xsd">'                                                                                                  
        #outText = ""
        
    #------------------------------                                                                                             
    # Read each line in XML 'text' 
    #  -- if line contains: <x><y></y></x>; replace all instances of '><' with '>/n<'
    #         -- save edited text; to process indentation
    #------------------------------ 
    xml_edited_Text = ""
    outText = ""
    
    for line in xmlText.splitlines():
        if ("><" in line):
            current_indent = ">\n" + indent*indent_index +"<"
            line = line.replace("><", current_indent)
            
        xml_edited_Text += line + os.linesep

    #------------------------------                                                                                             
    # Process indentation
    #   -- Read each line in XML 'text'; 
    #        -- if line contains '</'; decrement indent_index
    #        -- if line contains '<'; increment index_index
    #        -- if line contains both '<' and '</'; no action on indent_index
    #------------------------------ 
    for line in xml_edited_Text.splitlines():            
        bOpenMatched = False
        patc = re.compile(open_regEx)        
        m = patc.match(line.strip())

        if (m):
            bOpenMatched = True
                
        bClosedMatched = False
        patc = re.compile(close_regEx)            
        m = patc.match(line.strip())

        if (m):
            bClosedMatched = True        

        #------------------------------                                                                                             
        # Modify the line according to the above indentation                                                                                                                  
        #  -- add the modified line to the Buffer
        #------------------------------             
        if (bOpenMatched and bClosedMatched):
            # do nothing; just write the 'text'
            outText += (indent*indent_index) + line.strip() + os.linesep
        elif (bClosedMatched):
            indent_index -= 1
            outText += (indent*indent_index) + line.strip() + os.linesep
            
        elif (bOpenMatched):
            outText += (indent*indent_index) + line.strip() + os.linesep
            indent_index += 1  
        else:    
            # do nothing
            outText += (indent*indent_index) + line.strip() + os.linesep
                
    #outText = sBuffer[0] + outText
    return outText


#------------------------------
#------------------------------
def Return_duplicate_DOI_by_title():    
#------------------------------
# 20200507 - new method that locates and reports duplicate titles 
#                      found in the OSTI registry of submitted DOIs
#------------------------------

    list_metadata = []
    dict_duplicate_metadata = {}
    
    #------------------------------                                                                                             
    # Get List of records previously submited for DOIs
    #    -- append to this List as files are processed
    #------------------------------         
    XML_path = dict_configList.get("OSTI_submitted_records") 

    #------------------------------
    # Open the XML label 
    #   --  ElementTree supports 'findall' using dict_namespaces and designation of instances
    #   -- etree doesn't support designation of instances
    #         -- eg: ".//pds:File_Area_Observational[1]/pds:Table_Delimited[1]/pds:Record_Delimited/pds:maximum_record_length"
    #------------------------------
    try:  
        tree = ET.parse(XML_path)
        xmlProd_root = tree.getroot()
        
    except ET.ParseError as err:
        sString = "  -- ABORT (Return_duplicate_DOI_titles): the xml 'label; file (%s) could not be parsed\n" % (XML_path)                
        print (sString)
        sString = "      -- %s\n" % (err)
        print (sString)
        sys.exit()
        
    else:                      
        #------------------------------
        #------------------------------
        # Iterate over each <DOI> specified in the XML label
        #    -- for each <DOI>; capture the metadata
        #------------------------------
        #------------------------------
        obj_record_uri = "./record"
           
        #------------------------------
        # Get 'records' attribute
        #------------------------------
        for record in tree.findall(obj_record_uri):
            status_value = record.attrib
            id_value = record.find('id').text
            title_value = record.find('title').text

            if ('Registered' in str(status_value)) or ('Pending' in str(status_value)):
                #------------------------------  
                # Note that for Registered records, LIDVID is stored in two different attributes depending on whether submitted as IAD or IAD2
                #    -- IAD   stores LIDVID in: <report_numbers>
                #    -- IAD2 stores LIDVID in: <related_identifiers/related_identifier/identifier_value>                
                #------------------------------                                              
                LIDVID = lxml_findtext_with_exception(record, 'related_identifiers/related_identifier/identifier_value', "lxml_findtext_with_exception: LIDVID not found")   # returns "Null" (text) if not found
                
                if (LIDVID == "Null"):
                    LIDVID = lxml_findtext_with_exception(record, 'report_numbers', "")   # returns "Null" (text) if not found                    
            
            else:
                #------------------------------ 
                # Note that for Reserved records, LIDVID is stored in two different attributes depending on whether submitted as IAD or IAD2
                #    -- IAD   stores LIDVID in: <accession_number>
                #    -- IAD2 stores LIDVID in: <related_identifiers/related_identifier/identifier_value> 
                #                            <related_identifiers>
                #                                <related_identifier>
                #                                   <identifier_type>URL</identifier_type>
                #                                   <identifier_value>urn:nasa:pds:a12side_ccig_raw_arcsav::1.0</identifier_value>
                #
                # Note that not all 'reserved' records have recorded LIDVID in <related_identifiers/related_identifier/identifier_value>
                #    -- so Try and except
                #------------------------------                              
                LIDVID = lxml_findtext_with_exception(record, 'related_identifiers/related_identifier/identifier_value', "lxml_findtext_with_exception: LIDVID not found")
                        
                if (LIDVID == "Null"):
                    LIDVID = lxml_findtext_with_exception(record, 'accession_number', "")   # returns "Null" (text) if not found                    
            
            #------------------------------
            # Capture above metadata in List
            #------------------------------
            list_metadata.append([id_value, status_value, LIDVID, title_value])
            
            #------------------------------
            # Using the List; Capture all <title> in Dictionay
            #------------------------------
            if ('Reserved' in str(status_value)):                 
                sString = "  "
            else:
                sString = ""
                registered_LIDVID = LIDVID
                registered_status_value = status_value
                
                
            if (dict_duplicate_metadata.get(title_value, None) == None):
                id_value += ": " + str(status_value) + sString + " lidvid: " + LIDVID
                dict_duplicate_metadata[title_value] = [id_value]
                                
            else:
                id_value += ": " + str(status_value) + sString + " lidvid: " + LIDVID
                list_x = dict_duplicate_metadata.get(title_value)
                #list_x.append(id_value)

                id_value += " --  " + str(registered_status_value) + sString + " lidvid: " + registered_LIDVID
                list_x.append(id_value)
                
                dict_duplicate_metadata[title_value] = (list_x)
                
                
        #------------------------------
        # Process all <records> to find  duplicate <title>
        #    -- Log/ report duplicate <title>; where instances > 1
        #------------------------------
        util.WriteLogInfo(f_log,"Append","\nReturn_duplicate_DOI_titles:\n")                                                      

        for item in dict_duplicate_metadata:
            value = dict_duplicate_metadata.get(item)
            item_count = len(value)
            
            if (item_count > 1):
                sString = "<title>: "  + item + ": \n"
                util.WriteLogInfo(f_log,"Append", sString)                                                              

                for items in value:
                    sString = "  -- " + str(items) + "\n"
                    util.WriteLogInfo(f_log,"Append", sString)                                                              
           

        #------------------------------
        # Process all <records> to find  records where 'status' = Reserved
        #    -- Log/ report duplicate Reserved records
        #           -- to add to Orphaned XLS
        #------------------------------
        util.WriteLogInfo(f_log,"Append","\nReturn_duplicate_Reserved_DOI_titles:\n")                                                      

        for item in dict_duplicate_metadata:
            value = dict_duplicate_metadata.get(item)
            item_count = len(value)
            
            if (item_count > 1):
                 if ('Reserved' in str(value[1])):   
                     items = value[1].split(":")
                     lidvid = items[0]

                     #------------------------------
                     # Remove LIDVID from string
                     #------------------------------
                     sString = lidvid + ": "
                     other = value[1].replace(sString, "")

                     sString = lidvid + chr(9) + "  " + chr(9) + other + "\n"
                     util.WriteLogInfo(f_log,"Append", sString)                                                              
                     


#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Create_Registered_DOI_from_PDS3_Document(appBasePath, dict_fixedList, dict_configList, dict_ConditionData, dict_LIDVID_submitted, dict_siteURL, dict_fileName_matched_status):                                                                                                                        
#------------------------------  
#------------------------------                                                                                                 
# 20210126 -- initial
# 20210126 -- NOT USED; mostly a duplicate of code in: Create_Registered_DOI_from_PDS3_ODL
#------------------------------                                                                                                 
#  

    dbl_quote = chr(34)
    parent_xpath = "/record/"

    #------------------------------                                                                                                 
    # dict_all_records -- DICTIONARY of:                                                                                                       
    #   -- indexed by [fileName]
    #       -- text of each individual DOI XML label 
    #------------------------                                                                                                       
    dict_all_records = {}

    #------------------------------                                                                                                 
    # dir_list: create a LIST of unique directories                                                                                 
    #     --- that contain files to be processed                                                                                    
    # file_list: create a LIST of files to be processed                                                                             
    # context_lid_list: create a LIST of the LIDs of each context product                                                           
    #     --- reference these using <Internal_Reference>                                                                            
    # member_entry_list: create a LIST of the LIDs, etc for each collection product                                                 
    #                                                                                                                               
    # For each directory:                                                                                                           
    #   -- identify the files in the directory and process                                                                          
    #------------------------                                                                                                       
    dir_list = []                                                                                                                   
    file_list = [] 

    #------------------------------                                                                                     
    # Keep count of  LIDVIDs previously submitted and not previously submitted
    #------------------------------        
    count_LIDVID_prev_submitted = 0
    count_LIDVID_not_prev_submitted = 0
    
    #------------------------------                                                                                                 
    # Walk the directory tree starting at the directory specified in                                                                
    # the above parameter                                                                                                           
    #  -- fetch values to populate table structure                                                                                  
    #------------------------  
    root_path = dict_configList.get("root_path")
    
    if not os.path.exists(root_path):                                                                                               
        print "ROOT directory not found: " + root_path + "\n"                                                                       
        sys.exit()                                                                                                                  
    else:
        ext = dict_fixedList.get("source_fileExt").lower()
        print "ROOT directory found -- processing PDS3 files having file_extension of '%s' in directory: %s\n" %  (ext, root_path)                                          
    
    #------------------------------                                                                                                 
    # Create a tuple that holds file extensions                                                                                     
    #------------------------------                                                                                                 
    fileExtTuple = (dict_fixedList.get("source_fileExt").lower(), dict_fixedList.get("source_fileExt").upper())                   
    
    for root, dirs, files in os.walk(root_path): 
        #------------------------------                                                                                             
        # maintain a unique list of directories                                                                                     
        #------------------------------                                                                                             
        if (len(dir_list) == 0):                                                                                                    
            dir_list.append(dirs)                                                                                                         
        
        for f in files:                                                                                                             
            sString = os.path.join(root, f)                                                                                         
            if (sString.endswith(fileExtTuple)):                                                                                    
                #------------------------------                                                                                     
                # Ignore any 'collection' xml files                                                                                 
                #    -- each file should have 'collection' in the filename                                                          
                #------------------------------                                                                                     
                file_list.append(sString)                                                                                       
    
    
    #------------------------------                                                                                             
    # Get List of records previously submited for DOIs
    #    -- append to this List as files are processed
    #------------------------------         
    XML_path = dict_configList.get("OSTI_submitted_records") 
    
    dict_LIDVID_submitted = Return_LIDVID_submitted(XML_path, dict_LIDVID_submitted)
            
    for eachFile in file_list:       
        util.WriteDebugInfo(f_debug,debug_flag,"Append","MAIN.eachFile: " + eachFile + "\n")                                           
    
        RelPathName, FileName = ReturnRelativePathAndFileName(root_path, eachFile)                                          
        print "  processing file: " + RelPathName + chr(92) + FileName                                                      
    
        #------------------------------                                                                                     
        # Open / parse the ODL label                                                                                                
        #   -- read all of the text     
        #   -- pack into a dictionary
        #------------------------------  
        #------------------------------
        # Read the XML label
        #   -- generate a DICT of the identified namespaces in the XML preamble
        #         -- as the PDS3 ODL label doesn't have any namespaces; set to default
        #------------------------------
        global dict_namespaces
        dict_namespaces = {u'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        
        #------------------------------
        # Open / parse the ODL label 
        #   --  using pdsparser
        #------------------------------
        odl_parseable = True
        
        try:  
            dict_odl = pdsparser.PdsLabel.from_file(eachFile).as_dict()  
            
        except:
            odl_parseable = False
            sString = "  -- ERROR: the PDS3 Document ODL file could not be parsed: (%s)\n" % (eachFile)                
            print (sString)
            
            
        #------------------------------                                                                                     
        # Using product LIDVID, ensure product has not been previously submitted
        #   -- scan XML file specified in config file: <OSTI_submitted_records>
        #           -- records already submitted to OSTI/IAD
        #------------------------------                                                                                     
        if (odl_parseable):
            dict_ConditionData, list_ODL_no_DS_Terse = Process_IAD2_ODL_DataSet_metadata(dict_fixedList, dict_configList, dict_ConditionData, dict_odl, FileName, eachFile)
            
            #------------------------------                                                                                     
            # Ensure LIDVID not previously submitted
            #------------------------------ 
            identifier_product_LIDVID = dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"]
            accession_product_LIDVID = dict_ConditionData[FileName]["accession_number"]
      
            if (dict_LIDVID_submitted.get(identifier_product_LIDVID, None) == None) and (dict_LIDVID_submitted.get(accession_product_LIDVID, None) == None):
                count_LIDVID_not_prev_submitted += 1            
                prev_submitted = "DOI_not_previously_submitted"
    
                ##------------------------------                                                                                     
                ## Add product LIDVID to List of previously submitted products
                ##------------------------------ 
                #dict_LIDVID_submitted[product_LIDVID]= 'Null'
                list_a = "Null"
                 
            else:  
                count_LIDVID_prev_submitted += 1
                prev_submitted = "DOI_previously_submitted"
                
                a = dict_LIDVID_submitted.get(product_LIDVID)
                list_a = [ [k,v] for k,v in a.items() ]
                
            #print "dict_LIDVID_submitted[" + product_LIDVID + "] is '" + prev_submitted + "': " + str(dict_LIDVID_submitted.get(product_LIDVID).getitems())
            print "dict_LIDVID_submitted[" + identifier_product_LIDVID + "] is '" + prev_submitted + "': " + str(list_a)
                                                                                                     
            #------------------------------                                                                                     
            # Ensure LIDVID was previously registered
            #    -- store status of both submitted & registered
            #------------------------------ 
            dict_fileName_matched_status, dict_siteURL = Return_LIDVID_is_Registered(FileName, dict_ConditionData, dict_siteURL, dict_fileName_matched_status, prev_submitted, "PDS3-DS")
    
    #------------------------------  
    # Record the processing of the dictionary
    #------------------------------  
    if ( odl_parseable):        
        count_records = len(dict_ConditionData)
        util.WriteLogInfo(f_log,"Append","Process_IAD2_ProductLabel_metadata - dict_ConditionData.count: " + str(count_records) + "\n")                                                      
        
        for key, elem in dict_ConditionData.items():
                util.WriteLogInfo(f_log,"Append","Process_IAD2_ProductLabel_metadata - dict_ConditionData[" + key + "] = " + str(elem) + "\n")                                                      
        
        count_records = len(dict_fileName_matched_status)
        util.WriteLogInfo(f_log,"Append","Create_Registered_DOI_from_PDS3_ODL - dict_fileName_matched_status.count: " + str(count_records) + "\n")                                                      
        
        for key, elem in dict_fileName_matched_status.items():
                util.WriteLogInfo(f_log,"Append","Create_Registered_DOI_from_PDS3_ODL - dict_fileName_matched_status[" + key + "] = " + str(elem) + "\n")                                                      
                                       
        #------------------------------                                                                                     
        #------------------------------                                                                                     
        # Finished processing all of the XML files to be submitted for DOIs
        #     -- gathered all of the prcocessing results into: dict_fileName_matched_status
        #
        #------------------------------  
        # Create the directory to store the DOI XML files that were 'DOI_not_previously_submitted' and 'LIDVID_in_siteURL-matched'
        #------------------------------  
        #------------------------------                                                                                     
        # For every 'matched' result, create the DOI XML label file
        #   -- from the DOI template
        #------------------------------
        DOI_template_filepath = dict_configList.get("DOI_register_template")   
        DOI_directory_PathName = CreateDOI_Dir(f_debug, debug_flag, appBasePath)
    
        #------------------------------                                                                                     
        # Retrieve key, value for status in eachFile
        #   -- tuple_value[0] = 'DOI_previously_submitted' | 'DOI_not_previously_submitted'
        #   -- tuple_value[1] = tuple[1][0] = 'LIDVID_in_siteURL-matched' | 'LIDVID_in_siteURL-not-matched'
        #   -- tuple_value[2] = tuple[1][1] = product LIDVID
        #   -- tuple_value[3] = tuple[1][2] = table_data
        #                                   
        #------------------------------
        for key, tuple_value in sorted( dict_fileName_matched_status.items() ):
    
            #------------------------------                                                                                                 
            # For each key/value in dictionary (that contains the values for the DOI label)
            #     -- determine if the <action> is to either Create | Update the metadata; or to Deactivate the DOI
            #------------------------------  
            action_type = "C"
            
            #------------------------------                                                                                                 
            # Ascertain if the LIDVID in the PDS4 Product (being processed) has been Registered (or not)
            #          -- DOI_previously_submitted
            #          -- DOI_not_previously_submitted
            #------------------------------  
            if  (tuple_value[1][0] == 'LIDVID_in_siteURL-matched'):
                prodLabel_path = os.path.join(root, key)                                                                                         
    
                if (tuple_value[0] == 'DOI_previously_submitted'):        
                    #------------------------------                                                                                     
                    # action is to Update a Registered DOI record
                    #      -- query by LIDVID to get metadata:
                    #               -- If dict_metadata == None; PDS4 Product not found in registry
                    #               -- If dict_metadata == "not None"; PDS4 Product found in registry; 
                    #                       --  example: dict_LIDVID_submitted[urn:nasa:pds:uranus_occ_support:data::1.0] = ['Reserved', '1517664', '10.17189/1517664']
                    #------------------------------
                    dict_metadata = dict_LIDVID_submitted.get(tuple_value[1][1], 'None')
                  
                    if (dict_metadata is not None):
                        #------------------------------                                                                                 
                        #  the LIDVID in the PDS4 Product (being processed) has been Registered
                        #     -- PDS4 Product found in registry / has been Registered
                        #             -- retrieve <status> & <id> from previously registered DOI record
                        #------------------------------  
                        action = dict_metadata.get("status")       # either Registered or Reserved
                        id_value = dict_metadata.get("site_id")
                    
                        if (action == "Reserved"):
                            action_type = "CR"
                            
                        elif (action == "Registered") :
                            action_type = "CU"
    
                        else:
                            print "Create_Registered_DOI_from_XML: invalid action (" + tuple_value[0] + ") for LIDVID (" + tuple[1][1] + ") being Reserved."
                            sys.exit()
    
                        #------------------------------                                                                                     
                        # 20200409 - append <id> to set of metadata in dict_ConditionData
                        #                      -- this will modify the value in <id> to match the previously submitted / updated DOI record
                        #------------------------------
                        dict_metadata = dict_ConditionData.get(key)
                        dict_metadata["id"] = id_value
                        dict_ConditionData[key] = dict_metadata
                            
                
                elif (tuple_value[0] == 'DOI_not_previously_submitted'):
                      #------------------------------                                                                                     
                      # action is to Create a new DOI record
                      #      -- query by LIDVID to get metadata:
                      #               -- If dict_metadata == None; PDS4 Product not found in registry
                      #               -- If dict_metadata == "not None"; PDS4 Product found in registry; 
                      #                       --  example: dict_LIDVID_submitted[urn:nasa:pds:uranus_occ_support:data::1.0] = ['Reserved', '1517664', '10.17189/1517664']
                      #------------------------------
                      dict_metadata = dict_LIDVID_submitted.get(tuple_value[1][1], 'None')
                    
                      if (dict_metadata is not None):
                          #------------------------------                                                                                 
                          #  the LIDVID in the PDS4 Product (being processed) has been Registered
                          #     -- PDS4 Product found in registry / has been Registered
                          #             -- set <id> to Null value
                          #------------------------------  
                          #------------------------------                                                                                     
                          # 20200409 - append <id> to set of metadata in dict_ConditionData
                          #                      -- this will modify the value in <id> to match the previously submitted / updated DOI record
                          #------------------------------
                          action_type = "C"
                          
                          dict_metadata = dict_ConditionData.get(key)
                          dict_metadata["id"] = ""
                          dict_ConditionData[key] = dict_metadata
                      
                else:
                    print "Create_Registered_DOI_from_XML: invalid action (" + tuple_value[0] + ") for LIDVID (" + tuple[1][1] + ") being Registered."
                    sys.exit()
                    
                    
                #------------------------------                                                                                     
                # Copy the DOI_template_file into the directory where DOI_generated_label files are
                #   -- save the DOI_template_file as the new DOI_generated_file 
                #         -- use the original name of the PDS4 Product XML label
                #------------------------------
                sInventoryName = "DOI-" + action_type + "_registered_" + key
                fileDestination = os.path.join(DOI_directory_PathName,sInventoryName)                                                               
                fileSource = DOI_template_filepath                                                                                              
            
                shutil.copy2(fileSource, fileDestination)                                                                                   
    
                #------------------------------                                                                                     
                # Using the metadata in the PDS4 Product XML label
                #   -- add / modify the new DOI_generated_file with the metadata
                #------------------------------
                DOI_filepath = fileDestination
                
                #dict_ConditionData, list_keyword_values = Process_ProductLabel_metadata(dict_fixedList, prodLabel_path)            
                #dict_all_records = Process_DOI_metadata(dict_configList, dict_fixedList, dict_ConditionData, dict_all_records, key, list_keyword_values, DOI_filepath)
                dict_all_records = Process_DOI_metadata(dict_configList, dict_fixedList, dict_ConditionData, dict_all_records, key, DOI_filepath)
    
    
                #Return_LIDVID_submitted - dict_LIDVID_submitted[urn:nasa:pds:a12side_ccig_raw_arcsav::1.0] = ['Reserved', '1518439', '10.17189/1518439']
    
    
            elif ( tuple_value[0] == 'DOI_previously_submitted') and (tuple_value[1][0] == 'LIDVID_in_siteURL-not-matched' ): 
                siteID_lidvid = dict_ConditionData.get(key)["accession_number"]
     
                print "File (" + key + ") was ingested into the Registry; PDS3 Product LIDVID was 'previously submitted'; LIDVID in siteURL was not 'matched': "
                print "    -- Product LIDVID: "+str(dict_LIDVID_submitted.get(siteID_lidvid))
                print "    -- Registered / site_URL LIDVID: "+ tuple_value[1][1] 
                
            elif ( tuple_value[0] == 'DOI_not_previously_submitted') and (tuple_value[1][0] == 'LIDVID_in_siteURL-matched' ): 
                siteID_lidvid = dict_ConditionData.get(key)["accession_number"]
                
                print "File (" + key + ") was not ingested into the Registry; PDS3 Product LIDVID was 'not previously submitted'; siteURL 'matched': " + tuple_value[1][1] 
                print "    -- Product LIDVID: "+ str(dict_LIDVID_submitted.get(siteID_lidvid))
                print "    -- Registered / site_URL LIDVID: "+ tuple_value[1][1] 
    
            elif ( tuple_value[0] == 'DOI_not_previously_submitted') and (tuple_value[1][0] == 'LIDVID_in_siteURL-not-matched' ):
                siteID_lidvid = dict_ConditionData.get(key)["accession_number"]
    
                print "File (" + key + ") was not ingested into the Registry; PDS3 Product LIDVID was 'not previously submitted'; siteURL was not 'matched': " + tuple_value[1][1] 
                print "    -- Product LIDVID: "+str(dict_LIDVID_submitted.get(siteID_lidvid))
                print "    -- Registered / site_URL LIDVID: "+ tuple_value[1][1] 


    if ( odl_parseable):  
        #------------------------------                                                                                                 
        # Write / capture the individual DOI files into a single DOI file
        #      -- also capture the contents of the individual DOI files into 
        #           a dictionary that will be used to generate a single DOI XML label
        #          -- dict_all_records; indexed by filename
        #------------------------------    
        sString = "DOI_registered_all_records.xml"
        DOI_filepath = os.path.join(DOI_directory_PathName,sString)
    
        f_DOI_file = open(DOI_filepath, mode='wb')                
        f_DOI_file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        f_DOI_file.write("<records>\n")
    
        for key, value in dict_all_records.items():        
            c = "="
            f_DOI_file.write( "\n    <!-- " + c*(len(key)) + " -->\n")       
            f_DOI_file.write("    <!-- " + key .replace("--","-") + " -->\n")                 
            f_DOI_file.write( "    <!-- " + c*(len(key)) + " -->\n")       
            f_DOI_file.write("    " + value + "\n") 
            
        f_DOI_file.write("</records>\n\n") 
        f_DOI_file.close()                  
    
    return list_ODL_no_DS_Terse


#------------------------------                                                                                                 
#------------------------------                                                                                                 
def Create_Registered_DOI_from_PDS3_ODL(appBasePath, dict_fixedList, dict_configList, dict_ConditionData, dict_LIDVID_submitted, dict_siteURL, dict_fileName_matched_status):                                                                                                                        
#------------------------------  
#------------------------------                                                                                                 
# 20200602 -- initial
#------------------------------                                                                                                 
#  
    
    dbl_quote = chr(34)
    parent_xpath = "/record/"

    #------------------------------                                                                                                 
    # dict_all_records -- DICTIONARY of:                                                                                                       
    #   -- indexed by [fileName]
    #       -- text of each individual DOI XML label 
    #------------------------                                                                                                       
    dict_all_records = {}

    #------------------------------                                                                                                 
    # dir_list: create a LIST of unique directories                                                                                 
    #     --- that contain files to be processed                                                                                    
    # file_list: create a LIST of files to be processed                                                                             
    # context_lid_list: create a LIST of the LIDs of each context product                                                           
    #     --- reference these using <Internal_Reference>                                                                            
    # member_entry_list: create a LIST of the LIDs, etc for each collection product                                                 
    #                                                                                                                               
    # For each directory:                                                                                                           
    #   -- identify the files in the directory and process                                                                          
    #------------------------                                                                                                       
    dir_list = []                                                                                                                   
    file_list = [] 
    list_odl_not_parseable = []
    
    #------------------------------                                                                                     
    # Keep count of  LIDVIDs previously submitted and not previously submitted
    #------------------------------        
    count_LIDVID_prev_submitted = 0
    count_LIDVID_not_prev_submitted = 0
    
    #------------------------------                                                                                                 
    # Walk the directory tree starting at the directory specified in                                                                
    # the above parameter                                                                                                           
    #  -- fetch values to populate table structure                                                                                  
    #------------------------  
    root_path = dict_configList.get("root_path")
    
    if not os.path.exists(root_path):                                                                                               
        print "ROOT directory not found: " + root_path + "\n"                                                                       
        sys.exit()                                                                                                                  
    else:
        ext = dict_fixedList.get("source_fileExt").lower()
        print "ROOT directory found -- processing PDS3 files having file_extension of '%s' in directory: %s\n" %  (ext, root_path)                                          
    
    #------------------------------                                                                                                 
    # Create a tuple that holds file extensions                                                                                     
    #------------------------------                                                                                                 
    fileExtTuple = (dict_fixedList.get("source_fileExt").lower(), dict_fixedList.get("source_fileExt").upper())                   
    
    for root, dirs, files in os.walk(root_path): 
        #------------------------------                                                                                             
        # maintain a unique list of directories                                                                                     
        #------------------------------                                                                                             
        if (len(dir_list) == 0):                                                                                                    
            dir_list.append(dirs)                                                                                                         
        
        for f in files:                                                                                                             
            sString = os.path.join(root, f)                                                                                         
            if (sString.endswith(fileExtTuple)):                                                                                    
                #------------------------------                                                                                     
                # Ignore any 'collection' xml files                                                                                 
                #    -- each file should have 'collection' in the filename                                                          
                #------------------------------                                                                                     
                file_list.append(sString)                                                                                       
    
    
    #------------------------------                                                                                             
    # Get List of records previously submited for DOIs
    #    -- append to this List as files are processed
    #------------------------------         
    XML_path = dict_configList.get("OSTI_submitted_records") 
    
    dict_LIDVID_submitted = Return_LIDVID_submitted(XML_path, dict_LIDVID_submitted)

    #------------------------------
    # Set ODL as not parseable 
    #   --  using pdsparser
    #------------------------------
    odl_parseable = False
            
    for eachFile in file_list:       
        util.WriteDebugInfo(f_debug,debug_flag,"Append","MAIN.eachFile: " + eachFile + "\n")                                           
    
        RelPathName, FileName = ReturnRelativePathAndFileName(root_path, eachFile)                                          
        print "  processing file: " + RelPathName + chr(92) + FileName                                                      
    
        #------------------------------                                                                                     
        # Open / parse the ODL label                                                                                                
        #   -- read all of the text     
        #   -- pack into a dictionary
        #------------------------------  
        #------------------------------
        # Read the XML label
        #   -- generate a DICT of the identified namespaces in the XML preamble
        #         -- as the PDS3 ODL label doesn't have any namespaces; set to default
        #------------------------------
        global dict_namespaces
        dict_namespaces = {u'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        
        #------------------------------
        # Open / parse the ODL label 
        #   --  using pdsparser
        #------------------------------
        odl_parseable = True
        
        try:  
            dict_odl = pdsparser.PdsLabel.from_file(eachFile).as_dict()  
            
        except Exception as e:
            odl_parseable = False
            list_odl_not_parseable.append(eachFile)
            
            sString = "  -- ERROR Create_Registered_DOI_from_PDS3_ODL: the PDS3 ODL file could not be parsed: (%s)\n" % (eachFile)                
            print (sString)
            #sys.exit()
            
        #------------------------------                                                                                     
        # Using product LIDVID, ensure product has not been previously submitted
        #   -- scan XML file specified in config file: <OSTI_submitted_records>
        #           -- records already submitted to OSTI/IAD
        #------------------------------                                                                                     
        if (odl_parseable):
            #------------------------------                                                                                     
            # 201210408 -- added code to attempt to identify if processing either "DOCUMENT" | ("DATASET"
            #------------------------------                                                                                                 
            try:
                has_productType = dict_odl["PRODUCT_TYPE"]
            except:
                has_productType = "Null"
                
            if (not (has_productType == "Null")):
                if (has_productType == "DOCUMENT"):
                    dict_ConditionData = Process_IAD2_ODL_Document_metadata(dict_fixedList, dict_configList, dict_ConditionData, dict_odl, FileName, eachFile)
                    
                else:
                    if (has_productType == "DATASET"):
                        dict_ConditionData, list_ODL_no_DS_Terse = Process_IAD2_ODL_DataSet_metadata(dict_fixedList, dict_configList, dict_ConditionData, dict_odl, FileName, eachFile)
                    
            else:
                try:
                    is_dataset = dict_odl["DATA_SET"]
                except:
                    is_dataset = "Null"

                if (not (is_dataset == "Null")):
                    dict_ConditionData, list_ODL_no_DS_Terse = Process_IAD2_ODL_DataSet_metadata(dict_fixedList, dict_configList, dict_ConditionData, dict_odl, FileName, eachFile)
                else:
                    sString = "  -- ERROR Create_Registered_DOI_from_PDS3_ODL: unable to ascertain if PRODUCT_TYPE = ('DOCUMENT' | ('DATASET')"                
                    print (sString)
                    sys.exit()                                   
            
            #------------------------------                                                                                     
            # Ensure LIDVID not previously submitted
            #------------------------------ 
            identifier_product_LIDVID = dict_ConditionData[FileName]["related_identifiers/related_identifier/identifier_value"]
            accession_product_LIDVID = dict_ConditionData[FileName]["accession_number"]
      
            if (dict_LIDVID_submitted.get(identifier_product_LIDVID, None) == None) and (dict_LIDVID_submitted.get(accession_product_LIDVID, None) == None):
                count_LIDVID_not_prev_submitted += 1            
                prev_submitted = "DOI_not_previously_submitted"
    
                ##------------------------------                                                                                     
                ## Add product LIDVID to List of previously submitted products
                ##------------------------------ 
                #dict_LIDVID_submitted[product_LIDVID]= 'Null'
                list_a = "Null"
                 
            else:  
                count_LIDVID_prev_submitted += 1
                prev_submitted = "DOI_previously_submitted"
                
                a = dict_LIDVID_submitted.get(identifier_product_LIDVID)
                list_a = [ [k,v] for k,v in a.items() ]
                
            #print "dict_LIDVID_submitted[" + product_LIDVID + "] is '" + prev_submitted + "': " + str(dict_LIDVID_submitted.get(product_LIDVID).getitems())
            print "dict_LIDVID_submitted[" + identifier_product_LIDVID + "] is '" + prev_submitted + "': " + str(list_a)
                                                                                                     
            #------------------------------                                                                                     
            # Ensure LIDVID was previously registered
            #    -- store status of both submitted & registered
            #------------------------------ 
            dict_fileName_matched_status, dict_siteURL = Return_LIDVID_is_Registered(FileName, dict_ConditionData, dict_siteURL, dict_fileName_matched_status, prev_submitted, "PDS3-DS")
    
    #------------------------------  
    # Record the processing of the dictionary
    #------------------------------  
    if (odl_parseable):        
        count_records = len(dict_ConditionData)
        util.WriteLogInfo(f_log,"Append","Process_IAD2_ProductLabel_metadata - dict_ConditionData.count: " + str(count_records) + "\n")                                                      
        
        for key, elem in dict_ConditionData.items():
                util.WriteLogInfo(f_log,"Append","Process_IAD2_ProductLabel_metadata - dict_ConditionData[" + key + "] = " + str(elem) + "\n")                                                      
        
        count_records = len(dict_fileName_matched_status)
        util.WriteLogInfo(f_log,"Append","Create_Registered_DOI_from_PDS3_ODL - dict_fileName_matched_status.count: " + str(count_records) + "\n")                                                      
        
        for key, elem in dict_fileName_matched_status.items():
                util.WriteLogInfo(f_log,"Append","Create_Registered_DOI_from_PDS3_ODL - dict_fileName_matched_status[" + key + "] = " + str(elem) + "\n")                                                      
                                       
        #------------------------------                                                                                     
        #------------------------------                                                                                     
        # Finished processing all of the XML files to be submitted for DOIs
        #     -- gathered all of the prcocessing results into: dict_fileName_matched_status
        #
        #------------------------------  
        # Create the directory to store the DOI XML files that were 'DOI_not_previously_submitted' and 'LIDVID_in_siteURL-matched'
        #------------------------------  
        #------------------------------                                                                                     
        # For every 'matched' result, create the DOI XML label file
        #   -- from the DOI template
        #------------------------------
        DOI_template_filepath = dict_configList.get("DOI_register_template")   
        DOI_directory_PathName = CreateDOI_Dir(f_debug, debug_flag, appBasePath)
    
        #------------------------------                                                                                     
        # Retrieve key, value for status in eachFile
        #   -- tuple_value[0] = 'DOI_previously_submitted' | 'DOI_not_previously_submitted'
        #   -- tuple_value[1] = tuple[1][0] = 'LIDVID_in_siteURL-matched' | 'LIDVID_in_siteURL-not-matched'
        #   -- tuple_value[2] = tuple[1][1] = product LIDVID
        #   -- tuple_value[3] = tuple[1][2] = table_data
        #                                   
        #------------------------------
        for key, tuple_value in sorted( dict_fileName_matched_status.items() ):
    
            #------------------------------                                                                                                 
            # For each key/value in dictionary (that contains the values for the DOI label)
            #     -- determine if the <action> is to either Create | Update the metadata; or to Deactivate the DOI
            #------------------------------  
            action_type = "C"
            
            #------------------------------                                                                                                 
            # Ascertain if the LIDVID in the PDS4 Product (being processed) has been Registered (or not)
            #          -- DOI_previously_submitted
            #          -- DOI_not_previously_submitted
            #------------------------------  
            if  (tuple_value[1][0] == 'LIDVID_in_siteURL-matched'):
                prodLabel_path = os.path.join(root, key)                                                                                         
    
                if (tuple_value[0] == 'DOI_previously_submitted'):        
                    #------------------------------                                                                                     
                    # action is to Update a Registered DOI record
                    #      -- query by LIDVID to get metadata:
                    #               -- If dict_metadata == None; PDS4 Product not found in registry
                    #               -- If dict_metadata == "not None"; PDS4 Product found in registry; 
                    #                       --  example: dict_LIDVID_submitted[urn:nasa:pds:uranus_occ_support:data::1.0] = ['Reserved', '1517664', '10.17189/1517664']
                    #------------------------------
                    dict_metadata = dict_LIDVID_submitted.get(tuple_value[1][1], 'None')
                  
                    if (dict_metadata is not None):
                        #------------------------------                                                                                 
                        #  the LIDVID in the PDS4 Product (being processed) has been Registered
                        #     -- PDS4 Product found in registry / has been Registered
                        #             -- retrieve <status> & <id> from previously registered DOI record
                        #------------------------------  
                        action = dict_metadata.get("status")       # either Registered or Reserved
                        id_value = dict_metadata.get("site_id")
                    
                        if (action == "Reserved"):
                            action_type = "CR"
                            
                        elif (action == "Registered") :
                            action_type = "CU"
    
                        else:
                            print "Create_Registered_DOI_from_XML: invalid action (" + tuple_value[0] + ") for LIDVID (" + tuple[1][1] + ") being Reserved."
                            sys.exit()
    
                        #------------------------------                                                                                     
                        # 20200409 - append <id> to set of metadata in dict_ConditionData
                        #                      -- this will modify the value in <id> to match the previously submitted / updated DOI record
                        #------------------------------
                        dict_metadata = dict_ConditionData.get(key)
                        dict_metadata["id"] = id_value
                        dict_ConditionData[key] = dict_metadata
                            
                
                elif (tuple_value[0] == 'DOI_not_previously_submitted'):
                      #------------------------------                                                                                     
                      # action is to Create a new DOI record
                      #      -- query by LIDVID to get metadata:
                      #               -- If dict_metadata == None; PDS4 Product not found in registry
                      #               -- If dict_metadata == "not None"; PDS4 Product found in registry; 
                      #                       --  example: dict_LIDVID_submitted[urn:nasa:pds:uranus_occ_support:data::1.0] = ['Reserved', '1517664', '10.17189/1517664']
                      #------------------------------
                      dict_metadata = dict_LIDVID_submitted.get(tuple_value[1][1], 'None')
                    
                      if (dict_metadata is not None):
                            #------------------------------                                                                                 
                            #  the LIDVID in the PDS4 Product (being processed) has been Registered
                            #     -- PDS4 Product found in registry / has been Registered
                            #             -- set <id> to Null value
                            #------------------------------  
                            #------------------------------                                                                                     
                            # 20200409 - append <id> to set of metadata in dict_ConditionData
                            #                      -- this will modify the value in <id> to match the previously submitted / updated DOI record
                            #------------------------------
                            action_type = "C"
                            
                            dict_metadata = dict_ConditionData.get(key)
                            dict_metadata["id"] = ""
                            dict_ConditionData[key] = dict_metadata
                      
                else:
                    print "Create_Registered_DOI_from_XML: invalid action (" + tuple_value[0] + ") for LIDVID (" + tuple[1][1] + ") being Registered."
                    sys.exit()
                    
                    
                #------------------------------                                                                                     
                # Copy the DOI_template_file into the directory where DOI_generated_label files are
                #   -- save the DOI_template_file as the new DOI_generated_file 
                #         -- use the original name of the PDS4 Product XML label
                #------------------------------
                if (not (key.endswith(".xml"))):
                    items = key.split(".")
                    filename = items[0] + ".xml"
                    sInventoryName = "DOI-" + action_type + "_registered_" + filename
                    
                else:                    
                    sInventoryName = "DOI-" + action_type + "_registered_" + key
                    
                fileDestination = os.path.join(DOI_directory_PathName,sInventoryName)                                                               
                fileSource = DOI_template_filepath                                                                                              
            
                shutil.copy2(fileSource, fileDestination)                                                                                   
    
                #------------------------------                                                                                     
                # Using the metadata in the PDS4 Product XML label
                #   -- add / modify the new DOI_generated_file with the metadata
                #------------------------------
                DOI_filepath = fileDestination
                
                #dict_ConditionData, list_keyword_values = Process_ProductLabel_metadata(dict_fixedList, prodLabel_path)            
                #dict_all_records = Process_DOI_metadata(dict_configList, dict_fixedList, dict_ConditionData, dict_all_records, key, list_keyword_values, DOI_filepath)
                dict_all_records = Process_DOI_metadata(dict_configList, dict_fixedList, dict_ConditionData, dict_all_records, key, DOI_filepath)
    
    
                #Return_LIDVID_submitted - dict_LIDVID_submitted[urn:nasa:pds:a12side_ccig_raw_arcsav::1.0] = ['Reserved', '1518439', '10.17189/1518439']
    
    
            elif ( tuple_value[0] == 'DOI_previously_submitted') and (tuple_value[1][0] == 'LIDVID_in_siteURL-not-matched' ): 
                siteID_lidvid = dict_ConditionData.get(key)["accession_number"]
     
                print "File (" + key + ") was ingested into the Registry; PDS3 Product LIDVID was 'previously submitted'; LIDVID in siteURL was not 'matched': "
                print "    -- Product LIDVID: "+str(dict_LIDVID_submitted.get(siteID_lidvid))
                print "    -- Registered / site_URL LIDVID: "+ tuple_value[1][1] 
                
            elif ( tuple_value[0] == 'DOI_not_previously_submitted') and (tuple_value[1][0] == 'LIDVID_in_siteURL-matched' ): 
                siteID_lidvid = dict_ConditionData.get(key)["accession_number"]
                
                print "File (" + key + ") was not ingested into the Registry; PDS3 Product LIDVID was 'not previously submitted'; siteURL 'matched': " + tuple_value[1][1] 
                print "    -- Product LIDVID: "+ str(dict_LIDVID_submitted.get(siteID_lidvid))
                print "    -- Registered / site_URL LIDVID: "+ tuple_value[1][1] 
    
            elif ( tuple_value[0] == 'DOI_not_previously_submitted') and (tuple_value[1][0] == 'LIDVID_in_siteURL-not-matched' ):
                siteID_lidvid = dict_ConditionData.get(key)["accession_number"]
    
                print "File (" + key + ") was not ingested into the Registry; PDS3 Product LIDVID was 'not previously submitted'; siteURL was not 'matched': " + tuple_value[1][1] 
                print "    -- Product LIDVID: "+str(dict_LIDVID_submitted.get(siteID_lidvid))
                print "    -- Registered / site_URL LIDVID: "+ tuple_value[1][1] 


    if (odl_parseable):  
        #------------------------------                                                                                                 
        # Write / capture the individual DOI files into a single DOI file
        #      -- also capture the contents of the individual DOI files into 
        #           a dictionary that will be used to generate a single DOI XML label
        #          -- dict_all_records; indexed by filename
        #------------------------------    
        sString = "DOI_registered_all_records.xml"
        DOI_filepath = os.path.join(DOI_directory_PathName,sString)
    
        f_DOI_file = open(DOI_filepath, mode='wb')                
        f_DOI_file.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        f_DOI_file.write("<records>\n")
    
        for key, value in dict_all_records.items():        
            c = "="
            f_DOI_file.write( "\n    <!-- " + c*(len(key)) + " -->\n")       
            f_DOI_file.write("    <!-- " + key .replace("--","-") + " -->\n")                 
            f_DOI_file.write( "    <!-- " + c*(len(key)) + " -->\n")       
            f_DOI_file.write("    " + value + "\n") 
            
        f_DOI_file.write("</records>\n\n") 
        f_DOI_file.close()                  
    else:
        print "No files were found having file_extension of; '%s' " % (ext)
        sys.exit()

    return list_odl_not_parseable, list_ODL_no_DS_Terse
    
    
#------------------------------                                                                                                 
#------------------------------                                                                                                 
def main():                                                                                                                        
#------------------------------  
#------------------------------                                                                                                 
# 20190418 -- added '-f' as option to specify config file
# 20200414 -- added xmlUtil module
# 20200602 -- added "RegisterPDS4" | "RegisterPDS3"
# 20210408 -- rename "Create_Registered_DOI_from_PDS3_DataSet" to "Create_Registered_DOI_from_PDS3_ODL"
#------------------------------                                                                                                 
#                                                                                                                               
    global f_debug, debug_flag                                                                                                                  
    global f_log                                                                                                                    
    global util, xmlUtil

    global dict_configList, dict_fixedList

    #------------------------------                                                                                                 
    # Ensure parameters are correctly specified                                                                                     
    #  -- needs to specify CONFIG.XML file
    #------------------------------                                                                                                 
    usage = "usage: %prog [options] arg1 ..."                                                                                       
    version = "%prog 0.20170201"                                                                                                    
    
    parser = OptionParser(usage=usage, version="version")                                                                           

    parser.add_option("-f", "--xml",                                                                                                
                      metavar="FILE", action="store", dest="xmlConfigFile", default="NotFound", type="string",                       
                      help="  -f | --xml: specify name of the Config.xml file - the xml file that initializes / specifies the application metadata.")                                                            
    
    parser.add_option("-l", "--log",                                                                                                
                      metavar="FILE", action="store", dest="sLogFileName", default="NotFound", type="string",                       
                      help="  -l | --log: specify name of the log file")                                                            
    
    (options, args) = parser.parse_args()                                                                                           

    if (options.xmlConfigFile == "NotFound"):                                                                                          
        sString = "Use: must specify the name of the Config.xml file where files are stored via '-f | --xml' command line argument"                        
        parser.error(sString)                                                                                                        
    else:                                                                                                                          
        if not os.path.exists(options.xmlConfigFile):                                                                                    
            print "Config.xml file not found as specified in option: " + options.xmlConfigFile + "\n"                                                           
            sys.exit()                                                                                                                 
    
    if (options.sLogFileName == "NotFound"):                                                                                        
        sString = "Use: must specify log_file_name via '-l | --log' command line argument"                                          
        parser.error(sString)                                                                                                       
    else:                                                                                                                           
        sLogFileName = options.sLogFileName  
        
    #------------------------------                                                                                                 
    # Read the associated configuration file                                                                                        
    #   for the required metadata                                                                                                   
    #------------------------------                                                                                                 
    #------------------------------                                                                                                 
    # Read the associated configuration file                                                                                        
    #   for the required metadata                                                                                                   
    #------------------------------                                                                                                 
    dict_configList = {}                                                                                                            
    dict_fixedList  = {}
    dict_configList, dict_fixedList = GetConfigFileMetaData(options.xmlConfigFile)

    appBasePath = os.path.abspath(os.path.curdir)
    
    #------------------------------                                                                                                 
    # Set the values for the common parameters                                                                                      
    #------------------------                                                                                                       
    root_path = dict_configList.get("root_path")                                                                                    
    pds_uri   = dict_fixedList.get("pds_uri")                                                                                      
    
    #------------------------------
    # Open the "common" and the "xmlUtil" module files
    #  -- use the values defined in the configuration file
    #------------------------------
    sys.path.append(dict_configList.get("sys_path"))
    moduleName = dict_configList.get("common_module")
    util = __import__(moduleName)                                                                          
    moduleName = dict_configList.get("xmlUtil_module")
    xmlUtil = __import__(moduleName)                                                                          
        
    #------------------------------
    # Ascertain if DEBUG is active (or not so much)
    #------------------------
    debug_flag = util.str_to_bool(dict_fixedList.get("write_DEBUG"))
    
    #------------------------------
    # Open the DEBUG file
    #  -- but only if write_DEBUG = True
    #------------------------
    if (debug_flag):
        dir = os.path.join(os.path.abspath(os.path.curdir),"aaajunk.out")
        print "aaajunk dir = '" + dir + "'"
        f_debug = open(dir, "a")
        util.WriteDebugInfo(f_debug,debug_flag,"Init","Main_Initialize\n")
    else:
        f_debug = None                                                                                    
    
    #------------------------------                                                                                                 
    # Begin by processing the parameters                                                                                            
    #------------------------------                                                                                                 
    for x in sys.argv:                                                                                                              
        util.WriteDebugInfo(f_debug,debug_flag,"Append","Argument: " + x + "\n")                                                               
    
    #------------------------------                                                                                                 
    # Initialize the log file                                                                                                    
    #------------------------------                                                                                                 
    f_log = open(sLogFileName,"w")                                                                                                  
    util.WriteLogInfo(f_log,"Init","Main_Initialize\n")                                                                             
    util.WriteLogInfo(f_log,"Append","List of ConvertRTF8_to_Ascii values:\n")                                                      
    
    #------------------------------                                                                                                 
    # dict_fileName_matched_status -- DICTIONARY of:                                                                                                       
    #   -- indexed by [fileName]
    #   -- List of 'submitted' metadata:
    #       -- 'DOI_previously_submitted' | 'DOI_not_previously_submitted'  
    #   -- List of 'registered' metadata:  
    #       -- status: 'LIDVID_in_siteURL-matched' | 'LIDVID_in_siteURL-not-matched'
    #       -- Product_LIDVID (specified in each file)  
    #       -- Product_siteURL (ascertained from LIDVID)
    #       -- LIDVID @ siteURL (ascertained by scraping webpage) 
    #------------------------                                                                                                       
    # dict_ConditionData -- DICTIONARY of:                                                                                                       
    #   -- indexed by [fileName]
    #          -- DICTIONARY of:
    #                  --  dict_ConditionData["title"]
    #                  --  dict_ConditionData["publication_date"]
    #                  --  dict_ConditionData["site_url"]
    #                  --  dict_ConditionData["product_type"]
    #                  --  dict_ConditionData["product_type_specific"]
    #                  --  dict_ConditionData["product_nos"]
    #                  --  dict_ConditionData["related_resource"]
    #                  --  dict_ConditionData["description"]
    #                  --  dict_ConditionData["authors"] 
    #                  --  dict_ConditionData["contributors"] 
    #
    #  Note that in cases where the Reserved DOI record is to be overwritten
    #      an additional field is added that references the Reserve:
    #                  --   dict_ConditionData[id] 
    #------------------------------                                                                                                     
    #------------------------------                                                                                                 
    # dict_siteURL -- DICTIONARY of:                                                                                                       
    #   -- indexed by fileName
    #          -- siteURL (ascertained from LIDVID)
    #------------------------------                                                                                                     
    #------------------------------                                                                                                 
    # dict_LIDVID_submitted -- DICTIONARY of:                                                                                                       
    #   -- indexed by LIDVID
    #   -- DICTIONARY of 'submitted' metadata:
    #       -- status: Registered | Reserved
    #       -- DOI (if previously submiited) | Null (if not-previously submitted)
    #       -- site_id (e.g., <id>1517614</id>)
    #
    # Note that 'reserved' records do NOT use <report_numbers> to store LIDVID
    #    -- LIDVID is stored in "related_identifiers/related_identifier/identifier_value"
    #------------------------------                                  
    #------------------------------                                                                                                     
    dict_fileName_matched_status = {}                                                                                                           
    dict_siteURL = {}
    dict_ConditionData = {}
    dict_LIDVID_submitted = {}

    #------------------------------
    #------------------------------
    # Ascertain if there are duplicate DOI <titles>
    #------------------------------
    Return_duplicate_DOI_by_title()

    #------------------------------
    #------------------------------
    # Determine the type of Activity in terms of either 
    #    Reserving or Registering the provided metadata
    #------------------------------
    activity_type = dict_configList.get("activity_type")
    
    if (activity_type == "Reserve"):        
        Create_Reserved_DOI_from_XLS(appBasePath, dict_fixedList, dict_configList, dict_ConditionData)
        #Create_Reserved_DOI_from_CSV(appBasePath, dict_fixedList, dict_ConditionData)
        
    elif (activity_type == "RegisterPDS4"):
        Create_Registered_DOI_from_XML(appBasePath, dict_fixedList, dict_configList, dict_ConditionData, dict_LIDVID_submitted, dict_siteURL, dict_fileName_matched_status)

    #elif (activity_type == "RegisterPDS4Document"):
    #    Create_Registered_DOI_from_XML(appBasePath, dict_fixedList, dict_configList, dict_ConditionData, dict_LIDVID_submitted, dict_siteURL, dict_fileName_matched_status, "Document")
 
    elif (activity_type == "RegisterPDS3"):
        global list_ODL_no_DS_Terse
        list_ODL_no_DS_Terse = []
        
        list_odl_not_parseable, list_ODL_no_DS_Terse = Create_Registered_DOI_from_PDS3_ODL(appBasePath, dict_fixedList, dict_configList, dict_ConditionData, dict_LIDVID_submitted, dict_siteURL, dict_fileName_matched_status)

        #------------------------------
        # Print List of ODL files that did not have  ["DATA_SET_TERSE_DESC"] as description
        #------------------------------
        print ("\n=======")
        print ("PDS3 ODL file does not have [DATA_SET_TERSE_DESC] as description")
        print ("=======")
        for eachFile in list_ODL_no_DS_Terse:
            sString = "  ERROR Create_Registered_DOI_from_PDS3_ODL: the PDS3 ODL file does not have [DATA_SET_TERSE_DESC] as description: (%s)" % (eachFile)  
            print (sString)
            util.WriteDebugInfo(f_debug,debug_flag,"Append","MAIN: the PDS3 ODL file does not have [DATA_SET_TERSE_DESC] as description: (%s)\n" % (eachFile))                                           

        #------------------------------
        # Print List of ODL files that were not parseable
        #------------------------------
        print ("\n=======")
        print ("PDS3_ODL: the PDS3 ODL file could not be parsed")
        print ("=======")
        for eachFile in list_odl_not_parseable:
            sString = "  -- ERROR Create_Registered_DOI_from_PDS3_ODL: the PDS3 ODL file could not be parsed: (%s)" % (eachFile)                
            print (sString)
            util.WriteDebugInfo(f_debug,debug_flag,"Append","MAIN: the PDS3 ODL file could not be parsed: (%s)\n" % (eachFile))                                           
          
    else:
        print "dict_configList.get.activity_type contains illegal value: " + activity_type + "\n"                                                                       
        sys.exit()                                                                                                                  
        
    #------------------------------
    #------------------------------
        
                
    #------------------------------
    # End of processing
    #------------------------------
    print "-- end of processing --\n"


        
#------------------------------                                                                                                 
#------------------------------                                                                                                 
#  MAIN                                                                                                                         
#------------------------------                                                                                                 
#------------------------------                                                                                                 
#                                                                                                                               
if __name__ == '__main__':
    global f_debug                                                                                                                  
    global f_log   
            
    status = main()
    sys.exit(status)