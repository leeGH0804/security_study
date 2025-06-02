
# /root/ctf-web/myctf/myctf/urls.py

"""
URL configuration for myctf project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from hansel import views as hansel_views
from alibaba import views as alibaba_views
from django.conf import settings
from django.conf.urls.static import static
from pathlib import Path
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from alibaba.views import access_api
import os

BASE_DIR = Path(__file__).resolve().parent.parent

def root_view(request):
    host = request.get_host().split(':')[0]
    if host == "hanselandgretel":
        return HttpResponseRedirect("/login/")
    elif host == "alibaba":
        return HttpResponseRedirect("/alibaba/")
    else:
        return HttpResponseRedirect("/login/")

urlpatterns = [
    path("login/", hansel_views.login_view, name="login"),
    path("logout/", hansel_views.logout_view, name="logout"),
    path('api/access', alibaba_views.access_api, name="access_api"),
    path('alibaba/', include('alibaba.urls')),
    path('', root_view),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(BASE_DIR, 'static'))
