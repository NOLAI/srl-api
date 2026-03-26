import json
import os
from fastapi import APIRouter
from tortoise import connections
from tortoise.functions import Max

from app.db.models import MdlCourse, TraceData

router = APIRouter(prefix="/api/essay", tags=["user"])

@router.get(
    "/list/{user_id}",
    status_code=200,
)
async def get_essays_list(user_id: int):
    db_moodle = connections.get('moodle')

    ignored_courses = []
    ignored_courses_path = os.path.join(os.getenv('DATA_DIR'), 'ignored_courses.json')
    if os.path.exists(ignored_courses_path):
        with open(ignored_courses_path, 'r') as file:
            try:
                ignored_courses = json.loads(file.read())
            except:
                pass

    course_to_questionnaire_mapping = {}
    course_questionnaires_path = os.path.join(os.getenv('DATA_DIR'), 'course_questionnaires.json')
    if os.path.exists(course_questionnaires_path):
        with open(course_questionnaires_path, 'r') as file:
            try:
                course_to_questionnaire_mapping = json.loads(file.read())
            except:
                pass

    course_ids = await TraceData.filter(user_id=user_id, process_label__isnull=False).annotate(save_time_max=Max('save_time')).distinct().group_by('course_id').order_by('save_time_max').values('course_id', 'save_time_max')

    essays = []

    for course_id in course_ids:
        if int(course_id['course_id']) in ignored_courses:
            continue
        try:
            course = await MdlCourse.get(id=course_id['course_id'], using_db=db_moodle)
            name_en = course.fullname if course.fullname else "Essay "+str(course_id['course_id'])
            name_nl = name_en
            if '{mlang}' in course.fullname:
                name_en = course.fullname.split('{mlang en}')[1].split('{mlang}')[0]
                name_nl = course.fullname.split('{mlang nl}')[1].split('{mlang}')[0] if '{mlang nl}' in course.fullname else name_en

            essays.append({
                'course_id': int(course_id['course_id']),
                'name_nl': name_nl,
                'name_en': name_en,
                'questionnaire_id': course_to_questionnaire_mapping.get(str(course_id['course_id'])),
            })
        except:
            pass

    return essays
