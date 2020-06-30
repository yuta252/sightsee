from django.urls import path
from . import views

app_name = 'cameraapi'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='singup'),
    path('exhibit/', views.ExhibitView.as_view(), name='exhibit'),
    path('result/', views.ResultView.as_view(), name='result'),
]