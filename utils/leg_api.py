import pandas as pd
import numpy as np
import requests
from datetime import datetime
import re
from matplotlib import pyplot as plt
import os 


cc_api_key = os.environ.get('cc_api_key')
TODAY = datetime.today()
SESS_BEGIN = TODAY.replace(year=TODAY.year - ((TODAY.year % 4) - 2), month=1, day=1).strftime("%Y-%m-%d") if (TODAY.year % 4) >= 2 else TODAY.replace(year=TODAY.year - ((TODAY.year % 4) + 2), month=1, day=1).strftime("%Y-%m-%d")
SESS_END = "{}-{}-{}".format(int(SESS_BEGIN.split("-")[0]) + 3, 12, 31)

def process_cm_info(df):
    CM_RAW = df.json()

    for CM in CM_RAW:
        PERSON_DATA = requests.get(url="https://webapi.legistar.com/v1/nyc/Persons/{}/?&token={}".format(CM["OfficeRecordPersonId"], cc_api_key))
        CM_PERSONAL_DATA = PERSON_DATA.json()


        if CM_PERSONAL_DATA['PersonWWW']:
            district_numbers = re.findall('[0-9]+', CM_PERSONAL_DATA['PersonWWW'])
            if district_numbers:
                CM["District"] = int(district_numbers[0])
            else:
                if CM_PERSONAL_DATA['PersonEmail']:
                    district_numbers = re.findall('[0-9]+', CM_PERSONAL_DATA['PersonEmail'])
                    CM["District"] = int(district_numbers[0]) if district_numbers else np.nan
                else:
                    CM["District"] = np.nan
        else:
            CM["District"] = np.nan

        CM['Address'] = CM_PERSONAL_DATA['PersonAddress1']
        CM["City"] = CM_PERSONAL_DATA['PersonCity1']
        CM['Zip'] = CM_PERSONAL_DATA['PersonZip1']

    CM_DATA = sorted(CM_RAW, key=lambda i: i['District'] if not np.isnan(i['District']) else float('inf'))

    return pd.DataFrame(CM_DATA)

def generate_cc_df():
    CM_RAW = requests.get(url="https://webapi.legistar.com/v1/nyc/Bodies/1/OfficeRecords/?$filter=OfficeRecordStartDate+eq+datetime'{}'&token={}".format(SESS_BEGIN, cc_api_key))

    CM_DATA = process_cm_info(CM_RAW)

    CM_DATA.loc[CM_DATA['OfficeRecordFullName'] == 'Joseph C. Borelli', 'District'] = 51
    CM_DATA.loc[CM_DATA['OfficeRecordFullName'] == 'Justin L. Brannan', 'District'] = 43
    CM_DATA = CM_DATA[CM_DATA['OfficeRecordFullName'] != 'Public Advocate Jumaane Williams']
    CM_DATA['District'] = CM_DATA['District'].astype('Int64')

    return CM_DATA

def get_votes():
    all_votes = []

    CM_RAW = requests.get(url="https://webapi.legistar.com/v1/nyc/Bodies/1/OfficeRecords/?$filter=OfficeRecordStartDate+eq+datetime'{}'&token={}".format(SESS_BEGIN, cc_api_key))
    CM_RAW = CM_RAW.json()
    for CM in CM_RAW:
        PERSON_DATA = requests.get(url="https://webapi.legistar.com/v1/nyc/Persons/{}/?&token={}".format(CM["OfficeRecordPersonId"], cc_api_key))
        CM_PERSONAL_DATA = PERSON_DATA.json()
    
        VOTES = requests.get(url="https://webapi.legistar.com/v1/nyc/Persons/{}/votes/?$filter=VoteLastModifiedUtc+gt+datetime'{}'&token={}".format(CM_PERSONAL_DATA["PersonId"], SESS_BEGIN, cc_api_key))
        VOTES_JSON = VOTES.json()
    
        all_votes.extend(VOTES_JSON)

    VOTER = pd.DataFrame(all_votes)
    return VOTER

def find_close_votes(votes):
    df = votes.copy()
    vote_counts = df.groupby(['vote_event_item_id', 'vote_value_name']).size()
    pivot_table = vote_counts.unstack(fill_value=0)
    pivot_table = pivot_table.reset_index()

    pivot_table['anti'] = pivot_table['Negative'] + pivot_table['Abstain']
    pivot_table['total'] = pivot_table['Affirmative'] + pivot_table['anti']
    pivot_table['ratio'] = pivot_table['anti'] / pivot_table['Affirmative']

    pivot_table = pivot_table[pivot_table['ratio'].notna()]
    pivot_table.replace([np.inf, -np.inf], np.nan, inplace=True)

    full = pivot_table[pivot_table['total'] > 45]
    top_ratio = full.sort_values('ratio', ascending=False).head(100)

    ratio_ids = top_ratio['vote_event_item_id'].tolist()
    full_ratio = df[df['vote_event_item_id'].isin(ratio_ids)]

    fr_pivot = full_ratio.pivot_table(index='council_member', columns='vote_event_item_id', values='vote_value_id')
    fr_pivot.dropna(axis=1, how='any', inplace=True)

    return fr_pivot
    
