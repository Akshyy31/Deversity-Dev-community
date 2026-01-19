from django.core.exceptions import ValidationError
import os

ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png"]
MAX_FILE_SIZE_MB = 5


def validate_experience_proof(file):
    ext = os.path.splitext(file.name)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            "Only PDF, JPG, JPEG, and PNG files are allowed."
        )

    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            f"File size must be under {MAX_FILE_SIZE_MB} MB."
        )
