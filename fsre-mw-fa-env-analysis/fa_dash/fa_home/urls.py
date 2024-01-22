"""fa_dash URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path,include
from fa_home import views

urlpatterns = [
    path('',views.index,name='home'),
    path('submit_form/', views.submit_form,name='submit_form'),
    path('submit_form/db_dash/', views.db_dash,name='db_dash'),
    path('test/', views.test,name='db_dash'),
    
]
