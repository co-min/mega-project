from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

def store_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        store = getattr(request.user, "store", None)
        if not store:
            messages.error(request, "매장을 먼저 등록해주세요.")
            return redirect("accounts:profile")
        return view_func(request, *args, **kwargs)
    return wrapper