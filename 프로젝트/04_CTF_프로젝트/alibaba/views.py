
# /root/ctf-web/myctf/alibaba/views.py

from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
import hashlib
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def main_view(request):
    token = request.COOKIES.get('token', 'door')
    method = request.method

    message = ""
    if token == hashlib.md5("open_sesame".encode()).hexdigest() and method == "GET":
        message = "The cave opens when you speak the magic word."
    elif token == "open_sesame" and method == "GET":
        message = "Try posting the magic word itself..."
    elif token == "open_sesame" and method == "POST":
        return render(request, 'alibaba/door.html')

    response = render(request, 'alibaba/index.html', {"message": message})

    if not request.COOKIES.get('token'):
        response.set_cookie("token", "door")

    return response

def access_api(request):
    message = "open_sesame"
    md5_token = hashlib.md5(message.encode()).hexdigest()
    return JsonResponse({"token": md5_token})
