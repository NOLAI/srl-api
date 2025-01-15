from fastapi import APIRouter

from app.db.models import TraceData

import os
import pandas as pd

router = APIRouter(prefix="/api/process", tags=["process"])

@router.get(
    "/{user_id}/{course_id}",
    status_code=200,
)
async def get_processes(user_id: int, course_id: int):
    trace = await TraceData.filter(user_id=user_id, process_label__isnull=False, course_id=course_id).order_by('save_time')
    if not len(trace):
        return []
    essay_start_time = int(trace[0].save_time)
    trace = [{
        'type': PROCESSES[row.process_label]['type'],
        'process': PROCESSES[row.process_label]['process'],
        'colour': PROCESSES[row.process_label]['colour'],
        'start_time': int(row.save_time) - essay_start_time,
        } for row in trace]
    trace = [row for i, row in enumerate(trace) if i == 0 or row['process'] != trace[i-1]['process']]
    trace = [{
        **row,
        'end_time': int(trace[i + 1]['start_time'] if i + 1 < len(trace) else row['start_time']),
        } for i, row in enumerate(trace) if row['process'] != 'essay_task_start' and row['process'] != 'essay_task_end']
    
    csv_path = os.path.join(os.getenv('DATA_DIR'), f'nlp/{user_id}_{course_id}.csv')
    if os.path.exists(csv_path):
        df_nlp = pd.read_csv(csv_path, delimiter=';')

        trace = [row for row in trace if row['process'] != 'writing']

        for _, row in df_nlp.iterrows():
            trace.append({
                # 'process_label': str(row['label']),
                'type': PROCESSES[row['label']]['type'],
                'process': PROCESSES[row['label']]['process'],
                'colour': PROCESSES[row['label']]['colour'],
                'start_time': int(row['start_time']) - essay_start_time,
                'end_time': int(row['end_time']) - essay_start_time,
            })

    trace.sort(key=lambda x: x['start_time'])
    return trace

PROCESSES = {
    "MCO1": { "type": "metacognition", "process": "orientation", "colour": "#A6CEE3" },
    "MCO2": { "type": "metacognition", "process": "orientation", "colour": "#A6CEE3" },
    "MCO3": { "type": "metacognition", "process": "orientation", "colour": "#A6CEE3" },
    "MCO4": { "type": "metacognition", "process": "orientation", "colour": "#A6CEE3" },
    "MCO5": { "type": "metacognition", "process": "orientation", "colour": "#A6CEE3" },
    "MCP1": { "type": "metacognition", "process": "planning", "colour": "#1F78B4" },
    "MCP2": { "type": "metacognition", "process": "planning", "colour": "#1F78B4" },
    "MCP3": { "type": "metacognition", "process": "planning", "colour": "#1F78B4" },
    "MCP4": { "type": "metacognition", "process": "planning", "colour": "#1F78B4" },
    "MCE1": { "type": "metacognition", "process": "evaluation", "colour": "#33A02C" },
    "MCE2": { "type": "metacognition", "process": "evaluation", "colour": "#33A02C" },
    "MCM1": { "type": "metacognition", "process": "monitoring", "colour": "#B2DF8A" },
    "MCM2": { "type": "metacognition", "process": "monitoring", "colour": "#B2DF8A" },
    "MCM3": { "type": "metacognition", "process": "monitoring", "colour": "#B2DF8A" },
    "MCM4": { "type": "metacognition", "process": "monitoring", "colour": "#B2DF8A" },
    "MCM5": { "type": "metacognition", "process": "monitoring", "colour": "#B2DF8A" },
    "MCM6": { "type": "metacognition", "process": "monitoring", "colour": "#B2DF8A" },
    "MCM7": { "type": "metacognition", "process": "monitoring", "colour": "#B2DF8A" },
    "MCM8": { "type": "metacognition", "process": "monitoring", "colour": "#B2DF8A" },
    "LCF1": { "type": "cognition", "process": "reading", "colour": "#E31A1C" },
    "LCF2": { "type": "cognition", "process": "reading", "colour": "#E31A1C" },
    "LCF4": { "type": "cognition", "process": "reading", "colour": "#E31A1C" },
    "LCF5": { "type": "cognition", "process": "reading", "colour": "#E31A1C" },
    "LCF6": { "type": "cognition", "process": "reading", "colour": "#E31A1C" },
    "LCF7": { "type": "cognition", "process": "reading", "colour": "#E31A1C" },
    "LCR1": { "type": "cognition", "process": "rereading", "colour": "#FB9A99" },
    "LCR2": { "type": "cognition", "process": "rereading", "colour": "#FB9A99" },
    "HCEO1": { "type": "cognition", "process": "writing", "colour": "#FF7F00" },
    "HCEO2": { "type": "cognition", "process": "writing", "colour": "#FF7F00" },
    "HCEO3": { "type": "cognition", "process": "writing", "colour": "#FF7F00" },
    "HCEO4": { "type": "cognition", "process": "writing", "colour": "#FF7F00" },
    "HCEO5": { "type": "cognition", "process": "organising", "colour": "#FDBF6F" },
    "HCEO6": { "type": "cognition", "process": "organising", "colour": "#FDBF6F" },
    "NO_PATTERN": { "type": "other", "process": "not_detected", "colour": "#EBEBEB" },
    "NOT_RECOGNIZED": { "type": "other", "process": "not_detected", "colour": "#EBEBEB" },
    "ESSAY_TASK_START": { "type": "other", "process": "essay_task_start", "colour": "#FFFFFF" },
    "ESSAY_TASK_END": { "type": "other", "process": "essay_task_end", "colour": "#FFFFFF" },

    "MO": { "type": "metacognition", "process": "orientation", "colour": "#A6CEE3" },
    "MP": { "type": "metacognition", "process": "planning", "colour": "#1F78B4" },
    "ME": { "type": "metacognition", "process": "evaluation", "colour": "#33A02C" },
    "MM": { "type": "metacognition", "process": "monitoring", "colour": "#B2DF8A" },
    "COO": { "type": "cognition", "process": "copying", "colour": "#FF7F00" },
    "CV": { "type": "cognition", "process": "editing", "colour": "#FFD5AD" },
    "COR": { "type": "cognition", "process": "structuring", "colour": "#CD6800" },
    "CE": { "type": "cognition", "process": "expanding", "colour": "#7A0000" },
    "NL": { "type": "other", "process": "not_detected", "colour": "#EBEBEB" },
}