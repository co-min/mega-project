from django.urls import path
from . import views

app_name = 'employees' 

urlpatterns = [
    path('', views.employees_list_view, name='list'),
    path('create/', views.create_employee_form_view, name='create'),
    path('edit/<int:pk>/', views.edit_employee_form_view, name='edit'),
    path('delete/<int:pk>/', views.employee_delete_view, name='delete'),
]