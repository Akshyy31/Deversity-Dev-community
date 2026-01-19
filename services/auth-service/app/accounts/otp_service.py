import random
import json
from .redis_client import redis_client
from .tasks import send_otp_email



OTP_TTL = 300  # 5 minutes
MAX_ATTEMPTS = 3


def generate_otp():
    return str(random.randint(100000, 999999))




def send_otp(email):
    otp = generate_otp()
    key = f"otp:register:{email}"

    redis_client.setex(
        key,
        OTP_TTL,
        json.dumps({"otp": otp, "attempts": 0})
    )

    # 🔥 async email send
    send_otp_email.delay(email, otp)



def verify_otp(email, input_otp):
    key = f"otp:register:{email}"
    data = redis_client.get(key)

    if not data:
        return False, "OTP expired or not found"

    payload = json.loads(data)

    if payload["attempts"] >= MAX_ATTEMPTS:
        redis_client.delete(key)
        return False, "Too many attempts"

    if payload["otp"] != input_otp:
        payload["attempts"] += 1
        redis_client.setex(key, OTP_TTL, json.dumps(payload))
        return False, "Invalid OTP"

    redis_client.delete(key)
    return True, "OTP verified"
