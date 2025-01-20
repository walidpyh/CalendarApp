from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from forms.login import LoginForm
from forms.register import RegisterForm
from data.database.users import User
from data.database import db_session
import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime
import requests

auth_blueprint = Blueprint('auth', __name__, template_folder='templates')

def verify_recaptcha(recaptcha_response):
    secret_key = "REMOVED" # https://www.google.com/recaptcha/
    data = {'secret': secret_key, 'response': recaptcha_response}
    url = 'https://www.google.com/recaptcha/api/siteverify'
    response = requests.post(url, data=data)
    return response.json().get('success', False)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect authenticated users to /calendar
    if current_user.is_authenticated:
        return redirect(url_for('event.calendar'))

    form = LoginForm()
    if form.validate_on_submit(): # Validate Entries
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            return render_template('login.html', form=form, message='Invalid reCAPTCHA.')

        db_session_instance = db_session.create_session()  # Use a unique variable for DB session
        user = db_session_instance.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            session['otp_verified'] = False  # Refers to Flask's session
            if user.otp_enabled:
                return redirect(url_for('auth.verify_otp'))
            return redirect(url_for('event.calendar'))

        return render_template('login.html', form=form, message='Invalid username or password')
    return render_template('login.html', form=form)

@auth_blueprint.route('/logout')
@login_required
def logout():
    session.pop('otp_verified', None)
    logout_user()
    return redirect(url_for('auth.login'))

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect authenticated users to /calendar
    if current_user.is_authenticated:
        return redirect(url_for('event.calendar'))

    form = RegisterForm()
    if form.validate_on_submit():
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            return render_template('register.html', form=form, message='Invalid reCAPTCHA.')

        if form.password.data != form.password_again.data:
            return render_template('register.html', form=form, message='Passwords must match')
        
        db_session_instance = db_session.create_session()
        if db_session_instance.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', form=form, message='Email already in use')
        if form.bday.data > datetime.now().date() or abs((form.bday.data - datetime.now().date()).days // 365) > 150:
            return render_template('register.html', form=form, message='Enter a valid birth date')

        user = User(
            name=form.name.data,
            email=form.email.data,
            bday=form.bday.data
        )
        user.set_password(form.password.data)
        user.otp_secret = pyotp.random_base32()
        db_session_instance.add(user)
        db_session_instance.commit()
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('event.calendar'))
    return render_template('register.html', form=form)

@auth_blueprint.route('/setup-otp', methods=['GET', 'POST'])
@login_required
def setup_otp():
    user = current_user
    if request.method == 'POST':
        otp = request.form.get('otp')
        totp = pyotp.TOTP(user.otp_secret)
        if totp.verify(otp):
            user.otp_enabled = True
            db_session_instance = db_session.create_session()

            user = db_session_instance.merge(user)

            # Commit the changes
            db_session_instance.commit()

            flash('2FA enabled successfully!', 'success')
            return redirect(url_for('event.calendar'))
        flash('Invalid OTP. Please try again.', 'danger')

    totp = pyotp.TOTP(user.otp_secret)
    qr_url = totp.provisioning_uri(name=user.email, issuer_name="CalendarApp")
    img = qrcode.make(qr_url)
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    qr_code_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
    return render_template('setup_otp.html', qr_code=qr_code_base64)

@auth_blueprint.route('/verify-otp', methods=['GET', 'POST'])
@login_required
def verify_otp():
    user = current_user
    if request.method == 'POST':
        otp = request.form.get('otp')
        totp = pyotp.TOTP(user.otp_secret)
        if totp.verify(otp):
            session['otp_verified'] = True
            flash('OTP verified successfully!', 'success')
            return redirect(url_for('event.calendar'))
        flash('Invalid OTP. Please try again.', 'danger')
    return render_template('verify_otp.html')
