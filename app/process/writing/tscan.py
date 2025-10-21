import asyncio
import os
import uuid
import requests
from xml.etree import cElementTree as ET
import pandas as pd
import io

TSCAN_API_URL = os.getenv('TSCAN_API_URL')
TSCAN_API_USERNAME = os.getenv('TSCAN_API_USERNAME')
TSCAN_API_PASSWORD = os.getenv('TSCAN_API_PASSWORD')

async def run(segmented_essays):
    project_id = create_project()
    for i, essay_segment in segmented_essays.iterrows():
        text = essay_segment['text_written'].strip()
        if not text:
            continue
        add_text(project_id, f"{essay_segment['cluster_nr']}.txt", text)
    start_execution(project_id)
    while not is_done(project_id):
        await asyncio.sleep(1)
    df_results = get_results(project_id)
    delete_project(project_id)
    return df_results

def create_project():
    project_id = str(uuid.uuid4()).replace('-', '')
    response = requests.put(
        f"{TSCAN_API_URL}/{project_id}",
        auth=(TSCAN_API_USERNAME, TSCAN_API_PASSWORD),
    )
    if response.status_code == 201:
        return project_id
    else:
        raise Exception(f"Failed to create TSCAN project: {response.text}")


def add_text(project_id, filename, text):
    response = requests.post(
        f"{TSCAN_API_URL}/{project_id}/input/{filename}",
        params={'inputtemplate': 'textinput'},
        files={'file': text.encode('utf-8')},
        auth=(TSCAN_API_USERNAME, TSCAN_API_PASSWORD),
    )
    if response.status_code != 200:
        raise Exception(f"Failed to add text to TSCAN project: {response.text}")
    
def start_execution(project_id):
    response = requests.post(
        f"{TSCAN_API_URL}/{project_id}",
        auth=(TSCAN_API_USERNAME, TSCAN_API_PASSWORD),
    )
    if response.status_code != 202:
        raise Exception(f"Failed to start TSCAN execution: {response.text}")
    
def get_status(project_id):
    response = requests.get(
        f"{TSCAN_API_URL}/{project_id}",
        auth=(TSCAN_API_USERNAME, TSCAN_API_PASSWORD),
    )
    if response.status_code == 200:
        xml = response.text
        root = ET.fromstring(xml)
        status = int(root.find('status').get('code'))
        return status
    else:
        raise Exception(f"Failed to get TSCAN project status: {response.text}")

def is_done(project_id):
    status = get_status(project_id)
    return status == 2

def get_results(project_id):
    response = requests.get(
        f"{TSCAN_API_URL}/{project_id}/output/total.document.csv",
        auth=(TSCAN_API_USERNAME, TSCAN_API_PASSWORD),
    )
    if response.status_code == 200:
        csv = response.text
        df = pd.read_csv(io.StringIO(csv))
        return df
    else:
        raise Exception(f"Failed to get TSCAN project results: {response.text}")
    
def delete_project(project_id):
    response = requests.delete(
        f"{TSCAN_API_URL}/{project_id}",
        auth=(TSCAN_API_USERNAME, TSCAN_API_PASSWORD),
    )
    if response.status_code != 200:
        raise Exception(f"Failed to delete TSCAN project: {response.text}")