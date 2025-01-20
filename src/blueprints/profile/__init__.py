
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from forms.settings import UpdateAccountForm
from data.database import db_session
from data.database.users import User
import os
from PIL import Image
import secrets
from blueprints.decorators import otp_required

profile_blueprint = Blueprint('profile', __name__, template_folder='templates')

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join('static/profile_img', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@profile_blueprint.route('/settings', methods=['GET', 'POST'])
@login_required
@otp_required
def settings():
    form = UpdateAccountForm()

    # Handle POST request for updating user details
    if form.validate_on_submit():
        db_session_instance = db_session.create_session()
        user = db_session_instance.query(User).filter(User.id == current_user.id).first()

        # Check if the current password matches
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template('settings.html', form=form)

        # Update avatar if provided
        if form.picture.data:
            #if current_user.avatar != 'profile_default.png':
            #    delete_photo(current_user.avatar)  # Delete the old photo
            picture_file = save_picture(form.picture.data)
            user.avatar = picture_file

        # Update name and email
        user.name = form.name.data
        user.email = form.email.data

        # Update password if a new password is provided
        if form.new_password.data:
            user.set_password(form.new_password.data)

        # Commit changes to the database
        db_session_instance.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('profile.settings'))

    # Handle GET request to populate form fields
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email

    image_file = url_for('static', filename='profile_img/' + current_user.avatar)
    return render_template('settings.html', image_file=image_file, form=form)
