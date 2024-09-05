###################################################
#___  ___          _            _       _         #
#|  \/  |         | |          | |     | |        #
#| .  . | __ _ ___| |_ ___   __| | __ _| |_ __ _  #
#| |\/| |/ _` / __| __/ _ \ / _` |/ _` | __/ _` | #
#| |  | | (_| \__ \ || (_) | (_| | (_| | || (_| | #
#\_|  |_/\__,_|___/\__\___/ \__,_|\__,_|\__\__,_| #
################################################### 


# This script retrieves toots from a Mastodon instance and saves them as json files. It is intented to be run as a cron job.
# 

# Currently it retrieves the public and local timelines from the last hour.

# The Mastodon instance to query is defined in the variable 'instance'.

# The data is saved in the 'data' directory in a subdirectory named after the instance.
# The data is saved in json files, one for each hour, in subdirectories 'timeline_public' and 'timeline_local'.

# The script uses the Mastodon.py library to interact with the Mastodon API: https://pypi.org/project/Mastodon.py/
# For instructions on using the Mastodon.py library see: https://mastodonpy.readthedocs.io/en/stable/


################### Mastodon instance to query ################################# 
# Depending on the size of the querried instances, do a test run to see if the #
# script can collect all the requested within an hour, otherwise an hourly     #
# automation might run into trouble.                                           #
################################################################################

instances = []

################### Params for data retrieval ##################################

retrieve_timeline_public = True
retrieve_timeline_local = True

################### Path for log file ##########################################
# Please enter the full (not relative) path, where the path where log file     #
# should be saved and the desired file name itself                             #
################################################################################

log_file='mastodata_local_pubic.log'



import os
import json
import requests
import logging
import pandas as pd
from datetime import datetime
from mastodon import Mastodon

def check_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)
        
        
################# Logging level ###############################################
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s %(message)s')


################# Hourly Timeline Collection ##################################
################# Fetching local timeline #####################################
        
def get_timeline_local(mastodon, outpath_base, instance, hours=1):
        
    toots = []
    now = pd.Timestamp('now', tz='utc') 
    # set 'now' to zero to collect only "whole" hours
    now = now.replace(minute=0, second=0, microsecond=0)
    timeoffset = pd.DateOffset(hours=hours)
    since = now - timeoffset

    get_more = True
    max_id=None
    outpath = os.path.join(outpath_base, 'timeline_local')
    check_dir(outpath)
    while get_more:
        # Call the correct API-method, 40 posts per request is the current max. limit
        tmp = mastodon.timeline_local(limit=40, max_id=max_id)
        if len(tmp) > 0:
            toots += tmp
            max_id = tmp[-1]['id']
            if tmp[-1]['created_at'] < since: 
                get_more = False
        else:
            get_more = False

    toots = [toot for toot in toots if toot['created_at'] >= since]
    toots = [toot for toot in toots if toot['created_at'] <= now]
    #Logging amount of retrieved toots
    logging.info(f'{datetime.now()}: Number of toots retrieved from timeline_local for {instance}: {len(toots)}.') 
    if len(toots) > 0:
        outfile = os.path.join(outpath, f'{now}.json')
        # write collected toots to json files
        with open(outfile, 'w') as of:
            txt = json.dumps(toots, indent=4, default=str)
            of.write(txt)

            
################# Fetching public timeline #####################################
            
def get_timeline_public(mastodon, outpath_base, instance, hours=1):
    toots = []
    now = pd.Timestamp('now', tz='utc') 
    now = now.replace(minute=0, second=0, microsecond=0)
    timeoffset = pd.DateOffset(hours=hours)
    since = now - timeoffset

    get_more = True
    max_id=None
    outpath = os.path.join(outpath_base, 'timeline_public')
    check_dir(outpath)
    while get_more:
        tmp = mastodon.timeline_public(limit=40, max_id=max_id)
        if len(tmp) > 0:
            toots += tmp
            max_id = tmp[-1]['id']
            if tmp[-1]['created_at'] < since: 
                get_more = False
        else:
            get_more = False

    toots = [toot for toot in toots if toot['created_at'] >= since]
    toots = [toot for toot in toots if toot['created_at'] <= now]

    logging.info(f'{datetime.now()}: Number of toots retrieved from timeline_public for {instance}: {len(toots)}.') 
    if len(toots) > 0:
        outfile = os.path.join(outpath, f'{now}.json')

        with open(outfile, 'w') as of:
            txt = json.dumps(toots, indent=4, default=str)
            of.write(txt)


            
            
#### The function 'query_instance' starts the collection of timelines

def query_instance(instances, retrieve_timeline_public=retrieve_timeline_public, retrieve_timeline_local=retrieve_timeline_local):
   
    #### execute the function for every instance given in params ######
    for instance in instances:
    
    
    ### Generate secrets
    ### params #############################
        app_name = f'mastodata-{instance}'
        api_base_url = f'https://{instance}'

        #### Push declaration of the path in the folowing of condition, since
        #### the paths to the timeline data differ

        outpath_base = os.path.join('data_test', f'{instance}')
        #######################################

        #os.path.join nutzen
        secrets_path = 'secrets'
        check_dir(secrets_path)
        app_secret_file = f'{secrets_path}/mastodata_{instance}.secret'

        Mastodon.create_app(
            app_name,
            api_base_url = api_base_url,
            to_file = app_secret_file
        )

        mastodon = Mastodon(client_id = app_secret_file)
        # Es braucht einen Test, ob eine Mastodon Instanz Authentifizierung benötigt. Workouraound mit try except implementiert

        ### Implement the if else scheme from Mastidata hashtag here as well





        try:
            if retrieve_timeline_public: 
                print(f' {datetime.now()}: Started retrieving public timeline from {instance}.') # later to be realized as log entry
                get_timeline_public(mastodon, instance, outpath_base)
            if retrieve_timeline_local:
                print(f' {datetime.now()}: Started retrieving local timeline from {instance}.') # later to be realized as log entry
                get_timeline_local(mastodon, instance, outpath_base)

        except:
            logging.error(f'Error retrieving data from instance: {instance}. Check if instance requires authentication.')



####### Fetch data for specified instance from the previous hour #############

query_instance(instances, retrieve_timeline_public=retrieve_timeline_public, retrieve_timeline_local=retrieve_timeline_local)



           
