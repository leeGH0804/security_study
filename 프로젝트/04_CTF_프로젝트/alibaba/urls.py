
# /root/ctf-web/myctf/alibaba/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_view, name='alibaba_main'),
    path('door/', views.main_view, name='door'),
    path("api/access", views.access_api, name="access_api"),
]
