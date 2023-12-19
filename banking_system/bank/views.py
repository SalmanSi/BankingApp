from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import redirect
# Create your views here.

def index(request):

    return render(request,"bank/index.html")
    

def login_view(request):
    user=User(username="salman",password="salman")
    if request.method=="POST":
        username=request.POST["username"]
        password=request.POST["password"]
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return HttpResponseRedirect(reverse('home'))
        else:
            return render(request,"bank/login.html",{
                "message":"Invalid credentials."
            })
    return render(request,"bank/login.html")
        
    
def home(request):
    return render(request,"bank/home.html")