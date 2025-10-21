from tortoise.models import Model
from tortoise import fields


class TraceData(Model):
    id = fields.IntField(pk=True)
    user_id = fields.IntField()
    course_id = fields.IntField()
    save_time = fields.BigIntField()
    process_label = fields.CharField(max_length=255)

    class Meta:
        table = "trace_data_real_time_process"

    def __str__(self):
        return self.process_label
    
class WritingProcess(Model):
    id = fields.IntField(pk=True)
    user_id = fields.IntField(null=False)
    course_id = fields.IntField(null=False)
    start_time = fields.BigIntField(null=False)
    end_time = fields.BigIntField(null=False)
    process_label = fields.CharField(max_length=255, null=False)

    class Meta:
        table = "writing_process"

    def __str__(self):
        return self.process_label
    
class Essay(Model):
    id = fields.IntField(pk=True)
    user_id = fields.IntField()
    course_id = fields.IntField()
    save_time = fields.BigIntField()
    essay_content = fields.TextField()

    class Meta:
        table = "essay"

    def __str__(self):
        return self.essay_content
    
class EssayProductGoals(Model):
    id = fields.IntField(pk=True)
    essay = fields.ForeignKeyField("models.Essay", related_name="product_goals")
    structure = fields.JSONField()
    relevance = fields.JSONField()
    main_points = fields.JSONField()

    class Meta:
        table = "essay_product_goals"

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