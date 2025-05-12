# This Python file uses the following encoding: utf-8


#####
#
#
######
'''# Overview #
Python Code to fetch json data from GRTS Server by HUC12,
disentagle it, and write to a file for further analysis via R.

Switching to a mixed environment from pure R because I think
python handles messy nested JSON better than R.

Date of last mod: 7 May 2025

Adding some pandas data structures to facilitate conversion to R dataset
Added code to standardize dates

# HUC Area 04 #

Around 2020, USGS changed alignment for HUC area 04, partially in
support of Canadian/American Hydrological Harmonization.  In so doing,
they realigned several HUC 04 areas, notably the Lake Champlain
drainage.  The changeover to the new codes has been spotty at best. In
particular, EPA's GRTS and ATTAINS systems have not switched to the
new codes, but the Watershed Boundary Dataset that this code relies on
to generate HUC codes to query the GRTS API with, uses only the new
codes.

So in a previous part of the workflow (HUC-it, generating the relevant
HUCs for querying in New England and beyond), these older codes are
added to the list as a workaround until the new HUCs are fully
implemented and consistent across systems. 

# SSL Workaround #

EPA's reverse proxy Apache server doesn't support TLS 1.3, and doesn't
support renegotiation back to TLS 1.2 either. So odd SSL pool code is
added here to work around that by using TLS 1.2.

## Anti-portability ##

Note that this issue is most acute on Windows
(11) clients.  Linux systems with root access can set options on the
client end to mitigate the problem.

However, this code should work as-is on Linux, but hasn't been
extensively tested there. 

# Server Timeouts and Rate Limits #

The EPA server seems to have a rate limit, either de facto or de jure
that closes the connection early. So timing restraints and other
measures are included here to help mitigate that. 

'''

# Main Import Block
import csv
import sys
import ssl
import time
from datetime import datetime
from datetime import date
import pickle
import inspect

import requests
import urllib3
import json
import pandas as pd
import pyarrow as pa
import pyarrow.feather as feather
import openpyxl
# import xlsxwriter

from urllib3.util.retry import Retry

class CustomHttpAdapter (requests.adapters.HTTPAdapter):
    ## "Transport adapter" that allows us to use custom ssl_context.
    # Special Handler to cope with SSl Renegotiation Failure from
    # TLS 1.3 to TLS 1.2: RFC 5746 Error
    # Per: https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled


    def __init__(self, ssl_context=None, **kwargs):
        ## The constructor
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        retries = Retry(total=20,connect=10, read=10, redirect=0, backoff_factor=3,
                        other=0, raise_on_status=True)
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context,retries=5)


def get_legacy_session():
    ## Special handler for https sessions
    # Given RFC 5746
    # Problem pops up on Windows with EPA's gateway Apache server

    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session




# Open CSV file with HUC12 codes and other information desired
# Isolate the HUC12 codes from other material in the CSV file (such as
# state, square area, etc)

# Globals, for class variables

G_LINE_END_DOS='\r'
G_LINE_END_UNIX='\r\n'
G_OUTPUT_BASE_NAME = 'GRTS-Data-NewEng-byHUC'
G_OUTPUT_DIR = '../Data_IO/HUC-Data-Lists/'
# Testing vT ONLY
# G_INPUT_HUC12_FILE = G_OUTPUT_DIR + 'HUC-Data-Lists/VT_HUCs.csv'

G_INPUT_HUC12_FILE = G_OUTPUT_DIR + 'New_England_HUC12s.csv'
G_NORMAL_SLEEP_TIME = 0.75
G_ERROR_SLEEP_TIME = 3
G_HUC_PROGRESS_FILE = G_OUTPUT_DIR + 'HUC-ProgressReport.txt'
G_API_BASE = 'https://ordspub.epa.gov/ords/grts_rest/grts_rest_apex/grts_rest_apex/GetProjectsByHUC12/'
G_MIN_DATE = '1987-12-31' # first year of 319 in CWA.
# Change this as needed
line_end = G_LINE_END_DOS

