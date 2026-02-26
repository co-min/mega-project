from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from hr_project.models import UserProfile, Store

class SignUpForm(UserCreationForm):
    # User
    email = forms.EmailField(required = True)
    # Store
    store_name = forms.CharField(max_length=100, required = True)
    address = forms.CharField(max_length=255)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            UserProfile.objects.create(
                user=user,
                role='가맹점주'
            )
            
            Store.objects.create(
                owner=user,
                name=self.cleaned_data['store_name'],
                address=self.cleaned_data.get('address', '')
            )
            
        return user

class ProfileEditForm(forms.Form):
    # User 필드
    username = forms.CharField(label="이름", max_length=150, required=True)
    email = forms.EmailField(label="이메일", required=False)
    
    # Store 필드
    store_name = forms.CharField(label="매장 이름", max_length=100, required=True)
    address = forms.CharField(label="매장 주소", max_length=255, required=False)