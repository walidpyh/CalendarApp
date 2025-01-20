from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, EmailField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from datetime import date


class RegisterForm(FlaskForm):
    name = StringField(
        'Your name',
        validators=[
            DataRequired(),
            Length(min=2, max=20, message="Name must be between 2 and 20 characters.")
        ]
    )
    email = EmailField(
        'Email',
        validators=[
            DataRequired(),
            Email(message="Enter a valid email address.")
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters.")
        ]
    )
    password_again = PasswordField(
        'Repeat password',
        validators=[
            DataRequired(),
            EqualTo('password', message="Passwords must match.")
        ]
    )
    bday = DateField(
        'Your Birthday',
        validators=[
            DataRequired()
        ]
    )
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Register')

    def validate_password(self, field):
        """
        Custom validator to enforce password complexity and ensure it doesn't
        contain the user's email, name, or birthday.
        """
        password = field.data

        # Enforce complexity
        if not any(char.isupper() for char in password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not any(char.islower() for char in password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one digit.")
        if not any(char in "!@#$%^&*()-_=+[]{}|;:',.<>?/`~" for char in password):
            raise ValidationError("Password must contain at least one special character.")

        # Check if password contains email, name, or birthday
        email = self.email.data.lower() if self.email.data else ''
        name = self.name.data.lower() if self.name.data else ''
        bday = self.bday.data.strftime('%Y-%m-%d') if self.bday.data else ''

        if email and email.split('@')[0] in password.lower():
            raise ValidationError("Password must not contain your email address.")
        if name and name in password.lower():
            raise ValidationError("Password must not contain your name.")
        if bday and bday in password:
            raise ValidationError("Password must not contain your birthday.")

    def validate_bday(self, field):
        """
        Custom validator to ensure the user is at least 12 years old.
        """
        bday = field.data
        today = date.today()
        age = today.year - bday.year - ((today.month, today.day) < (bday.month, bday.day))
        if age < 12:
            raise ValidationError("You must be at least 12 years old to register.")