"""
URL configuration for rumipress project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import include, path
from django.contrib.auth.views import LoginView
from accounts.forms import CustomAuthenticationForm
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('distribution/', include('distribution.urls', namespace = 'distribution')),
    # Make login page the home page; redirect authenticated users to success URL
    path('', LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True, authentication_form=CustomAuthenticationForm), name='home'),
    # Override default auth login to use custom form with inactive message
    path('accounts/login/', LoginView.as_view(template_name='registration/login.html', authentication_form=CustomAuthenticationForm), name='login'),
    # Use custom logout to avoid 405 and ensure redirect
    path('accounts/logout/', views.logout_redirect, name='logout_redirect'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
]
