from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Staff/Admin URLs
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Normal User URLs
    path('user/login/', views.normal_user_login, name='normal_user_login'),
    path('user/logout/', views.normal_user_logout, name='normal_user_logout'),
    path('user/dashboard/', views.normal_user_dashboard, name='normal_user_dashboard'),
    path('user/submit-complaint/', views.submit_complaint, name='submit_complaint'),
    path('user/complaints/', views.get_user_complaints, name='get_user_complaints'),
    path('user/complaint/<int:complaint_id>/', views.get_complaint_detail, name='get_complaint_detail'),
    path('user/complaint/<int:complaint_id>/response/', views.handle_complaint_response, name='handle_complaint_response'),
]