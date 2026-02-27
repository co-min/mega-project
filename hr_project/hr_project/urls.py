"""
URL configuration for hr_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # 루트 URL: 로그인 페이지로 리다이렉트
    path('', RedirectView.as_view(pattern_name='accounts:login', permanent=False), name='home'),
    # 근태 관리
    path('attendances/', include('attendances.urls')),
    # 직원 관리
    path('employees/', include('employees.urls')),
    # 스케줄 관리
    path('schedules/', include('schedules.urls')),
    # 급여 관리
    path('wages/', include('wages.urls')),
    # 계정 관리 (로그인/로그아웃/회원가입)
    path('accounts/', include('accounts.urls')),
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
