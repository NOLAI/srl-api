from app.process.const import PROCESSES
from fastapi import APIRouter

from app.db.models import Essay, TraceData, WritingProcess
from app.process.writing.writing import process_writing

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

    writing_processes = await WritingProcess.filter(user_id=user_id, course_id=course_id).order_by('start_time')
    if not len(writing_processes):
        writing_processes = await process_writing(user_id, course_id)
    writing_processes = [{
        'type': PROCESSES[row.process_label]['type'],
        'process': PROCESSES[row.process_label]['process'],
        'start_time': int(row.start_time) - essay_start_time,
        'end_time': int(row.end_time) - essay_start_time,
        } for row in writing_processes]
    trace = [row for row in trace if row['process'] != 'writing']
    trace += writing_processes

    trace.sort(key=lambda x: x['start_time'])
    return trace


@router.get(
    "/process",
    status_code=200,
)
async def process_writing_job():
    print("Running writing processes job...", flush=True)
    sessions = await Essay.all().distinct().values('user_id', 'course_id')
    for session in sessions:
        if not session['user_id'] or not session['course_id']:
            continue
        count = await WritingProcess.filter(user_id=session['user_id'], course_id=session['course_id']).count()
        if count > 0:
            continue
        print(f"Processing writing processes for user {session['user_id']} in course {session['course_id']}...", flush=True)
        await process_writing(session['user_id'], session['course_id'])
    print("Finished product goals job.", flush=True)
    return "done"