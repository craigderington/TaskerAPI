#! .env/bin/python

from flask import Flask, g, Response, request, jsonify, abort, make_response, url_for, flash
from flask_restful import Api, Resource, reqparse, fields, marshal
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from sqlalchemy import exc
from celery import Celery
from database import db_session
from models import Task, TaskType, User
from flask_mail import Mail, Message
from schemas import task_schema
from datetime import datetime
import json
import config

# define app 
app = Flask(__name__)

# define our login_manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/api/v1.0/auth/login"
login_manager.login_message = "Login required to access this site."
login_manager.login_message_category = "primary"

# api wrapper
api = Api(app)

# top secret stuff
app.config['SECRET_KEY'] = config.SECRET_KEY

# disable strict slashes
app.url_map.strict_slashes = False

# celery config
app.config['CELERY_BROKER_URL'] = config.CELERY_BROKER_URL
app.config['CELERY_RESULT_BACKEND'] = config.CELERY_RESULT_BACKEND
app.config['CELERY_ACCEPT_CONTENT'] = config.CELERY_ACCEPT_CONTENT
app.config.update(accept_content=['json', 'pickle'])

# initialize celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# config mail
mail = Mail(app)


# clear all db sessions at the end of each request
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


# load the user
@login_manager.user_loader
def load_user(id):
    try:
        return db_session.query(User).get(int(id))
    except exc.SQLAlchemyError as err:
        return None


# run before each request
@app.before_request
def before_request():
    g.user = current_user


# unauthorized
@login_manager.unauthorized_handler
def unauthorized():
    """
    Unauthorized Handler
    :return:
    """
    data = 'Unauthorized Access.  Permission Denied!'
    resp = Response(
        response=json.dumps(data),
        status=401,
        mimetype='application/json'
    )
    return resp


# tasks sections, for async functions, etc...
@celery.task(serializer='pickle')
def send_async_email(msg):
    """Background task to send an email with Flask-Mail."""
    with app.app_context():
        mail.send(msg)


# fields for marshalling
task_fields = {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'task_uuid': fields.String,
    'task_type': fields.String,
    'task_name': fields.String,
    'task_description': fields.String,
    'task_created_on': fields.DateTime,
    'task_last_changed_on': fields.DateTime,
    'task_due_date': fields.DateTime,
    'task_completed': fields.Boolean,
    'task_completed_date': fields.DateTime,
    'task_reminders': fields.Boolean,
    'task_uri': fields.Url('task')
}


class TaskListAPI(Resource):
    """
    API Resource for listing all tasks from the database.
    Provides the endpoint for creating new tasks
    :param: logged in user's user_pk_id
    :type a json object
    :return task list by user, status_code
    """
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('id', type=int, required=False,
                                   help='The API URL\'s ID of the task.')
        self.reqparse.add_argument('task_name', type=str, required=True,
                                   help='The name for the task.')
        self.reqparse.add_argument('task_description', type=str, required=False,
                                   help='The description for the task.')
        self.reqparse.add_argument('task_due_date', type=str, required=True,
                                   help='The task due date.')
        self.reqparse.add_argument('task_reminders', type=bool, required=False,
                                   help='Has the task reminder been sent.')
        self.reqparse.add_argument('task_completed', type=bool, required=False,
                                   help='Has the task been completed.')
        self.reqparse.add_argument('task_completed_date', type=str, required=False,
                                   help='Task completed date.')
        self.reqparse.add_argument('task_uri', type=str, required=False,
                                   help='The full URL path to the requested resource')

        super(TaskListAPI, self).__init__()

    @login_required
    def get(self):
        try:
            tasks = db_session.query(Task).filter(
                Task.user_id == current_user.id
            ).all()

            if tasks:
                # marshal the fields
                m_data = marshal(tasks, task_fields)
                resp = Response(
                    response=json.dumps(m_data),
                    status=200,
                    mimetype='application/json'
                )

                return resp

            return {'tasks': 'No Tasks Found for ID...'}

        except exc.SQLAlchemyError as db_err:
            return {'error': str(db_err)}

    def post(self):
        try:
            args = self.reqparse.parse_args()
            data = request.get_json()
            task = task_schema.make_task(data)
            m_data = marshal(task, task_fields)

            resp = Response(
                response=json.dumps(m_data),
                status=201,
                mimetype='application/json'
            )

            return resp

        except Exception as e:
            return {'error': str(e)}


