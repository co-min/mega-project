# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from .models import UserProfile, UserSettings

# def profile_view(request):
#     """Profile page view"""
#     # 프로필 사진 업로드 처리
#     if request.method == 'POST' and request.FILES.get('profile_image'):
#         if request.user.is_authenticated:
#             profile, created = UserProfile.objects.get_or_create(user=request.user)
#             profile.profile_image = request.FILES['profile_image']
#             profile.save()
#             return redirect('profile')
    
#     # 임시 데이터 (실제로는 로그인 필요)
#     # user = request.user if request.user.is_authenticated else None
    
#     # 데모용 임시 데이터
#     profile_data = {
#         'name': 'Gavano',
#         'email': 'gavano@megacoffee.com',
#         'phone': '010-1234-5678',
#         'role': '가맹점주',
#     }
    
#     stores = [
#         {'name': '메가커피 강남점', 'address': '서울 강남구 테헤란로 123', 'is_primary': True},
#         {'name': '메가커피 서초점', 'address': '서울 서초구 서초대로 456', 'is_primary': False},
#         {'name': '메가커피 역삼점', 'address': '서울 강남구 역삼동 789', 'is_primary': False},
#     ]
    
#     # 실제 구현 (로그인 후):
#     # if request.user.is_authenticated:
#     #     profile, created = UserProfile.objects.get_or_create(user=request.user)
#     #     stores = Store.objects.filter(owner=request.user)
#     #     profile_data = {
#     #         'name': request.user.get_full_name() or request.user.username,
#     #         'email': request.user.email,
#     #         'phone': profile.phone,
#     #         'role': profile.role,
#     #         'profile_image': profile.profile_image.url if profile.profile_image else None,
#     #     }
    
#     context = {
#         'profile': profile_data,
#         'stores': stores,
#     }
    
#     return render(request, "accounts/profile.html", context)


# def setting_view(request):
#     """Settings page view"""
#     # 설정 저장 처리
#     if request.method == 'POST':
#         if request.user.is_authenticated:
#             settings, created = UserSettings.objects.get_or_create(user=request.user)
            
#             # 알림 설정
#             settings.email_notifications = request.POST.get('email_notifications') == 'on'
#             settings.push_notifications = request.POST.get('push_notifications') == 'on'
            
#             # 기본 설정
#             settings.language = request.POST.get('language', 'ko')
#             settings.theme = request.POST.get('theme', 'light')
            
#             settings.save()
#             messages.success(request, '설정이 저장되었습니다.')
#             return redirect('setting')
    
#     # 데모용 임시 데이터
#     settings_data = {
#         'email_notifications': True,
#         'push_notifications': True,
#         'language': 'ko',
#         'theme': 'light',
#     }
    
#     # 실제 구현 (로그인 후):
#     # if request.user.is_authenticated:
#     #     settings, created = UserSettings.objects.get_or_create(user=request.user)
#     #     settings_data = {
#     #         'email_notifications': settings.email_notifications,
#     #         'push_notifications': settings.push_notifications,
#     #         'language': settings.language,
#     #         'theme': settings.theme,
#     #     }
    
#     context = {
#         'settings': settings_data,
#     }
    
#     return render(request, "setting.html", context)