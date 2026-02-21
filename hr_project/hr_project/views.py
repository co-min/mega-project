from datetime import date
import calendar
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserProfile, UserSettings


def profile_view(request):
    """Profile page view"""
    
    context = {
        
    }
    
    return render(request, "profile.html", context)


def setting_view(request):
    """Settings page view"""
    
    context = {
        
    }
    
    return render(request, "setting.html", context)