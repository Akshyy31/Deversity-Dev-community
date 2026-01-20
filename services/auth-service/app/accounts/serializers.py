from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator

User = get_user_model()


class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=50)
    full_name = serializers.CharField(max_length=150)

    phone = serializers.CharField(
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\+?\d{10,15}$",
                message="Enter a valid phone number.",
            )
        ],
    )

    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.Role.choices)

    # common
    skills = serializers.ListField(
        child=serializers.CharField(min_length=1),
        required=False,
        allow_empty=False,
    )

    # mentor-only
    years_of_experience = serializers.IntegerField(
        required=False, min_value=1, max_value=50
    )
    experience_proof = serializers.FileField(required=False)

    # ---------- field-level ----------

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_experience_proof(self, file):
        allowed = ["application/pdf", "image/jpeg", "image/png"]
        if file.content_type not in allowed:
            raise serializers.ValidationError(
                "Only PDF, JPG, or PNG files are allowed."
            )
        return file

    # ---------- object-level ----------

    def validate(self, attrs):
        role = attrs.get("role")

        if role == User.Role.ADMIN:
            raise serializers.ValidationError(
                {"role": "Admin registration is not allowed."}
            )

        if role == User.Role.DEVELOPER:
            if not attrs.get("skills"):
                raise serializers.ValidationError(
                    {"skills": "Skills are required for developer."}
                )

        if role == User.Role.MENTOR:
            errors = {}
            if not attrs.get("skills"):
                errors["skills"] = "Skills are required for mentor."
            if not attrs.get("years_of_experience"):
                errors["years_of_experience"] = "Experience is required."
            if not attrs.get("experience_proof"):
                errors["experience_proof"] = "Experience proof is required."
            if errors:
                raise serializers.ValidationError(errors)

        if "skills" in attrs:
            attrs["skills"] = [
                s.strip().lower() for s in attrs["skills"] if s.strip()
            ]
            if not attrs["skills"]:
                raise serializers.ValidationError(
                    {"skills": "Skills cannot be empty."}
                )

        return attrs


class VerifyOTPSerializer(serializers.Serializer):
    otp_id = serializers.UUIDField()
    otp = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_active:
            raise serializers.ValidationError("User inactive")

        attrs["user"] = user
        return attrs
    
class VerifyLoginOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6, max_length=6)
    

class ProfileDetailSerializer(serializers.Serializer):
    # ---- User fields ----
    email = serializers.EmailField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    phone = serializers.CharField(allow_blank=True, required=False)
    role = serializers.CharField()

    # ---- Common profile ----
    skills = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    profile_image = serializers.ImageField(required=False)

    # ---- Mentor-only ----
    years_of_experience = serializers.IntegerField(required=False)
    experience_proof = serializers.FileField(required=False)
    

class ProfileUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False, max_length=150)
    username = serializers.CharField(required=False, max_length=50)
    phone = serializers.CharField(required=False)

    skills = serializers.ListField(
        child=serializers.CharField(min_length=1),
        required=False
    )

    profile_image = serializers.ImageField(required=False)

    def validate_username(self, value):
        user = self.context["request"].user
        if User.objects.exclude(id=user.id).filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value

    def update(self, instance, validated_data):
        """
        instance = request.user
        """

        # ---- USER TABLE ----
        for field in ("full_name", "username", "phone"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()

        # ---- PROFILE TABLE ----
        if instance.role == User.Role.DEVELOPER:
            profile = instance.developer_profile
        elif instance.role == User.Role.MENTOR:
            profile = instance.mentor_profile
        else:
            return instance

        if "skills" in validated_data:
            profile.skills = [
                s.strip().lower()
                for s in validated_data["skills"]
                if s.strip()
            ]

        if "profile_image" in validated_data:
            profile.profile_image = validated_data["profile_image"]

        profile.save()
        return instance
