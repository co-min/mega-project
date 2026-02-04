from django.urls import path
from . import views

app_name = 'employees' 

urlpatterns = [
    path('', views.employees_list_view, name='employees_list'),
    path('form/', views.employee_form_view, name='employee_create'),
    path('form/<int:pk>/', views.employee_form_view, name='employee_edit'),
    path('delete/<int:pk>/', views.employee_delete_view, name='employee_delete'),
]