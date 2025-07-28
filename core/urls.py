from django.urls import path
from . import views, engineer_views, amc_admin_views

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
    
    # Engineer URLs
    path('engineer/', engineer_views.engineer_dashboard, name='engineer_dashboard'),
    path('complaint/<int:complaint_id>/', engineer_views.complaint_detail, name='complaint_detail'),
    path('complaint/<int:complaint_id>/update/', engineer_views.update_complaint_status, name='update_complaint_status'),
    path('complaint/<int:complaint_id>/pdf/', engineer_views.download_complaint_pdf, name='download_complaint_pdf'),
    
    # AMC Admin URLs
    path('admin/', amc_admin_views.amc_admin_dashboard, name='amc_admin_dashboard'),
    path('complaint/<int:complaint_id>/update-priority/', amc_admin_views.update_complaint_priority, name='update_complaint_priority'),
    path('complaint/<int:complaint_id>/assign-engineer/', amc_admin_views.assign_engineer, name='assign_engineer'),
    path('reports/download/', amc_admin_views.download_complaints_report, name='download_complaints_report'),
    path('bulk-actions/', amc_admin_views.bulk_actions, name='bulk_actions'),
]