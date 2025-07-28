from django.urls import path
from . import engineer_views

app_name = 'engineer'

urlpatterns = [
    # Engineer Dashboard
    path('', engineer_views.engineer_dashboard, name='dashboard'),
    path('complaint/<int:complaint_id>/', engineer_views.complaint_detail, name='complaint_detail'),
    path('complaint/<int:complaint_id>/assign-to-self/', engineer_views.assign_to_self, name='assign_to_self'),
    path('complaint/<int:complaint_id>/update/', engineer_views.update_complaint_status, name='update_complaint_status'),
    path('complaint/<int:complaint_id>/pdf/', engineer_views.download_complaint_pdf, name='download_complaint_pdf'),
]