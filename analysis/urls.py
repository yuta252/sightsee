from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('edit/<int:pk>/', views.EditView.as_view(), name='upload_edit'),
    path('delete/', views.DeleteView.as_view(), name='delete'),
    path('mypage/', views.MypageView.as_view(), name='mypage'),
    path('setting/<int:pk>/', views.SettingView.as_view(), name='setting'),
    path('user_delete/', views.UserLangDeleteView.as_view(), name='userlang_delete'),
    path('user_edit/', views.UserLangEditView.as_view(), name='userlang_edit'),
    path('user_edit_ajax/', views.UserLangEditAJAXView.as_view(), name='userlang_edit_ajax'),
    path('email/change/', views.EmailChange.as_view(), name='email_change'),
    path('email/change/done/', views.EmailChangeDone.as_view(), name='email_change_done'),
    path('email/change/complete/<str:token>/', views.EmailChangeComplete.as_view(), name='email_change_complete'),
    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_change/done/', views.PasswordChangeDone.as_view(), name='password_change_done'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/done', views.ContactDone.as_view(), name='contact_done'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('signup/done', views.SignupDone.as_view(), name='signup_done'),
    path('signup/complete/<token>/', views.SignupComplete.as_view(), name='signup_complete'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Login.as_view(), name='logout'),
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDone.as_view(), name='password_reset_done'),
    path('password_reset/confirm/<uidb64>/<token>/', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('password_reset/complete/', views.PasswordResetComplete.as_view(), name='password_reset_complete'),
    # path('sightseeapi/', views.Spotapi.as_view(), name='spotapi'),
    # path('sightdetailapi/', views.SpotDetailapi.as_view(), name='spotDetailapi'),
]
