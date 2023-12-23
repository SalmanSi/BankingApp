from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.shortcuts import redirect
# Create your views here.

def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    return render(request,"bank/user.html")
    

def login_view(request):
    
    if request.method=="POST":
        username=request.POST["username"]
        password=request.POST["password"]
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request,"bank/login.html",{
                "message":"Invalid credentials."
            })
    return render(request,"bank/login.html")    
        
def logout_view(request):
    logout(request)
    return render(request,"bank/login.html",{
        "message":"Logged Out"
    })

def register_view(request):
    if request.method=="POST":
        username=request.POST["username"]
        password=request.POST["password"]
        first_name=request.POST["first_name"]
        last_name=request.POST["last_name"]
        email=request.POST["email"]
        # create user
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        login(request,user)
        return HttpResponseRedirect(reverse('index'))

    return render(request,"bank/register.html")

