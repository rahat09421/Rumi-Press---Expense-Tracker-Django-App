from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.views.decorators.http import require_http_methods

def  home(request):
    return render(request, 'home.html')

@require_http_methods(["GET", "POST"]) 
def logout_redirect(request):
    logout(request)
    return redirect('/accounts/login/')