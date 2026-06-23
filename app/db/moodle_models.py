from tortoise import fields
from tortoise.models import Model


class MdlUser(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=255)

    class Meta:
        table = "mdl_user"

    def __str__(self):
        return self.username


class MdlCourse(Model):
    id = fields.IntField(pk=True)
    fullname = fields.CharField(max_length=255)
    shortname = fields.CharField(max_length=255)

    class Meta:
        table = "mdl_course"

    def __str__(self):
        return self.fullname


class MdlPage(Model):
    id = fields.IntField(pk=True)
    course = fields.IntField()
    name = fields.CharField(max_length=255)
    content = fields.TextField()

    class Meta:
        table = "mdl_page"

    def __str__(self):
        return self.name


class MdlQuestionnaire(Model):
    id = fields.IntField(pk=True)
    course = fields.IntField()
    name = fields.CharField(max_length=255)

    class Meta:
        table = "mdl_questionnaire"

    def __str__(self):
        return self.name


class MdlQuestionnaireQuestion(Model):
    id = fields.IntField(pk=True)
    surveyid = fields.IntField()
    name = fields.CharField(max_length=255)
    content = fields.TextField()
    type_id = fields.IntField()

    class Meta:
        table = "mdl_questionnaire_question"


class MdlQuestionnaireQuestionType(Model):
    id = fields.IntField(pk=True)
    typeid = fields.IntField()
    type = fields.CharField(max_length=255)
    has_choices = fields.CharField(max_length=255)
    response_table = fields.CharField(max_length=255)

    class Meta:
        table = "mdl_questionnaire_question_type"


class MdlQuestionnaireQuestionChoice(Model):
    id = fields.IntField(pk=True)
    question_id = fields.IntField()
    content = fields.TextField()

    class Meta:
        table = "mdl_questionnaire_quest_choice"


class MdlQuestionnaireResponse(Model):
    id = fields.IntField(pk=True)
    questionnaireid = fields.IntField()
    userid = fields.IntField()

    class Meta:
        table = "mdl_questionnaire_response"


class MdlQuestionnaireResponseBool(Model):
    id = fields.IntField(pk=True)
    response_id = fields.IntField()
    question_id = fields.IntField()
    choice_id = fields.CharField(max_length=255)

    class Meta:
        table = "mdl_questionnaire_response_bool"


class MdlQuestionnaireResponseText(Model):
    id = fields.IntField(pk=True)
    response_id = fields.IntField()
    question_id = fields.IntField()
    response = fields.TextField()

    class Meta:
        table = "mdl_questionnaire_response_text"


class MdlQuestionnaireResponseMultiple(Model):
    id = fields.IntField(pk=True)
    response_id = fields.IntField()
    question_id = fields.IntField()
    choice_id = fields.IntField()

    class Meta:
        table = "mdl_questionnaire_resp_multiple"


class MdlQuestionnaireResponseSingle(Model):
    id = fields.IntField(pk=True)
    response_id = fields.IntField()
    question_id = fields.IntField()
    choice_id = fields.IntField()

    class Meta:
        table = "mdl_questionnaire_resp_single"


class MdlQuestionnaireResponseRank(Model):
    id = fields.IntField(pk=True)
    response_id = fields.IntField()
    question_id = fields.IntField()
    choice_id = fields.IntField()
    rankvalue = fields.IntField()

    class Meta:
        table = "mdl_questionnaire_response_rank"
