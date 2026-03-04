from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required = True)

    class Meta:
        model = User
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()

        return user

class StoreSetupForm(forms.Form):
    store_name = forms.CharField(max_length=100, required=True)
    address = forms.CharField(max_length=255, required=False)

class ProfileEditForm(forms.Form):
    # User 필드
    username = forms.CharField(label="이름", max_length=150, required=True)
    email = forms.EmailField(label="이메일", required=False)
    
    # Store 필드
    store_name = forms.CharField(label="매장 이름", max_length=100, required=True)
    address = forms.CharField(label="매장 주소", max_length=255, required=False)