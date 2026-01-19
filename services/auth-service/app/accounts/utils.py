import random
import hashlib
from django.contrib.auth.hashers import make_password
import os, uuid
from django.conf import settings


def generate_otp():
    return str(random.randint(100000, 999999))

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()

def hash_password(password: str) -> str:
    return make_password(password)



def save_temp_file(file, role):
    temp_dir = os.path.join(settings.MEDIA_ROOT, "temp", role)
    os.makedirs(temp_dir, exist_ok=True)

    filename = f"{uuid.uuid4()}_{file.name}"
    path = os.path.join(temp_dir, filename)

    with open(path, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)

    return path