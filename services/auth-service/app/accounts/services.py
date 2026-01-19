from django.db import transaction
from django.contrib.auth import get_user_model

from .models import DeveloperProfile, MentorProfile
from .otp_service import verify_otp

User = get_user_model()


@transaction.atomic
def register_user_after_otp(validated_data, otp):
    email = validated_data["email"]

    success, message = verify_otp(email, otp)
    if not success:
        raise ValueError(message)

    role = validated_data["role"]

    user = User.objects.create_user(
        email=email,
        password=validated_data["password"],
        role=role,
        username=validated_data["username"],
        full_name=validated_data["full_name"],
        phone=validated_data.get("phone", "")
    )

    if role == User.Role.DEVELOPER:
        DeveloperProfile.objects.create(
            user=user,
            skills=validated_data["skills"]
        )

        user.is_active = True
        user.is_verified = True

    elif role == User.Role.MENTOR:
        MentorProfile.objects.create(
            user=user,
            skills=validated_data["skills"],
            years_of_experience=validated_data["years_of_experience"],
            experience_proof=validated_data["experience_proof"]
        )
        # mentor waits for admin approval

    user.save()
    return user
