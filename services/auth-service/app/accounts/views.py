import uuid, json, random, os, shutil
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    RegistrationSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
    VerifyLoginOTPSerializer,
    ProfileUpdateSerializer,
    ProfileDetailSerializer,
)
from .tasks import send_otp_email, send_otp_email_task
from .utils import save_temp_file, hash_otp, generate_otp
from .models import User, DeveloperProfile, MentorProfile
from .redis_client import redis_client
from .jwt import generate_tokens
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated, AllowAny


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=RegistrationSerializer,
        responses={201: None},
        tags=["Auth"],
    )
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        otp = random.randint(100000, 999999)
        otp_id = str(uuid.uuid4())

        temp_file_path = None
        if data["role"] == User.Role.MENTOR:
            temp_file_path = save_temp_file(data["experience_proof"], "mentor")

        payload = {
            "email": data["email"],
            "username": data["username"],
            "full_name": data["full_name"],
            "password": make_password(data["password"]),
            "phone": data.get("phone"),
            "role": data["role"],
            "skills": data.get("skills"),
            "years_of_experience": data.get("years_of_experience"),
            "experience_proof_path": temp_file_path,
            "otp": str(otp),
        }

        redis_key = f"otp:register:{otp_id}"
        redis_client.setex(redis_key, 300, json.dumps(payload))

        send_otp_email.delay(data["email"], otp)

        return Response(
            {"otp_id": otp_id, "message": "OTP sent"},
            status=status.HTTP_201_CREATED,
        )


class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp_id = serializer.validated_data["otp_id"]  # ✅ FIX
        otp = serializer.validated_data["otp"]

        redis_key = f"otp:register:{otp_id}"
        raw = redis_client.get(redis_key)

        if not raw:
            return Response({"error": "OTP expired"}, status=400)

        data = json.loads(raw)

        if data["otp"] != otp:
            return Response({"error": "Invalid OTP"}, status=400)

        try:
            user = User.objects.create(
                email=data["email"],
                username=data["username"],
                full_name=data["full_name"],
                password=data["password"],
                phone=data["phone"],
                role=data["role"],
                is_verified=True,
                is_active=True,
                is_approved=(data["role"] != User.Role.MENTOR),  # ✅ FIX
            )
        except IntegrityError:
            return Response(
                {"error": "User already exists"},
                status=400,
            )

        if user.role == User.Role.DEVELOPER:
            DeveloperProfile.objects.create(
                user=user,
                skills=data["skills"],
            )

        else:
            final_dir = os.path.join(settings.MEDIA_ROOT, "mentor_proofs")
            os.makedirs(final_dir, exist_ok=True)

            final_path = shutil.move(data["experience_proof_path"], final_dir)

            MentorProfile.objects.create(
                user=user,
                skills=data["skills"],
                years_of_experience=data["years_of_experience"],
                experience_proof=final_path.replace(settings.MEDIA_ROOT + "/", ""),
            )

        redis_client.delete(redis_key)

        return Response(
            {
                "message": (
                    "Registration completed. Await admin approval."
                    if user.role == User.Role.MENTOR
                    else "Registration completed successfully"
                )
            },
            status=201,
        )


import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        if user.role == User.Role.MENTOR and not user.is_approved:
            return Response(
                {"detail": "Mentor account not approved yet"},
                status=status.HTTP_403_FORBIDDEN,
            )

        otp = generate_otp()
        challenge_id = str(uuid.uuid4())

        # store OTP
        redis_client.setex(f"otp:{challenge_id}", 300, hash_otp(otp))

        # store login context
        redis_client.setex(f"login_ctx:{challenge_id}", 300, user.id)

        send_otp_email_task.delay(user.email, otp)

        response = Response({"otp_required": True}, status=status.HTTP_200_OK)

        # THIS IS THE KEY PART
        response.set_cookie(
            key="challenge_id",
            value=challenge_id,
            httponly=True,
            secure=False,  # True in production (HTTPS)
            samesite="Lax",
            max_age=300,
        )

        return response


class VerifyLoginOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyLoginOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]

        challenge_id = request.COOKIES.get("challenge_id")
        if not challenge_id:
            return Response({"detail": "Login expired"}, status=400)

        user_id = redis_client.get(f"login_ctx:{challenge_id}")
        stored_otp = redis_client.get(f"otp:{challenge_id}")

        if not user_id or not stored_otp:
            return Response({"detail": "Login expired"}, status=400)

        if stored_otp != hash_otp(otp):
            return Response({"detail": "Invalid OTP"}, status=400)

        # cleanup
        redis_client.delete(f"otp:{challenge_id}")
        redis_client.delete(f"login_ctx:{challenge_id}")

        user = User.objects.get(id=user_id)

        if user.role == User.Role.MENTOR and not user.is_approved:
            return Response(
                {"detail": "Mentor account not approved yet"},
                status=status.HTTP_403_FORBIDDEN,
            )
        tokens = generate_tokens(user)

        response = Response({**tokens, "role": user.role}, status=status.HTTP_200_OK)

        # remove cookie
        response.delete_cookie("challenge_id")

        return response


class ProfileUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        data = {
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "phone": user.phone,
            "role": user.role,
        }

        if user.role == User.Role.DEVELOPER:
            profile = user.developer_profile
            data.update(
                {
                    "skills": profile.skills,
                    "profile_image": profile.profile_image,
                }
            )

        elif user.role == User.Role.MENTOR:
            profile = user.mentor_profile
            data.update(
                {
                    "skills": profile.skills,
                    "profile_image": profile.profile_image,
                    "years_of_experience": profile.years_of_experience,
                    "experience_proof": profile.experience_proof,
                }
            )

        serializer = ProfileDetailSerializer(data)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,  
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Profile updated successfully"},
            status=status.HTTP_200_OK,
        )
