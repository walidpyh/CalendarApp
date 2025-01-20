from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TimeField
from wtforms.validators import DataRequired
import datetime as dt


class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()], default=dt.datetime.now().date())
    start_time = TimeField('Start Time', validators=[DataRequired()], default=dt.time(00, 00, 00))
    end_date = DateField('End Date', validators=[DataRequired()], default=dt.datetime.now().date())
    end_time = TimeField('End Time', validators=[DataRequired()], default=dt.time(23, 59, 00))
    color = StringField('Color', validators=[DataRequired()])