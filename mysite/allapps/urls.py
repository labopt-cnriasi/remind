from django.urls import path
from . import views
from django.conf.urls import url
from django.contrib import admin
app_name = "allapps"

urlpatterns = [
    url(r'^applicativo1/', views.App1View.as_view(), name='app1'),
    url(r'^applicativo1_result', views.App1_outputView.as_view(), name='app1_result'),
]

admin.autodiscover()