class HUC12List:

    def __init__(self, infile_name=G_INPUT_HUC12_FILE ):
        self.infile_name = infile_name
        self.huc12_list = []
        self.huc_progres_name = G_HUC_PROGRESS_FILE

        self.huc_progres_file = open (self.huc_progres_name,'w',
                                      encoding="utf-8")

        self.huc_progres_file.write("These HUCs Processed: \n")
        
        with open (self.infile_name, newline='') as self.csvfile:
            self.filereader = csv.DictReader(self.csvfile, delimiter = ',',
                quotechar='"')
                
            for row in self.filereader:
                self.huc12_list.append(row)

        
    def print_hucs(self):
        print (self.huc12_list)

    def write_hucs_done(self,huc_data):

        self.huc_progres_file.write(huc_data)
        self.huc_progres_file.write(line_end)
        

    def __del__(self):
        # Close File
        self.csvfile.close()
        self.huc_progres_file.close()
            
class GRTSDataParent:
    output_base_name = G_OUTPUT_BASE_NAME
    output_dir = G_OUTPUT_DIR
    grts_data_by_huc = []
    grts_response_by_huc = []
    grts_status_by_huc =[]
    input_huc12_data = []
 
    
    def __init__(self,  huc12_data_list, output_file_type='parent'):
        '''
        huc12_data is an instance of class HUC12LIST
        '''
                 
        self.output_file_type = output_file_type
        self.input_huc12_data = huc12_data_list
        self.output_file_name = self.output_dir + self.output_base_name + '.' + self.output_file_type

    def retrieve_GRTS_data (self, HUC_12_number, api_base=G_API_BASE):
        grts_response = get_legacy_session().get(api_base+HUC_12_number)
        if grts_response.status_code !=200:
            self.slow_retrieval(grts_response.status_code)
            print ("*********  ERROR URL Response ********")
            print (grts_response.status_code)
            print ("*********  Eeeeek ********")
       
        self.grts_data_by_huc.append(grts_response.json())
        self.grts_status_by_huc.append(grts_response.status_code)
        
        return (json.loads(grts_response.content))

    def parse_date_char (self, data_row):
        '''
        Fix M/D/Y into as date in dataset
        '''
            
        revised_data_row=data_row
        revised_data_row['project_start_date_text'] = data_row.get('project_start_date')
        i_temp = str (data_row.get('project_start_date'))

        when = self.reasonable_date_check(i_temp)
        revised_data_row['project_start_date'] = when

        print ("Sauce****")
        print (type(revised_data_row))
        
        print (revised_data_row)
        print()
        
        return (revised_data_row)

    def reasonable_date_check (self, date_string):
        '''
        This function checks and fixes out of bounds dates
        as needed.

        Takes a date in string form  ('%m/%d/%Y')
        Checks and substitutes reasonable dates as needed:
        * If none, give it CWA 319 program start date
        * If earlier than CWA 319 program start date, set to start date
        * If later than 'today', set date as today

        Then return date as a datetime.datetime() object
        '''
        
        #looking for date as a datetime.datetime object

        grts_min_date = datetime.strptime(G_MIN_DATE,'%Y-%m-%d')
        grts_max_date = datetime.today()
        
        try:
            date_check = datetime.strptime(date_string, '%m/%d/%Y') # check for none/null/invalid
            # This is the belt part of belt and suspenders

        except ValueError:
            date_check = grts_min_date
            print ('foo')
            print (grts_max_date)
            print ('date_string is :')
            print (date_string)

        if date_check: # Check for None/Null: The suspenders part
           
            if date_check < grts_min_date:
                date_check = grts_min_date
            elif date_check > grts_max_date:
                date_check = grts_max_date
            elif date_check >= grts_min_date and date_check <= grts_max_date:
                pass
            
        else:
            date_check = grts_min_date

        return (date_check)

    
    
    
    def slow_retrieval (r_code):


        # get a big record, see 010600030901
        # grab error codes to analyze?
        print ("Response Code: " + r_code)
        time.sleep (G_ERROR_SLEEP_TIME)
       
        return

class GRTSDataPickled(GRTSDataParent):
    ''' Pickled data dump '''
    
    def __init__(self,output_file_type='pickled'):
        self.output_file_type=output_file_type
        self.output_file_name = self.output_dir + self.output_base_name + '.' + self.output_file_type
        self.output_file = open (self.output_file_name,'wb')

    def dump_data_to_disk(self):
        ''' Whole dataset at once '''
        pickle.dump(self.grts_data_by_huc, self.output_file)

    def __del__(self):
        self.output_file.close()

