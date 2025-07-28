from django.urls import path
from . import admin_views

app_name = 'admin_portal'

urlpatterns = [
    # Admin Dashboard
    path('', admin_views.admin_dashboard, name='dashboard'),
    path('chart-data/', admin_views.get_chart_data, name='chart_data'),
    path('system-health/', admin_views.system_health, name='system_health'),
]