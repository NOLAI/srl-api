import os
import requests
import pandas as pd
import json

LIWC_API_URL = os.getenv('LIWC_API_URL')
LIWC_API_KEY = os.getenv('LIWC_API_KEY')
LIWC_API_SECRET = os.getenv('LIWC_API_SECRET')

def run(segmented_essays):
    data = json.dumps([{
        'request_id': str(essay_segment['cluster_nr']),
        'text': essay_segment['text_written'].strip()
    } for i, essay_segment in segmented_essays.iterrows() if essay_segment['text_written'].strip()])
    response = requests.post(f"{LIWC_API_URL}/analyze/written", auth=(LIWC_API_KEY, LIWC_API_SECRET), data=data)
    if response.status_code == 200:
        results = response.json()['results']
        results = list(map(lambda r: {'cluster_nr': int(r['request_id']), **r['summary'], **r['liwc15']}, results))
        return pd.DataFrame(results)
    else:
        raise Exception(f"Failed to get LIWC results: {response.text}")