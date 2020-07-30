"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.conf.urls import url
from django.http import HttpResponseRedirect

from allapps import views

urlpatterns = [
    
    url(r'^$', lambda r: HttpResponseRedirect('home/')),

    url(r'home/', views.HomeView.as_view(), name='home'),
    url(r'applicativo1/', views.App1View.as_view(), name='app1'),
    path('allapps/', include('allapps.urls')),
    path('admin/', admin.site.urls),
]