from database import Base
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Float
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
# Define application Bases


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_uuid = Column(String(36), unique=True, nullable=False)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password = Column(String(256), nullable=False)
    active = Column(Boolean, default=1)
    email = Column(String(120), unique=True, nullable=False)
    last_login = Column(DateTime)
    login_count = Column(Integer)
    fail_login_count = Column(Integer)
    created_on = Column(DateTime, default=datetime.now, nullable=True)
    changed_on = Column(DateTime, default=datetime.now, nullable=True)
    created_by_fk = Column(Integer)
    changed_by_fk = Column(Integer)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return int(self.id)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        if self.last_name and self.first_name:
            return '{} {}'.format(
                self.first_name,
                self.last_name
            )


class TaskType(Base):
    __tablename__ = 'task_types'
    id = Column(Integer, primary_key=True)
    task_type = Column(String(64), nullable=False, unique=True)
    is_active = Column(Boolean)

    def __repr__(self):
        if self.task_type is not None:
            return '{}'.format(
                int(self.id),
                str(self.task_type)
            )


class ReminderType(Base):
    __tablename__ = 'reminder_types'
    id = Column(Integer, primary_key=True)
    reminder_type = Column(String(64), nullable=False, unique=True)
    is_active = Column(Boolean)

    def __repr__(self):
        if self.id and self.reminder_type is not None:
            return '{} {}'.format(
                int(self.id),
                str(self.reminder_type)
            )


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    task_uuid = Column(String(36), unique=True, nullable=False)
    task_type_id = Column(ForeignKey('task_types.id'), nullable=False)
    task_type = relationship('TaskType')
    task_name = Column(String(64))
    task_description = Column(String(1024))
    task_created_on = Column(DateTime, default=datetime.now, nullable=True)
    task_last_changed_on = Column(DateTime, default=datetime.now, nullable=True)
    task_due_date = Column(DateTime)
    task_completed = Column(Boolean, default=0)
    task_completed_date = Column(DateTime)
    task_reminders = Column(Boolean, default=0)
    task_uri = Column(String(255), default=None, nullable=False)

    def __repr__(self):
        if self.id and self.task_name is not None:
            return '{}-{}'.format(
                self.id,
                self.task_name
            )

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TaskReminder(Base):
    __tablename__ = 'task_reminders'
    id = Column(Integer, primary_key=True)
    task_id = Column(ForeignKey('tasks.id'), nullable=False)
    reminder_type = Column(ForeignKey('reminder_types.id'), nullable=False)
    reminder_date = Column(DateTime)
    reminder_text = Column(String(255), nullable=False)
    reminder_delta_type = Column(String(64), nullable=False)
    reminder_delta_value = Column(Integer)
    reminder_completed = Column(Boolean, default=0)
    reminder_sent = Column(Boolean, default=0)
    reminder_sent_date = Column(DateTime)

    def __repr__(self):
        if self.task_id and self.reminder_type is not None:
            return '{} {} {}'.format(
                int(self.task_id),
                str(self.reminder_type),
                self.reminder_date.strftime('%Y-%m-%d %H:%M:%S'),
                str(self.reminder_text)
            )


