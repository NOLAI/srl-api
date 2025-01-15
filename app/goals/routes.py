from fastapi import APIRouter

import os
import pandas as pd
import json

from app.db.models import TraceData

router = APIRouter(prefix="/api/goals", tags=["process"])

@router.get(
    "/{user_id}/{course_id}",
    status_code=200,
)
async def get_goals(user_id: int, course_id: int):
    csv_path = os.path.join(os.getenv('DATA_DIR'), f'goals/{user_id}_{course_id}.csv')
    if not os.path.exists(csv_path):
        return []
    
    trace = await TraceData.filter(user_id=user_id, process_label__isnull=False, course_id=course_id).order_by('save_time')
    if not len(trace):
        return []
    essay_start_time = int(trace[0].save_time)
    
    df_goals = pd.read_csv(csv_path, delimiter=';')
    df_goals['time'] = df_goals['time'] - essay_start_time
    df_goals = df_goals[['time']].join([
        df_goals['structure'].apply(json.loads),
        df_goals['relevance'].apply(json.loads),
        df_goals['main_points'].apply(json.loads),
    ])

    return [
        {
            'name': 'structure',
            'subgoals': [{'name': k, 'completed': v} for k, v in df_goals.iloc[-1]['structure'].items()],
            'events': [event for event in [{'time': int(df_goals.iloc[i]['time']), 'names': [k for k, v in df_goals.iloc[i]['structure'].items() if v and (i == 0 or not df_goals.iloc[i-1]['structure'][k])]} for i in range(len(df_goals))] if len(event['names'])],
        },
        {
            'name': 'relevance',
            'subgoals': [{'name': ('paragraph', {'number': k+1}), 'completed': v,} for k, v in enumerate(df_goals.iloc[-1]['relevance'])],
            'events': [{'time': int(df_goals.iloc[i]['time']), 'names': []} for i in range(len(df_goals)) if (i == 0 and len(df_goals.iloc[i]['relevance'])) or (i > 0 and df_goals.iloc[i]['relevance'] > df_goals.iloc[i-1]['relevance'])],
        },
        {
            'name': 'main_points',
            'subgoals': [{'name': ('main_point', {'name': k}), 'completed': v} for k, v in df_goals.iloc[-1]['main_points'].items()],
            'events': [event for event in [{'time': int(df_goals.iloc[i]['time']), 'names': [('main_point', {'name': k}) for k, v in df_goals.iloc[i]['main_points'].items() if v and (i == 0 or not df_goals.iloc[i-1]['main_points'][k])]} for i in range(len(df_goals))] if len(event['names'])],
        },
    ]