# accounts/urls.py

from django.urls import path
from accounts import views

urlpatterns = [
     path("register/", views.RegisterAPIView.as_view()),
    path("verify-otp/", views.VerifyOTPAPIView.as_view()),
    path("login/", views.LoginAPIView.as_view()),
    path("verify-login-otp/", views.VerifyLoginOTPAPIView.as_view()),
]
