from functools import wraps
from flask import session, redirect, url_for
from flask_login import current_user

def otp_required(f):
    """
    Decorator to restrict access to OTP-verified users.
    Redirects to the OTP setup page if OTP is not enabled,
    or to the OTP verification page if it is enabled but not verified.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user has enabled OTP
        if not current_user.otp_enabled:
            return redirect(url_for('auth.setup_otp'))

        # Check if OTP is verified
        if not session.get('otp_verified', False):
            return redirect(url_for('auth.verify_otp'))

        # Proceed with the original function
        return f(*args, **kwargs)
    return decorated_function