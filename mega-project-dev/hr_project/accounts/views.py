from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, ProfileEditForm

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('wages:wages')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

@login_required
def profile_edit_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    store = getattr(user, 'store', None)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST)
        if form.is_valid():
            user.username = form.cleaned_data['username']
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

    return render(request, 'accounts/profile_edit.html', {'form': form})