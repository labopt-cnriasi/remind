from django.urls import path
from . import views
from django.conf.urls import url
from django.contrib import admin
app_name = "allapps"

urlpatterns = [
    url(r'^applicativo1/', views.App1View.as_view(), name='app1'),
    url(r'^applicativo1_result', views.App1_outputView.as_view(), name='app1_result'),
    url(r'^applicativo2/', views.App2View.as_view(), name='app2'),
    url(r'^applicativo2_result', views.App2_outputView.as_view(), name='app2_result'),
    url(r'^applicativo3/', views.App3View.as_view(), name='app3'),
    url(r'^contatti', views.contattiView.as_view(), name='contatti'),
]
admin.autodiscover()

