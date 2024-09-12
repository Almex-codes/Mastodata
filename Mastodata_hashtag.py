###################################################
#___  ___          _            _       _         #
#|  \/  |         | |          | |     | |        #
#| .  . | __ _ ___| |_ ___   __| | __ _| |_ __ _  #
#| |\/| |/ _` / __| __/ _ \ / _` |/ _` | __/ _` | #
#| |  | | (_| \__ \ || (_) | (_| | (_| | || (_| | #
#\_|  |_/\__,_|___/\__\___/ \__,_|\__,_|\__\__,_| #
################################################### 
# written by Alexander Martin and Marcus Burkhardt #
##############################################################################
# This script retrieves posts from the hashtag timeline of mastodon. Two     #
# different methods of data collection are possible. However, both methods   #
# need you to enter one or more hashtags please insert them below in the     #
# params. Each hashtag has to be in quotes and seperated by comma.           #
# You can also decide to collect data from one or multiple instances.        #
# Keep in mind, if you do not enter any instance name, every instance        #
# registered on https://fedidb.org/ will be querried!                        #
##############################################################################
# 1. Hourly requests:                                                        #
# This method is intended to be used by automating the script in a cron job. #
# Data is saved in this directory pattern:                                   #
# 'WHERE_YOU_EXECUTE_THE_SCRIPT/data/hashtag hourly - YOUR_HASHTAGS'         #
# Data is saved in json files, one for each hour. The filename contains      #
# the name of the instance from where it originates.                         #
# Set retrieve_hourly_timeline_hashtag to True to use this method.           #
# ############################################################################
# 2. Requesting older posts:                                                 #
# Here, the collection is NOT automated. For this method a starting point is #
# defined in the params below. Follow the pattern of the example date.       #
# Data is saved in this directory pattern:                                   #
# 'WHERE_YOU_EXECUTE_THE_SCRIPT/data/hashtag                                 #
#                                                                            # 
##############################################################################
# The script uses the Mastodon.py library to interact with the Mastodon API: #
# https://pypi.org/project/Mastodon.py/                                      #
# For instructions on using the Mastodon.py library see:                     #
# https://mastodonpy.readthedocs.io/en/stable/                               #
##############################################################################


# Imported modules
# https://pypi.org/project/Mastodon.py/
# Based on: https://mastodonpy.readthedocs.io/en/stable/
import os
import json
import logging
import requests
import pandas as pd
import timeit
import concurrent.futures
import pytz
from datetime import datetime, timedelta 
from dateutil import parser
from mastodon import Mastodon

################### Params for execution #####################################

# Set the method you want to use to "True". Remember, please use the methods 
# seperatly,  not simultaniously.
retrieve_hourly_timeline_hashtag = False
retrieve_old_timeline_hashtag = True

### Insert hashtags, according to the example given. ## 
### Works with one as well as multiple hashtags. ######
### Insert hashtags like this ['tag1', 'tag2', ...] ## 

hashtags = []

# Please enter desired Mastodon instances domain. All instances must be inside 
# the brackets and each of them in quotes.
# If left empty all instances from fedidb are retrieved and queried (~2300).
instances = []

### Params for the retrieval of older posts.
utc=pytz.UTC
#Insert starting point for requesting older posts. 
start_date = '2024-06-20'
since = parser.parse(start_date)
since = utc.localize(since)

###############################################################################

#### Params for retrieval of instance list via fedidb API #####################

keep = 'Mastodon'
fedidb_url = 'https://api.fedidb.org/v1/servers/'

limit = 40
params = {
    'limit': limit
}

###############################################################################
###Check for and change to correct path

def check_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


# Logging
# This script uses print statements in the terminal output, to inform you if a
# critical error occurs. Other information, e.g. amount of collected posts is
# saved to 'mastodata_hashtag.log'. 
# Most loggings are also print statements so you can see them if you execute 
# the script via terminal.
logging.basicConfig(filename='mastodata_hashtag.log', level=logging.INFO, format='%(asctime)s %(message)s')


#######################################################################
############ Using fedidb to get a list of mastodon domains     #######
# This step is skipped, if you wish to collect data only from   #######
# specific isntances.                                           #######
#######################################################################
# Collecting domains from fedidb and extracting Mastodon #      #######
# domains is done in two steps. First query_fedidb collects     #######
# the domains of registered instances with fedidb's API.        #######
# More info here: https://fedidb.org/docs/api/v1                #######
# Domains are saved in 'fediverse'.                             #######
# Afterwards 'get_intances' extracts only the mastodon domains. #######
# Domains are saved in 'instances'.                             #######
#######################################################################         

######### Getting fedidb instances#####################################        
        
def query_fedidb(url, params=dict()):
    fediverse = []
    more = True
    while more:

            if 'limit=' not in url:
                response = requests.get(url, params=params)
            else:
                response = requests.get(url)


            if response.status_code == 200:
                data_raw = response.json()
            else:
                data_raw = dict()

            #Overwrite initial request link with new link
            if 'links' in data_raw and 'next' in data_raw['links']:
                url = (data_raw['links']['next'])
            else:
                more = False

            if url is None:
                more = False

            fediverse.extend(data_raw['data'])
    return fediverse

######## Extracting Mastodon domains and writing them to 'instances' #####

def get_instances(url, params=dict()):
    fediverse = query_fedidb(url, params=params)
    fediverse_df = pd.json_normalize(fediverse)
    mastodon_df = fediverse_df[fediverse_df['software.name'] == keep]
    return mastodon_df['domain'].tolist()

