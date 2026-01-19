from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .validators import validate_experience_proof
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        DEVELOPER = "developer", "Developer"
        MENTOR = "mentor", "Mentor"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, blank=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DEVELOPER,
    )

    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "full_name"]

    objects = UserManager()


class DeveloperProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="developer_profile"
    )

    skills = models.JSONField()  # ["Python", "Django", "Docker"]

    profile_image = models.ImageField(
        upload_to="profiles/developers/", blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)


class MentorProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="mentor_profile"
    )

    skills = models.JSONField()
    profile_image = models.ImageField(
        upload_to="profiles/mentors/", blank=True, null=True
    )
    years_of_experience = models.PositiveIntegerField()
    experience_proof = models.FileField(
        upload_to="mentor_proofs/", validators=[validate_experience_proof]
    )

    created_at = models.DateTimeField(auto_now_add=True)
