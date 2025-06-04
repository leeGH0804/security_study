
# /root/ctf-web/myctf/hansel/views.py

from django.shortcuts import render

# Create your views here.

import hashlib
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login_view(request):
    success = False
    error = False

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        with open("/root/ctf-web/accounts.txt", "r") as f:
            for line in f:
                user, pw = line.strip().split(":")
                if username == user and password == pw:
                    response = render(request, "hansel/login.html", {"success": True})
                    response.delete_cookie("secret")
                    return response

        return render(request, "hansel/login.html", {"error": True})

    hint = "alibaba"
    hashed_hint = hashlib.sha256(hint.encode()).hexdigest()
    response = render(request, "hansel/login.html", {
        "success": success,
        "error": error
    })
    response.set_cookie("secret", hashed_hint, secure=False, httponly=False)
    return response

@csrf_exempt
def logout_view(request):
    hint = "alibaba"
    hashed_hint = hashlib.sha256(hint.encode()).hexdigest()
    response = redirect("/login/")
    response.set_cookie("secret", hashed_hint)
    return response