##########################################################################
################Getting old hashtag timeline##############################
##########################################################################            
def get_old_timeline_hashtag(instance,  hashtags, outpath_base, since=datetime.now()-timedelta(days=1), limit=40):

    ### params #############################
    app_name = f'mastodata-{instance}'
    api_base_url = f'https://{instance}'

    #os.path.join nutzen
    secrets_path = 'secrets'
    check_dir(secrets_path)
    app_secret_file = f'{secrets_path}/mastodata_{instance}.secret'

    # Generating access hash, saved in the folder "secrets",
    # for each instance.
    Mastodon.create_app(
        app_name,
        api_base_url = api_base_url,
        to_file = app_secret_file
    )

    mastodon = Mastodon(client_id = app_secret_file)

    # Checking if "hashtags" is a string or list
    if isinstance(hashtags, str):
        hashtags = [hashtags]
    elif isinstance(hashtags, list):
        hashtags = hashtags
    else:
        print('Hashtags must be a string or a list of strings')
        return

    now = pd.Timestamp('now', tz='utc') 
    
    # Handing over your date choice 
    if isinstance(since, str):
        since = parser.parse(since)
    elif isinstance(since, datetime):
        since = since
    else:
        print('Since must be a string or a datetime object')
        return
    # Collecting toots and writing them to 'toots'
    toots = []
    for hashtag in hashtags:

        get_more = True
        max_id=None
        outpath = os.path.join(outpath_base)
        check_dir(outpath)
        while get_more:            
            tmp = mastodon.timeline_hashtag(hashtag, limit=limit, max_id=max_id)
            if len(tmp) > 0:
                toots += tmp
                max_id = tmp[-1]['id']
                if tmp[-1]['created_at'] < since: 
                    get_more = False
            else:
                get_more = False

        toots = [toot for toot in toots if toot['created_at'] >= since]
       
        logging.info(f'{datetime.now()}: Number of toots retrieved from {instance} for #{hashtag}: {len(toots)} ')
        print(f'{datetime.now()}: Number of toots retrieved from {instance} for #{hashtag}: {len(toots)} ')
        if len(toots) > 0:
            outfile = os.path.join(outpath, f'{hashtag}_{instance}_start_date_{since}_end_date_{now}.json')

            with open(outfile, 'w') as of:
                txt = json.dumps(toots, indent=4, default=str)
                of.write(txt)         
   
#########################################################################     
#################### Getting hourly hashtag timeline ####################        
#########################################################################

def get_hourly_timeline_hashtag(instance, hashtags, outpath_base, limit=40):

        ### params #############################
    app_name = f'mastodata-{instance}'
    api_base_url = f'https://{instance}'


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
     # Prüfen ob hastags ein string ist oder eine Liste:
    if isinstance(hashtags, str):
        hashtags = [hashtags]
    elif isinstance(hashtags, list):
        hashtags = hashtags
    else:
        print('Hashtags must be a string or a list of strings')
        return

    now = pd.Timestamp('now', tz='utc') 
    now = now.replace(minute=0, second=0, microsecond=0)
    timeoffset = pd.DateOffset(hours=1)
    since = now - timeoffset

    toots = []
    for hashtag in hashtags:

        get_more = True
        max_id=None
        outpath = os.path.join(outpath_base)
        check_dir(outpath)
        while get_more:            
            tmp = mastodon.timeline_hashtag(hashtag, limit=limit, max_id=max_id)
            if len(tmp) > 0:
                toots += tmp
                max_id = tmp[-1]['id']
                if tmp[-1]['created_at'] < since: 
                    get_more = False
            else:
                get_more = False

        toots = [toot for toot in toots if toot['created_at'] >= since]
        # Logging amount of retrieved toots per instance
        logging.info(f'{datetime.now()}: Number of toots retrieved from {instance} for #{hashtag}: {len(toots)} ')
        print(f'{datetime.now()}: Number of toots retrieved from {instance} for #{hashtag}: {len(toots)} ')
        if len(toots) > 0:
            outfile = os.path.join(outpath, f'{hashtag}_{instance}_{now}.json')

            with open(outfile, 'w') as of:
                txt = json.dumps(toots, indent=4, default=str)
                of.write(txt)  


def runner(instances):

##### Get mastodon domains from 'instances###############  
    if len(instances) == 0:
        print('Query fedidb')
        instances = get_instances(fedidb_url, params=params)

    

##### if-condition for the retrieval of older posts
    if retrieve_old_timeline_hashtag == True:
        for instance in instances:
            outpath_base = os.path.join('data', f'hashtag search – {hashtags if isinstance(hashtags, str) else ", ".join(hashtags)}')
            # Some instance block data collection via generic API access. 
            # To prevent the entire collection from crashing "try" is used.
            try:
                get_old_timeline_hashtag(instance, hashtags, outpath_base=outpath_base, since=since, limit=40)
            except:
                print(f'Error retrieving data from instance: {instance}. Check if instance requires authentication.')  
                logging.error(f'Error retrieving data from instance: {instance}. Check if instance requires authentication.')

##### if-condition for hourly collection

    elif retrieve_hourly_timeline_hashtag == True: 
        for instance in instances:
            outpath_base = os.path.join('data', f'hashtag hourly - {hashtags if isinstance(hashtags, str) else ", ".join(hashtags)}')
            try: 
                get_hourly_timeline_hashtag(instance,  hashtags, outpath_base=outpath_base)
            except:
                print(f'Error retrieving data from instance: {instance}. Check if instance requires authentication.')
                logging.error(f'Error retrieving data from instance: {instance}. Check if instance requires authentication.')
   
    else:
        print('Please set one of the timeline retrievals to "True" in the parameters at the very top.')

#Envokes every other function
runner(instances)

