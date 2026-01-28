from django.urls import path
from . import views

urlpatterns = [
    path('', views.employees_list_view, name='employees'),
    path('form/', views.employee_form_view, name='employee_form'),
    path('form/<int:pk>/', views.employee_form_view, name='employee_edit'),
    path('delete/<int:pk>/', views.employee_delete_view, name='employee_delete'),
]
