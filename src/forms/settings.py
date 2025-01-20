from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, FileField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from flask_login import current_user
from data.database.users import User
from data.database import db_session


class UpdateAccountForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])

    # Password fields
    current_password = PasswordField('Current Password', validators=[])
    new_password = PasswordField('New Password', validators=[])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password', message='Passwords must match.')])

    submit = SubmitField('Update')

    def validate_email(self, email):
        if email.data != current_user.email:
            session = db_session.create_session()
            user = session.query(User).filter(User.email == email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')

    def validate_new_password(self, new_password):
        # Validate length only if the field is not empty
        if new_password.data and len(new_password.data) < 8:
            raise ValidationError('Field must be at least 8 characters long.')

    def validate_current_password(self, current_password):
        # Validate the current password only if the new password is provided
        if self.new_password.data and not current_user.check_password(current_password.data):
            raise ValidationError('Current password is incorrect.')
