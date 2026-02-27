from django.shortcuts import redirect


def home_view(request):
    if request.user.is_authenticated:
        # 로그인된 사용자는 근태 화면으로
        return redirect('attendances:attendances')
    else:
        # 비로그인 사용자는 로그인 페이지로
        return redirect('accounts:login')
