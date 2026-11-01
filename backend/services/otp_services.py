import secrets
from datetime import datetime,timedelta,timezone
import random

def generate_email_otp():
    otp = str(secrets.randbelow(900000) + 100000)
    return otp

def generate_otp_expiry():
    expiry= datetime.now(timezone.utc) + timedelta(minutes=1)
    return expiry.isoformat()

def is_otp_expired(expiry_time: str):
    expiry = datetime.fromisoformat(expiry_time)

    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    return datetime.now(timezone.utc) > expiry

