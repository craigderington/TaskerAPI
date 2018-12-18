from marshmallow_sqlalchemy import ModelSchema
from models import Task, User


class TaskSchema(ModelSchema):

    def make_task(self, data):
        return Task(**data)

    class Meta:
        fields = ('id', 'task_uuid', 'task_name', 'task_description', 'task_due_date', 'task_created_on',
                  'task_last_changed_on', 'task_completed', 'task_completed_date', 'task_reminders',
                  'user_id', 'uri')


task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

