from .db_session import SqlAlchemyBase
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
import datetime

"""
Represents a user in the database with attributes like email, name, birthday, 
and avatar. Includes relationships to user-specific data such as calendar events. 
Provides methods for setting and verifying passwords.
"""

import hashlib
import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin
from datetime import datetime
from data.database.db_session import SqlAlchemyBase

class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    bday = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now)
    avatar = sqlalchemy.Column(sqlalchemy.Text, nullable=False, default='profile_default.png')
    # OTP-related fields
    otp_secret = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # Secret for OTP
    otp_enabled = sqlalchemy.Column(sqlalchemy.Boolean, default=False)  # Whether OTP is enabled

    # Relationship with the Calendar model
    calendar_relationship = orm.relationship("Calendar", back_populates="users_relationship")

    def set_password(self, password):
        """
        Hashes the password using SHA256 and sets it to the hashed_password field.
        """
        salt = "CalendarAppSalt6875"  # Salt for more randomness
        salted_password = (password + salt).encode('utf-8')
        self.hashed_password = hashlib.sha256(salted_password).hexdigest()

    def check_password(self, password):
        """
        Verifies the password against the stored hash.
        """
        salt = "CalendarAppSalt6875"  # Salt for more randomness
        salted_password = (password + salt).encode('utf-8')
        hashed_input_password = hashlib.sha256(salted_password).hexdigest()
        return hashed_input_password == self.hashed_password
