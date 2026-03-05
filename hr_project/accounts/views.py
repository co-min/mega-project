from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, ProfileEditForm, User
from .models import Store, UserProfile
from django.conf import settings
import requests 
from django.http import JsonResponse  
from .forms import StoreSetupForm

def login_view(request):
    """
    커스텀 로그인 뷰
    
    GET 요청: 로그인 폼 화면을 렌더링
    POST 요청: 사용자 인증 처리
    
    [동작 흐름]
    1. 이미 로그인된 사용자가 접근하면 근태 화면으로 즉시 리다이렉트
    2. POST 요청에서 username과 password를 받아 인증 시도
    3. 인증 성공 시:
       - 세션에 사용자 정보 저장 (login 함수)
       - URL의 ?next= 파라미터가 있으면 해당 페이지로 이동
       - 없으면 근태 화면(attendances:attendances)으로 이동
    4. 인증 실패 시:
       - 에러 정보를 포함한 로그인 폼 재표시
    
    [보안]
    - authenticate() 함수가 자동으로 비밀번호 해시 검증
    - Django의 CSRF 토큰으로 요청 위조 방지
    """
    # 이미 로그인된 사용자는 next 파라미터가 있으면 해당 페이지로, 없으면 근태 화면으로 리다이렉트
    if request.user.is_authenticated:
        next_url = request.GET.get('next', 'attendances:attendances')
        return redirect(next_url)
    
    if request.method == 'POST':
        # 로그인 폼에서 제출된 데이터 가져오기
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Django 인증 시스템으로 사용자 확인
        # authenticate()는 자동으로 비밀번호 해시를 검증
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 인증 성공: 세션에 사용자 정보 저장
            login(request, user)
            
            # ?next= 파라미터가 있으면 해당 페이지로, 없으면 근태 화면으로
            # 예: /accounts/login/?next=/employees/ → 로그인 후 /employees/로 이동
            next_url = request.GET.get('next', 'attendances:attendances')
            return redirect(next_url)
        else:
            # 인증 실패: 에러를 표시하기 위해 form 객체 생성
            # login.html의 {% if form.errors %} 조건이 True가 되도록
            class LoginForm:
                errors = True
            
            return render(request, 'account/login.html', {'form': LoginForm()})
    
    # GET 요청: 로그인 폼 화면 표시
    return render(request, 'account/login.html')

@login_required
def profile_view(request):
    return render(request, 'account/profile.html')


@login_required
def profile_edit_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    store = getattr(user, 'store', None)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
                messages.error(request, "이미 사용중인 이름입니다.")
                return redirect("accounts:profile_edit")
            user.username = username
            user.email = form.cleaned_data['email']
            user.save()

            if store:
                store.name = form.cleaned_data['store_name']
                store.address = form.cleaned_data['address']
                store.save()

            messages.success(request, '프로필 정보가 성공적으로 수정되었습니다.')
            return redirect('accounts:profile') 
    else:
        initial_data = {
            'username': user.username,
            'email': user.email,
            'store_name': store.name if store else '',
            'address': store.address if store else '',
        }
        form = ProfileEditForm(initial=initial_data)

    return render(request, 'account/profile_edit.html', {'form': form})

# 카카오 맵 설정
def kakao_search(request):
    keyword = request.GET.get("keyword")

    if not keyword:
        return JsonResponse({"documents": []})

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {
        "Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}"
    }
    print("내가 보낼 헤더:", headers)
    

    params = {
        "query": keyword,
        "size": 5
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return JsonResponse(response.json())
        
    except requests.exceptions.RequestException as e:
        print(f"카카오 API 통신 에러: {e}")
        if response is not None:
            print(f"카카오 서버 응답: {response.text}")
            
        return JsonResponse({"error": "검색에 실패했습니다."}, status=500)
    

# 구글 로그인 시 매장 생성 (설정)
@login_required
def store_setup_view(request):
    if hasattr(request.user, "store"):
        return redirect("attendances:attendances")

    if request.method == "POST":
        form = StoreSetupForm(request.POST)
        if form.is_valid():
            Store.objects.create(
                owner=request.user,
                name=form.cleaned_data['store_name'],
                address=form.cleaned_data.get('address', '')
            )
            return redirect("attendances:attendances")
        else:
            form = StoreSetupForm()
    return render(request, "account/store_setup.html")