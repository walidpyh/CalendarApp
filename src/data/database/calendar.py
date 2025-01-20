import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase

"""
Represents calendar events with details like title, dates, times, color, 
and a relationship to the user who created the event.
"""

class Calendar(SqlAlchemyBase):
    __tablename__ = 'calendar'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    start_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    start_time = sqlalchemy.Column(sqlalchemy.Time, nullable=False)
    end_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    end_time = sqlalchemy.Column(sqlalchemy.Time, nullable=False)
    color = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    users_relationship = orm.relationship("User", back_populates="calendar_relationship")
