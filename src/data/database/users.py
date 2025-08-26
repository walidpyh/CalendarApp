from .db_session import SqlAlchemyBase
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
import datetime
from security.password_policy import PasswordPolicy

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
    
    # Account protection
    failed_login_attempts = sqlalchemy.Column(sqlalchemy.Integer, default=0)  # Track failed logins
    account_locked_until = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)  # Lockout timestamp
    last_password_change = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now)  # For password expiration
    
    # Relationship with the Calendar model
    calendar_relationship = orm.relationship("Calendar", back_populates="users_relationship")

    def set_password(self, password):
        """
        Hashes the password using Argon2id and sets it to the hashed_password field.
        """
        self.hashed_password = PasswordPolicy.hash_password(password)
        self.last_password_change = datetime.now()

    def check_password(self, password):
        """
        Verifies the password against the stored hash.
        """
        # Check if password is stored in old SHA-256 format
        if len(self.hashed_password) == 64:  # SHA-256 produces 64 hex chars
            # Verify with old method
            salt = "CalendarAppSalt6875"
            salted_password = (password + salt).encode('utf-8')
            hashed_input_password = hashlib.sha256(salted_password).hexdigest()
            is_valid = hashed_input_password == self.hashed_password
            
            # If valid, upgrade to Argon2id
            if is_valid:
                self.set_password(password)
            return is_valid
        else:
            # Use new Argon2id verification
            return PasswordPolicy.verify_password(self.hashed_password, password)
    
    def increment_failed_login(self):
        """
        Increments the failed login counter and locks the account if necessary
        """
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            # Lock for 30 minutes
            self.account_locked_until = datetime.now() + datetime.timedelta(minutes=30)
    
    def reset_failed_login(self):
        """
        Resets the failed login counter after successful login
        """
        self.failed_login_attempts = 0
        self.account_locked_until = None
    
    def is_account_locked(self):
        """
        Checks if the account is currently locked
        """
        if self.account_locked_until is None:
            return False
        return datetime.now() < self.account_locked_until
    
    def password_expired(self, days=90):
        """
        Checks if the user's password has expired (default: 90 days)
        """
        if not self.last_password_change:
            return False
        expiry_date = self.last_password_change + datetime.timedelta(days=days)
        return datetime.now() > expiry_date
