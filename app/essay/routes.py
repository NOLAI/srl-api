from fastapi import APIRouter
from tortoise import connections

from app.db.models import MdlCourse, TraceData

router = APIRouter(prefix="/api/essay", tags=["user"])

@router.get(
    "/list/{user_id}",
    status_code=200,
)
async def get_essays_list(user_id: int):
    db_moodle = connections.get('moodle')

    course_ids = await TraceData.filter(user_id=user_id, process_label__isnull=False).distinct().values('course_id')

    essays = []

    for course_id in course_ids:
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
                'name_en': name_en
            })
        except:
            pass

    return essays
