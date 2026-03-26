import json
import os

from fastapi import APIRouter
from tortoise import connections

from app.db.models import MdlCourse, MdlQuestionnaire, MdlQuestionnaireQuestion, MdlQuestionnaireQuestionChoice, MdlQuestionnaireQuestionType, MdlQuestionnaireResponse, MdlQuestionnaireResponseBool, MdlQuestionnaireResponseMultiple, MdlQuestionnaireResponseRank, MdlQuestionnaireResponseSingle, MdlQuestionnaireResponseText
from app.questions.utils import split_lang, strip_html

router = APIRouter(prefix="/api/questions", tags=["user"])

@router.get(
    "/{id}",
    status_code=200,
)
async def get_questions(id: int):
    course_questionnaires = set()
    course_questionnaires_path = os.path.join(os.getenv('DATA_DIR'), 'course_questionnaires.json')
    if os.path.exists(course_questionnaires_path):
        with open(course_questionnaires_path, 'r') as file:
            try:
                course_questionnaires = set(json.loads(file.read()).values())
            except:
                pass    

    db_moodle = connections.get('moodle')
    responses = await MdlQuestionnaireResponse.filter(userid=id).using_db(db_moodle).all()
    responses = [{
        "id": response.id,
        "questionnaire_id": response.questionnaireid,
        "questionnaire": None,
        "user_id": response.userid,
        "questions": [],
    } for response in responses if response.questionnaireid in course_questionnaires]
    for response in responses:
        questionnaire = await MdlQuestionnaire.get(id=response['questionnaire_id'], using_db=db_moodle)
        course = await MdlCourse.get(id=questionnaire.course, using_db=db_moodle)
        response['questionnaire'] = {
            'id': questionnaire.id,
            'name': split_lang(strip_html(questionnaire.name)),
            'course': {
                'id': course.id,
                'name': split_lang(strip_html(course.fullname)),
            },
        }
        questions = await MdlQuestionnaireQuestion.filter(surveyid=response['questionnaire_id']).using_db(db_moodle).all()
        for question in questions:
            try:
                type = await MdlQuestionnaireQuestionType.get(typeid=question.type_id, using_db=db_moodle)
                answer_type = None
                answer_value = None
                if type.response_table == 'response_bool':
                    answer = await MdlQuestionnaireResponseBool.get(response_id=response['id'], question_id=question.id, using_db=db_moodle)
                    answer_type = 'bool'
                    answer_value = True if answer.choice_id == 'y' else False
                elif type.response_table == 'response_text':
                    answer = await MdlQuestionnaireResponseText.get(response_id=response['id'], question_id=question.id, using_db=db_moodle)
                    answer_type = 'text'
                    answer_value = strip_html(answer.response)
                elif type.response_table == 'resp_single':
                    answer = await MdlQuestionnaireResponseSingle.get(response_id=response['id'], question_id=question.id, using_db=db_moodle)
                    choice = await MdlQuestionnaireQuestionChoice.get(id=answer.choice_id, using_db=db_moodle)
                    answer_type = 'single_choice'
                    answer_value = split_lang(strip_html(choice.content))
                elif type.response_table == 'resp_multiple':
                    answers = await MdlQuestionnaireResponseMultiple.filter(response_id=response['id'], question_id=question.id).using_db(db_moodle).all()
                    choices = []
                    for answer in answers:
                        choice = await MdlQuestionnaireQuestionChoice.get(id=answer.choice_id, using_db=db_moodle)
                        choices.append(split_lang(strip_html(choice.content)))
                    answer_type = 'multiple_choice'
                    answer_value = choices
                elif type.response_table == 'response_rank':
                    answers = await MdlQuestionnaireResponseRank.filter(response_id=response['id'], question_id=question.id).using_db(db_moodle).all()
                    choices = []
                    for answer in answers:
                        choice = await MdlQuestionnaireQuestionChoice.get(id=answer.choice_id, using_db=db_moodle)
                        choices.append({
                            'choice': split_lang(strip_html(choice.content)),
                            'rank': answer.rankvalue,
                        })
                    choices = sorted(choices, key=lambda x: x['rank'])
                    answer_type = 'rank'
                    answer_value = choices
                if answer_type is not None:
                    response['questions'].append({
                        'id': question.id,
                        'name': question.name,
                        'content': split_lang(strip_html(question.content)),
                        'answer_type': answer_type,
                        'answer_value': answer_value,
                        'type': type,
                    })
            except Exception:
                continue
    return responses
