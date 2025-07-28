from django.urls import path
from . import amc_admin_views

app_name = 'amc_admin'

urlpatterns = [
    # AMC Admin Dashboard
    path('', amc_admin_views.amc_admin_dashboard, name='dashboard'),
    path('complaint/<int:complaint_id>/', amc_admin_views.complaint_detail, name='complaint_detail'),
    path('complaint/<int:complaint_id>/update-priority/', amc_admin_views.update_complaint_priority, name='update_complaint_priority'),
    path('complaint/<int:complaint_id>/assign-engineer/', amc_admin_views.assign_engineer, name='assign_engineer'),
    path('reports/download/', amc_admin_views.download_complaints_report, name='download_complaints_report'),
    path('bulk-actions/', amc_admin_views.bulk_actions, name='bulk_actions'),
]