from django.contrib import admin
from django.urls import path, re_path, include
from sesame.views import LoginView
from user.views import TestView
urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r"^auth/", include("drf_social_oauth2.urls", namespace="drf")),
    path("sesame/login/", LoginView.as_view(), name="sesame-login"),
    path("sesame_test/",TestView.as_view(),name='sesametest')
]
