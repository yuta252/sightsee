from django.urls import path
from . import views

app_name = 'iOSapi'

urlpatterns = [
    path('authmail/', views.AuthMailView.as_view(), name='authmail'),
    path('authsuccess/', views.AuthSuccessView.as_view(), name='authsuccess'),
    path('question/', views.QuestionResisterView.as_view(), name='questionresister'),
    path('login/', views.LogInView.as_view(), name='login'),
    path('passreset/', views.PassResetView.as_view(), name='passreset'),
    path('passauth/', views.PassAuthView.as_view(), name='passauth'),
    path('passsend/', views.PassSendView.as_view(), name='passsend'),
    path('spotlist/', views.HomeView.as_view(), name='home'),
    path('searchlist/', views.SearchView.as_view(), name='search'),
    path('islike/', views.LikeView.as_view(), name='islike'),
    path('favorite/', views.FavoriteView.as_view(), name='favorite'),
    path('spotdetail/', views.SpotDetailView.as_view(), name='spotdetail'),
    path('postreview/', views.PostReviewView.as_view(), name='postreview'),
    path('reviewlist/', views.ReviewListView.as_view(), name='reviewlist'),
    path('exhibitlist/', views.ExhibitListView.as_view(), name='exhibitlist'),
    path('exhibitdetail/', views.ExhibitDetailView.as_view(), name='exhibitdetail'),
    path('camera/', views.CameraView.as_view(), name='camera'),
    path('contact/', views.ContactView.as_view(), name='contact'),
]

"""
urlpatterns = [
    path('authmail/', views.AuthMailView.as_view(), name='authmail'),
    path('sightlist/', views.Spotapi.as_view(), name='spot'),
    path('maplist/', views.Mapapi.as_view(), name='map'),
    path('sightdetail/', views.SpotDetailapi.as_view(), name='spot_detail'),
    path('review/', views.Reviewapi.as_view(), name='review'),
    path('postreview/', views.PostReview.as_view(), name='post_review'),
    path('cameraresult/', views.CameraResult.as_view(), name='camera_result'),
]
"""