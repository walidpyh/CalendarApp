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
from security import log_auth_event, rate_limit, sanitize_input
from security.password_policy import PasswordPolicy

auth_blueprint = Blueprint('auth', __name__, template_folder='templates')

def verify_recaptcha(recaptcha_response):
    secret_key = "REMOVED" # https://www.google.com/recaptcha/
    data = {'secret': secret_key, 'response': recaptcha_response}
    url = 'https://www.google.com/recaptcha/api/siteverify'
    response = requests.post(url, data=data)
    return response.json().get('success', False)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=10, per_seconds=60)  # Additional rate limiting at route level
def login():
    # Redirect authenticated users to /calendar
    if current_user.is_authenticated:
        return redirect(url_for('event.calendar'))

    form = LoginForm()
    if form.validate_on_submit(): # Validate Entries
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            log_auth_event(
                event_type="login_attempt",
                username=form.email.data,
                success=False,
                details={"reason": "reCAPTCHA failed"}
            )
            return render_template('login.html', form=form, message='Invalid reCAPTCHA.')

        db_session_instance = db_session.create_session()  # Use a unique variable for DB session
        user = db_session_instance.query(User).filter(User.email == form.email.data).first()
        
        # Check if user exists and account is not locked
        if user:
            if user.is_account_locked():
                log_auth_event(
                    event_type="login_attempt",
                    user_id=user.id,
                    username=user.email,
                    success=False,
                    details={"reason": "account_locked"}
                )
                return render_template('login.html', form=form, 
                                    message='Account locked due to too many failed attempts. Try again later.')
            
            # Verify password
            if user.check_password(form.password.data):
                # Reset failed login counter on success
                user.reset_failed_login()
                db_session_instance.commit()
                
                login_user(user, remember=form.remember_me.data)
                session['otp_verified'] = False  # Refers to Flask's session
                
                log_auth_event(
                    event_type="login_success",
                    user_id=user.id,
                    username=user.email,
                    success=True
                )
                
                # Check if password is expired
                if user.password_expired():
                    flash('Your password has expired. Please set a new password.', 'warning')
                    return redirect(url_for('profile.change_password'))
                
                if user.otp_enabled:
                    return redirect(url_for('auth.verify_otp'))
                return redirect(url_for('event.calendar'))
            else:
                # Increment failed login counter
                user.increment_failed_login()
                db_session_instance.commit()
                
                log_auth_event(
                    event_type="login_attempt",
                    user_id=user.id,
                    username=user.email,
                    success=False,
                    details={"reason": "invalid_password", "attempt": user.failed_login_attempts}
                )
        else:
            # Log attempt with non-existent user
            log_auth_event(
                event_type="login_attempt",
                username=form.email.data,
                success=False,
                details={"reason": "user_not_found"}
            )

        return render_template('login.html', form=form, message='Invalid username or password')
    return render_template('login.html', form=form)

@auth_blueprint.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        log_auth_event(
            event_type="logout",
            user_id=current_user.id,
            username=current_user.email,
            success=True
        )
    
    session.pop('otp_verified', None)
    logout_user()
    return redirect(url_for('auth.login'))

@auth_blueprint.route('/register', methods=['GET', 'POST'])
@rate_limit(max_requests=5, per_seconds=300)  # Strict rate limiting for registration
def register():
    # Redirect authenticated users to /calendar
    if current_user.is_authenticated:
        return redirect(url_for('event.calendar'))

    form = RegisterForm()
    if form.validate_on_submit():
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            log_auth_event(
                event_type="registration_attempt",
                username=form.email.data,
                success=False,
                details={"reason": "reCAPTCHA failed"}
            )
            return render_template('register.html', form=form, message='Invalid reCAPTCHA.')

        # Sanitize user inputs
        name = sanitize_input(form.name.data)
        email = form.email.data.lower().strip()
        
        if form.password.data != form.password_again.data:
            log_auth_event(
                event_type="registration_attempt",
                username=email,
                success=False,
                details={"reason": "passwords_dont_match"}
            )
            return render_template('register.html', form=form, message='Passwords must match')
        
        # Check password against known breached passwords
        is_pwned, count = PasswordPolicy.check_pwned_password(form.password.data)
        if is_pwned:
            log_auth_event(
                event_type="registration_attempt",
                username=email,
                success=False,
                details={"reason": "password_compromised", "breach_count": count}
            )
            return render_template('register.html', form=form, 
                                message='This password has been found in data breaches. Please choose a different one.')
        
        db_session_instance = db_session.create_session()
        if db_session_instance.query(User).filter(User.email == email).first():
            log_auth_event(
                event_type="registration_attempt",
                username=email,
                success=False,
                details={"reason": "email_in_use"}
            )
            return render_template('register.html', form=form, message='Email already in use')
            
        if form.bday.data > datetime.now().date() or abs((form.bday.data - datetime.now().date()).days // 365) > 150:
            log_auth_event(
                event_type="registration_attempt",
                username=email,
                success=False,
                details={"reason": "invalid_birthday"}
            )
            return render_template('register.html', form=form, message='Enter a valid birth date')

        user = User(
            name=name,
            email=email,
            bday=form.bday.data
        )
        user.set_password(form.password.data)
        user.otp_secret = pyotp.random_base32()
        db_session_instance.add(user)
        db_session_instance.commit()
        
        log_auth_event(
            event_type="registration_success",
            user_id=user.id,
            username=user.email,
            success=True
        )
        
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
            db_session_instance.commit()

            log_auth_event(
                event_type="otp_setup",
                user_id=user.id,
                username=user.email,
                success=True
            )

            flash('2FA enabled successfully!', 'success')
            return redirect(url_for('event.calendar'))
            
        log_auth_event(
            event_type="otp_setup",
            user_id=user.id,
            username=user.email,
            success=False,
            details={"reason": "invalid_otp"}
        )
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
@rate_limit(max_requests=5, per_seconds=60)  # Rate limit OTP verification attempts
def verify_otp():
    user = current_user
    if request.method == 'POST':
        otp = request.form.get('otp')
        totp = pyotp.TOTP(user.otp_secret)
        if totp.verify(otp):
            session['otp_verified'] = True
            
            log_auth_event(
                event_type="otp_verification",
                user_id=user.id,
                username=user.email,
                success=True
            )
            
            flash('OTP verified successfully!', 'success')
            return redirect(url_for('event.calendar'))
            
        log_auth_event(
            event_type="otp_verification",
            user_id=user.id,
            username=user.email,
            success=False,
            details={"reason": "invalid_otp"}
        )
        flash('Invalid OTP. Please try again.', 'danger')
    return render_template('verify_otp.html')
