from fastapi import APIRouter

import os
import json

from app.db.models import Essay, EssayProductGoals, TraceData
from app.goals.goals import init_nlp, process_essay, process_essays

router = APIRouter(prefix="/api/goals", tags=["process"])

@router.get(
    "/{user_id}/{course_id}",
    status_code=200,
)
async def get_goals(user_id: int, course_id: int):
    with open(os.path.join(os.getenv('DATA_DIR'), 'goals.json'), 'r') as file:
        tasks = json.loads(file.read())
    if not str(course_id) in tasks:
        return []
    task = tasks[str(course_id)]
    
    trace = await TraceData.filter(user_id=user_id, process_label__isnull=False, course_id=course_id).order_by('save_time')
    if not len(trace):
        return []
    essay_start_time = int(trace[0].save_time)

    essays = await Essay.filter(user_id=user_id, course_id=course_id).order_by('save_time')
    essays = [essay for i, essay in enumerate(essays) if i == len(essays)-1 or int(essays[i+1].save_time) - int(essay.save_time) > 3000]
    if not len(essays):
        return []

    goals = []
    nlp, task_lang = None, None
    for essay in essays:
        essay_goals = await essay.product_goals
        if essay_goals:
            goals.append({
                'time': int(essay.save_time) - essay_start_time,
                'structure': essay_goals[0].structure,
                'relevance': essay_goals[0].relevance,
                'main_points': essay_goals[0].main_points,
            })
        else:
            if nlp is None:
                nlp, task_lang = init_nlp(essays[-1].essay_content, task)
            essay_goals = process_essay(essay.essay_content, task_lang, nlp)
            await EssayProductGoals.create(
                essay_id=essay.id,
                structure=essay_goals['structure'],
                relevance=essay_goals['relevance'],
                main_points=essay_goals['main_points'],
            )
            goals.append({
                'time': int(essay.save_time) - essay_start_time,
                **essay_goals
            })

    return [
        {
            'name': 'structure',
            'subgoals': goals[-1]['structure'],
            'events': [event for event in [{'time': goal['time'], 'names': [s['name'] for j, s in enumerate(goal['structure']) if s['completed'] and (i == 0 or not goals[i-1]['structure'][j]['completed'])]} for i, goal in enumerate(goals)] if len(event['names'])],
        },
        {
            'name': 'relevance',
            'subgoals': [{'name': ('paragraph', {'number': k+1}), 'completed': v,} for k, v in enumerate(goals[-1]['relevance'])],
            'events': [{'time': int(goal['time']), 'names': []} for i, goal in enumerate(goals) if (i == 0 and len(goal['relevance'])) or (i > 0 and sum(goal['relevance']) > sum(goals[i-1]['relevance']))],
        },
        {
            'name': 'main_points',
            'subgoals': [{'name': ('main_point', {'name': m['name']}), 'completed': m['completed']} for m in goals[-1]['main_points']],
            'events': [event for event in [{'time': int(goal['time']), 'names': [('main_point', {'name': m['name']}) for j, m in enumerate(goal['main_points']) if m['completed'] and (i == 0 or not goals[i-1]['main_points'][j]['completed'])]} for i, goal in enumerate(goals)] if len(event['names'])],
        },
    ]

@router.get(
    "/process",
    status_code=200,
)
async def process_essays_job():
    print("Running product goals job...", flush=True)
    with open(os.path.join(os.getenv('DATA_DIR'), 'goals.json'), 'r') as file:
        tasks = json.loads(file.read())
    sessions = await Essay.filter(course_id__in=tasks.keys()).distinct().values('user_id', 'course_id')
    for session in sessions:
        if not session['user_id'] or not session['course_id']:
            continue
        essays = await Essay.filter(user_id=session['user_id'], course_id=session['course_id']).order_by('save_time')
        essays = [{
            'id': int(essay.id),
            'content': essay.essay_content,
        } for i, essay in enumerate(essays) if (i == len(essays)-1 or int(essays[i+1].save_time) - int(essay.save_time) > 3000) and not await essay.product_goals]
        
        if not essays:
            continue

        print(f"Processing {len(essays)} essays for user {session['user_id']} in course {session['course_id']}...", flush=True)
        essays = process_essays(essays, tasks[session['course_id']])
        for essay in essays:
            await EssayProductGoals.create(
                essay_id=essay['id'],
                structure=essay['structure'],
                relevance=essay['relevance'],
                main_points=essay['main_points'],
            )
    
    print("Finished product goals job.", flush=True)
    return "done"