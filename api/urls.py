from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('authmail/', views.AuthMailView.as_view(), name='authmail'),
    path('sightlist/', views.Spotapi.as_view(), name='upload'),
    path('sightdetail/', views.SpotDetailapi.as_view(), name='upload'),
    path('review/', views.Reviewapi.as_view(), name='review'),
    path('postreview/', views.PostReview.as_view(), name='post_review'),
]
