from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, role="developer", **extra_fields):
        if not email:
            raise ValueError("Email is required")

        if role == "admin":
            raise ValueError("Admin users cannot be created via API")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            role=role,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("is_approved", True)

        return self.create_user(
            email=email,
            password=password,
            role="admin",
            **extra_fields
        )
