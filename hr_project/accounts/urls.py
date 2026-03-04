from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='account_login'), name='logout'),
    path('setup/', views.store_setup_view, name = 'store_setup'),
    path('kakao_search/', views.kakao_search, name = 'kakao_search'),
    path('accounts/', include('allauth.urls')),
]