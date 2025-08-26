import re
from passlib.hash import argon2
import requests

class PasswordPolicy:
    @staticmethod
    def is_password_strong(password, email=None, name=None, bday=None):
        """
        Verify password strength against security policy
        
        :param password: The password to check
        :param email: User email to check against (prevent email in password)
        :param name: User name to check against (prevent name in password)
        :param bday: User birthday to check against (prevent birthday in password)
        :return: (bool, str) - (Success, Error message if any)
        """
        # Check length
        if len(password) < 12:  # Increased minimum length from 8 to 12
            return False, "Password must be at least 12 characters long"
            
        # Check complexity
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one digit"
        if not re.search(r'[!@#$%^&*()_\-+={}[\]|:;"\'<>,.?/~`]', password):
            return False, "Password must contain at least one special character"
            
        # Check for common words
        if any(common_word in password.lower() for common_word in ['password', 'admin', '123456', 'qwerty']):
            return False, "Password contains common sequences or words"
            
        # Check against personal information if provided
        if email and email.split('@')[0].lower() in password.lower():
            return False, "Password must not contain your email address"
        if name and name.lower() in password.lower():
            return False, "Password must not contain your name"
        if bday and bday in password:
            return False, "Password must not contain your birthday"
            
        # All checks passed
        return True, ""
    
    @staticmethod
    def check_pwned_password(password):
        """
        Check if password has been exposed in data breaches using k-Anonymity model
        
        :param password: Password to check
        :return: (bool, int) - (Is password pwned, How many times it was found)
        """
        import hashlib
        
        # Hash the password with SHA-1
        password_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        
        # Use k-Anonymity model - only send first 5 chars of hash
        prefix = password_hash[:5]
        suffix = password_hash[5:]
        
        try:
            # Check against HaveIBeenPwned API
            response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}")
            if response.status_code == 200:
                for line in response.text.splitlines():
                    if line.split(':')[0] == suffix:
                        count = int(line.split(':')[1])
                        return True, count
                return False, 0
            else:
                # If API is down, let's be cautious and continue without blocking
                return False, 0
        except Exception:
            # If request fails, let's be cautious and continue without blocking
            return False, 0
            
    @staticmethod
    def hash_password(password):
        """
        Hash password using Argon2id (more secure than SHA-256)
        
        :param password: Plain text password
        :return: Hashed password
        """
        return argon2.using(
            type='ID',           # Argon2id variant
            memory_cost=65536,   # 64MB memory usage
            time_cost=3,         # 3 iterations
            parallelism=4        # 4 parallel threads
        ).hash(password)
        
    @staticmethod
    def verify_password(hashed_password, plain_password):
        """
        Verify password against stored hash
        
        :param hashed_password: Stored password hash
        :param plain_password: Plain text password to verify
        :return: True if password matches, False otherwise
        """
        return argon2.verify(plain_password, hashed_password) 