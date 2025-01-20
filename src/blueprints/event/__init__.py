from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from forms.event import EventForm
from data.database.calendar import Calendar
from data.database import db_session
from datetime import datetime, timedelta
from blueprints.decorators import otp_required


event_blueprint = Blueprint('event', __name__, template_folder='templates')

@event_blueprint.route('/calendar')
@login_required
@otp_required
def calendar():
    session_db = db_session.create_session()
    events_db = session_db.query(Calendar).filter(Calendar.user_id == current_user.id).all() 
    events = []
    for event in events_db:
        events.append({
            'id': event.id,
            'title': event.title,
            'start': f'{event.start_date}T{event.start_time}',
            'end': f'{event.end_date}T{event.end_time}',
            'color': event.color
        })
    return render_template('calendar.html', events=events)

@event_blueprint.route('/calendar_add_event', methods=['GET', 'POST'])
@login_required
@otp_required
def add_event():
    form = EventForm()
    if form.validate_on_submit():
        new_event = Calendar(
            title=form.title.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            color=form.color.data,
            user_id=current_user.id
        )
        session_db = db_session.create_session()
        session_db.add(new_event)
        session_db.commit()
        flash('Event added!', 'success')
        return redirect(url_for('event.calendar'))
    return render_template('add_event.html', form=form)

@event_blueprint.route('/calendar_edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
@otp_required
def edit_event(event_id):
    session_db = db_session.create_session()
    event = session_db.query(Calendar).filter_by(id=event_id, user_id=current_user.id).first()
    if not event:
        abort(403)

    form = EventForm()

    if request.method == 'POST' and form.validate_on_submit():
        event.title = form.title.data
        event.start_date = form.start_date.data
        event.end_date = form.end_date.data
        event.start_time = form.start_time.data
        event.end_time = form.end_time.data
        event.color = form.color.data
        session_db.commit()
        flash('Event updated!', 'success')
        return redirect(url_for('event.calendar'))
    
    elif request.method == 'GET':
        # Populate the form with the current event details
        form.title.data = event.title
        form.start_date.data = event.start_date
        form.end_date.data = event.end_date
        form.start_time.data = event.start_time
        form.end_time.data = event.end_time
        form.color.data = event.color

    return render_template('edit_event.html', form=form, event=event)

@event_blueprint.route('/calendar_delete_event/<int:event_id>', methods=['GET'])
@login_required
@otp_required
def delete_event(event_id):
    session_db = db_session.create_session()
    event = session_db.query(Calendar).filter_by(id=event_id, user_id=current_user.id).first()
    if not event:
        abort(403)

    session_db.delete(event)
    session_db.commit()
    flash('Event deleted!', 'success')
    return redirect(url_for('event.calendar'))