class GRTSDataJson(GRTSDataParent):
    def __init__(self,output_file_type='json'):
        
        self.output_file_type=output_file_type
        self.output_file_name = self.output_dir + self.output_base_name + '.' + self.output_file_type
        self.output_file = open (self.output_file_name,'w', encoding="utf-8")
        self.output_file.write('{ "data":')
        # print (self.output_file_name)
        
    def write_data_2_disk(self,data_to_write):
        ''' One line at a time '''
        self.output_file.write(json.dumps(data_to_write))
        self.output_file.write(',')

    def __del__(self):
        self.output_file.write('}')
        self.output_file.close()
        
class GRTSDataJsonLD(GRTSDataParent):
    def __init__(self,output_file_type='ld.json'):
        self.output_file_type=output_file_type
        self.output_file_name = self.output_dir + self.output_base_name + '.' + self.output_file_type
        self.output_file = open (self.output_file_name,'w', encoding="utf-8")
        
    def write_data_2_disk(self,data_to_write):
        ''' One line at a time '''
        self.output_file.write(json.dumps(data_to_write))
        self.output_file.write(line_end)

    def __del__(self):
        # self.output_file.write(']')
        self.output_file.close()    

class GRTSDataCSV(GRTSDataParent):
    def __init__(self,output_file_type='csv.txt'):
        self.output_file_type=output_file_type
        self.field_delim=';' # consider using something else, like | or \t or ¬
        self.output_file_name = self.output_dir + self.output_base_name + '_' + self.output_file_type
        self.output_file = open (self.output_file_name,'w', encoding="utf-8")
        self.headr_file = open ("data-Header-Row.txt", 'r',encoding="utf-8")
        # Insert headr line into csv file
        # Write CSV header row
        for headline in self.headr_file:
            self.write_data_2_disk(headline) # should only be one line
        
    def write_data_2_disk(self, data_to_write):
        self.output_file.write(data_to_write)
            
    def __del__(self):

        # Something here?
        self.output_file.close()
        

class GRTSPandasFrame(GRTSDataParent):
    def __init__(self,excel_output_file_type='pandas.xlsx',
                 feather_output_file_type='pandas.feather'):
        self.excel_output_file_name = self.output_dir + self.output_base_name + '.' + excel_output_file_type
        self.feather_output_file_name =self.output_dir +  self.output_base_name + '.' + feather_output_file_type
        self.project_level_info = []
        
        
    def add_data_2_list(self, data_to_add):
        self.project_level_info.append(data_to_add)

    def createDframe(self):
        pandaFrame = pd.DataFrame(self.project_level_info)
        return (pandaFrame)
        
    def write_data_2_excel(self, data_to_write):
        dframe=data_to_write
        print()
        print("writing pandas to excel file")
        dframe.to_excel(self.excel_output_file_name)
        
    def __del__(self):
        print(self.project_level_info)
        
    def write_data_2_feather(self, data_to_write):
        feather.write_feather(data_to_write,self.feather_output_file_name)

def main():
    
    NewE_hucs =  HUC12List(G_INPUT_HUC12_FILE)
    #  NewE_hucs.print_hucs
    GRTS_Data = GRTSDataParent(NewE_hucs.huc12_list)
    pickle_data = GRTSDataPickled()
    json_data = GRTSDataJson()
    jsonLD_data = GRTSDataJsonLD()
    csv_data = GRTSDataCSV()
    p_frame=GRTSPandasFrame()
    
    for row in GRTS_Data.input_huc12_data:  # [1:40:1]: # Sub range for Testing
        data = GRTS_Data.retrieve_GRTS_data(row['huc12'])
        print ("Data:")
        print (data)
        print (" ")
        json_data.write_data_2_disk(data)
        jsonLD_data.write_data_2_disk(data)
        NewE_hucs.write_hucs_done(row['huc12'])
        time.sleep(G_NORMAL_SLEEP_TIME) # Sleep to avoid rate limits
        
    
    pickle_data.dump_data_to_disk()

    for in_row in GRTS_Data.grts_data_by_huc:
        for subentries in in_row['items']: # Row loop
            GRTS_Data.parse_date_char(subentries) 
            e_dict=subentries.keys()
            dict_val=subentries.values()
            for cols in dict_val: # columns/variables
                col_data = str (cols)
                csv_data.write_data_2_disk(col_data)
                csv_data.write_data_2_disk(csv_data.field_delim)
                
            csv_data.write_data_2_disk(line_end)
            p_frame.add_data_2_list(subentries)
            
    dframe=p_frame.createDframe()
    p_frame.write_data_2_excel(dframe)
    p_frame.write_data_2_feather(dframe)
    sys.exit()
    return
    
if __name__ == "__main__":
    main()





