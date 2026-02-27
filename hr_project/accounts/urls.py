from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # 커스텀 로그인 뷰 사용 (근태 화면으로 리다이렉트 기능 포함)
    path('login/', views.login_view, name='login'),
    # Django 기본 로그아웃 뷰 (로그아웃 후 로그인 페이지로 이동)
    path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),
    # 회원가입
    path('signup/', views.signup_view, name='signup'),
    # 프로필 조회/수정
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
]