class TaskAPI(Resource):
    """
    API Resource for retrieving, modifying, updating and deleting a single
    task, by ID.
    :param: task_id
    :return: task details by ID.
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('id', type=int, required=False,
                                   help='The API URL\'s ID of the task.')
        self.reqparse.add_argument('task_name', type=str, required=True,
                                   help='The name of the user task.',
                                   location='args')
        self.reqparse.add_argument('task_description', type=str, required=False,
                                   help='The task description',
                                   location='args')
        self.reqparse.add_argument('task_due_date', type=str, required=True,
                                   help='The date the task was created.',
                                   location='args')
        self.reqparse.add_argument('task_completed', type=bool, required=False,
                                   help='Has the task been completed.',
                                   location='args')
        self.reqparse.add_argument('task_completed_date', type=str, required=False,
                                   help='Task completed date.',
                                   location='args')
        self.reqparse.add_argument('task_reminders', type=bool, required=False,
                                   help='Has the task reminder been sent?',
                                   location='args')
        self.reqparse.add_argument('task_uri', type='str', required=False,
                                   help='The full URL path to the requested resource')
        super(TaskAPI, self).__init__()

    @login_required
    def get(self, id):
        try:
            task = db_session.query(Task).filter(
                Task.id == id,
                Task.user_id == g.user.id
            ).first()

            if task:
                m_data = marshal(task, task_fields)
                resp = Response(
                    response=json.dumps(m_data),
                    status=200,
                    mimetype='application/json'
                )

            else:
                str_err = {'message': 'No records found.  Try adding a new task...'}
                resp = Response(
                    response=json.dumps(str_err),
                    status=200,
                    mimetype='application/json'
                )

            return resp

        except exc.SQLAlchemyError as db_err:
            resp = Response(
                response=str(db_err),
                status=200,
                mimetype='application/json'
            )
            return resp

    @login_required
    def put(self, id):
        try:
            pass
        except Exception as e:
            return {'error': str(e)}

    @login_required
    def delete(self, id):
        try:
            pass
        except Exception as e:
            return {'error': str(e)}


class UserLogin(Resource):
    """
    User Login Resource
    :param username, password
    :return redirect
    """

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('username')
        self.reqparse.add_argument('password')
        super(UserLogin, self).__init__()

    def post(self):
        """
        The method allowing user to POST login credentials
        :return: login
        """
        data = self.reqparse.parse_args()
        user = db_session.query(User).filter_by(username=data['username']).first()

        if not user or not user.check_password(data['password']):
            return {'message': 'Invalid login credentials...'.format(data['username'])}

        # login the user
        login_user(user)
        return {
            'current_user': g.user.username,
            'logged_in': True,
            'status': 200
        }


@login_required
def send_email(to, subject, msg_body, **kwargs):
    """
    Send Mail function
    :param to:
    :param subject:
    :param template:
    :param kwargs:
    :return: celery async task id
    """
    msg = Message(
        subject,
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[to, ]
    )
    msg.body = "Tasker API"
    msg.html = msg_body
    send_async_email.delay(msg)


# register the API resources and define endpoints
api.add_resource(TaskListAPI, '/api/v1.0/tasks', endpoint='tasks')
api.add_resource(TaskAPI, '/api/v1.0/tasks/<int:id>', endpoint='task')
api.add_resource(UserLogin, '/api/v1.0/auth/login', endpoint='login')


if __name__ == '__main__':
    app.run(
        debug=config.DEBUG,
        port=config.PORT
    )
