from datetime import date
import calendar
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, Store, UserSettings


# Optional sample schedules (currently unused)
SAMPLE_SCHEDULES = {
    (2026, 1, 1): [{"name": "고길동", "color": "red", "start": "08:00", "end": "14:00"}],
    (2026, 1, 2): [{"name": "차마리", "color": "blue", "start": "10:00", "end": "16:00"}],
    (2026, 1, 3): [{"name": "김진화", "color": "green", "start": "16:00", "end": "22:00"}],
    (2026, 1, 4): [
        {"name": "고길동", "color": "red", "start": "08:00", "end": "14:00"},
        {"name": "차마리", "color": "blue", "start": "10:00", "end": "16:00"},
    ],
    (2026, 1, 5): [{"name": "김진화", "color": "green", "start": "16:00", "end": "22:00"}],
}


def build_month(year: int, month: int):
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdayscalendar(year, month)

    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    weeks_with_events = []
    for week in weeks:
        week_data = []
        for day in week:
            if day > 0:
                week_data.append({"day": day, "events": []})
            else:
                week_data.append({"day": 0, "events": []})
        weeks_with_events.append(week_data)

    return {
        "weeks": weeks_with_events,
        "weekdays": weekdays,
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "today": date.today(),
    }


def dashboard_view(request):
    # Read year/month from query params; default to today
    try:
        year = int(request.GET.get("year")) if request.GET.get("year") else date.today().year
        month = int(request.GET.get("month")) if request.GET.get("month") else date.today().month
    except ValueError:
        year = date.today().year
        month = date.today().month

    ctx = build_month(year, month)

    # Compute prev/next for navigation
    prev_month = month - 1
    prev_year = year
    next_month = month + 1
    next_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1
    if next_month > 12:
        next_month = 1
        next_year += 1

    ctx.update({
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
    })

    return render(request, "dashboard.html", ctx)


def profile_view(request):
    """Profile page view"""
    # 프로필 사진 업로드 처리
    if request.method == 'POST' and request.FILES.get('profile_image'):
        if request.user.is_authenticated:
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.profile_image = request.FILES['profile_image']
            profile.save()
            return redirect('profile')
    
    # 임시 데이터 (실제로는 로그인 필요)
    # user = request.user if request.user.is_authenticated else None
    
    # 데모용 임시 데이터
    profile_data = {
        'name': 'Gavano',
        'email': 'gavano@megacoffee.com',
        'phone': '010-1234-5678',
        'role': '가맹점주',
    }
    
    stores = [
        {'name': '메가커피 강남점', 'address': '서울 강남구 테헤란로 123', 'is_primary': True},
        {'name': '메가커피 서초점', 'address': '서울 서초구 서초대로 456', 'is_primary': False},
        {'name': '메가커피 역삼점', 'address': '서울 강남구 역삼동 789', 'is_primary': False},
    ]
    
    # 실제 구현 (로그인 후):
    # if request.user.is_authenticated:
    #     profile, created = UserProfile.objects.get_or_create(user=request.user)
    #     stores = Store.objects.filter(owner=request.user)
    #     profile_data = {
    #         'name': request.user.get_full_name() or request.user.username,
    #         'email': request.user.email,
    #         'phone': profile.phone,
    #         'role': profile.role,
    #         'profile_image': profile.profile_image.url if profile.profile_image else None,
    #     }
    
    context = {
        'profile': profile_data,
        'stores': stores,
    }
    
    return render(request, "profile.html", context)


def setting_view(request):
    """Settings page view"""
    # 설정 저장 처리
    if request.method == 'POST':
        if request.user.is_authenticated:
            settings, created = UserSettings.objects.get_or_create(user=request.user)
            
            # 알림 설정
            settings.email_notifications = request.POST.get('email_notifications') == 'on'
            settings.push_notifications = request.POST.get('push_notifications') == 'on'
            
            # 기본 설정
            settings.language = request.POST.get('language', 'ko')
            settings.theme = request.POST.get('theme', 'light')
            
            settings.save()
            messages.success(request, '설정이 저장되었습니다.')
            return redirect('setting')
    
    # 데모용 임시 데이터
    settings_data = {
        'email_notifications': True,
        'push_notifications': True,
        'language': 'ko',
        'theme': 'light',
    }
    
    # 실제 구현 (로그인 후):
    # if request.user.is_authenticated:
    #     settings, created = UserSettings.objects.get_or_create(user=request.user)
    #     settings_data = {
    #         'email_notifications': settings.email_notifications,
    #         'push_notifications': settings.push_notifications,
    #         'language': settings.language,
    #         'theme': settings.theme,
    #     }
    
    context = {
        'settings': settings_data,
    }
    
    return render(request, "setting.html", context)
