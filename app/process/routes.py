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
                'type': PROCESSES[row['label']]['type'],
                'process': PROCESSES[row['label']]['process'],
                'start_time': int(row['start_time']) - essay_start_time,
                'end_time': int(row['end_time']) - essay_start_time,
            })

    trace.sort(key=lambda x: x['start_time'])
    return trace

PROCESSES = {
    "MCO1": { "type": "metacognition", "process": "orientation"},
    "MCO2": { "type": "metacognition", "process": "orientation"},
    "MCO3": { "type": "metacognition", "process": "orientation"},
    "MCO4": { "type": "metacognition", "process": "orientation"},
    "MCO5": { "type": "metacognition", "process": "orientation"},
    "MCP1": { "type": "metacognition", "process": "planning"},
    "MCP2": { "type": "metacognition", "process": "planning"},
    "MCP3": { "type": "metacognition", "process": "planning"},
    "MCP4": { "type": "metacognition", "process": "planning"},
    "MCE1": { "type": "metacognition", "process": "evaluation"},
    "MCE2": { "type": "metacognition", "process": "evaluation"},
    "MCM1": { "type": "metacognition", "process": "monitoring"},
    "MCM2": { "type": "metacognition", "process": "monitoring"},
    "MCM3": { "type": "metacognition", "process": "monitoring"},
    "MCM4": { "type": "metacognition", "process": "monitoring"},
    "MCM5": { "type": "metacognition", "process": "monitoring"},
    "MCM6": { "type": "metacognition", "process": "monitoring"},
    "MCM7": { "type": "metacognition", "process": "monitoring"},
    "MCM8": { "type": "metacognition", "process": "monitoring"},
    "LCF1": { "type": "cognition", "process": "reading"},
    "LCF2": { "type": "cognition", "process": "reading"},
    "LCF3": { "type": "cognition", "process": "reading"},
    "LCF4": { "type": "cognition", "process": "reading"},
    "LCF5": { "type": "cognition", "process": "reading"},
    "LCF6": { "type": "cognition", "process": "reading"},
    "LCF7": { "type": "cognition", "process": "reading"},
    "LCR1": { "type": "cognition", "process": "rereading"},
    "LCR2": { "type": "cognition", "process": "rereading"},
    "HCEO1": { "type": "cognition", "process": "writing"},
    "HCEO2": { "type": "cognition", "process": "writing"},
    "HCEO3": { "type": "cognition", "process": "writing"},
    "HCEO4": { "type": "cognition", "process": "writing"},
    "HCEO5": { "type": "cognition", "process": "organising"},
    "HCEO6": { "type": "cognition", "process": "organising"},
    "NO_PATTERN": { "type": "other", "process": "not_detected"},
    "NOT_RECOGNIZED": { "type": "other", "process": "not_detected"},
    "ESSAY_TASK_START": { "type": "other", "process": "essay_task_start"},
    "ESSAY_TASK_END": { "type": "other", "process": "essay_task_end"},

    "MO": { "type": "metacognition", "process": "orientation"},
    "MP": { "type": "metacognition", "process": "planning"},
    "ME": { "type": "metacognition", "process": "evaluation"},
    "MM": { "type": "metacognition", "process": "monitoring"},
    "COO": { "type": "cognition", "process": "copying"},
    "CV": { "type": "cognition", "process": "editing"},
    "COR": { "type": "cognition", "process": "structuring"},
    "CE": { "type": "cognition", "process": "expanding"},
    "NL": { "type": "other", "process": "not_detected"},
}