"""
URL configuration for the reports app.
Defines routes for dashboard, report generation, and analytics.
"""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Reports
    path('list/', views.ReportsListView.as_view(), name='list'),
    path('generate/', views.generate_report, name='generate'),
    path('detail/<int:pk>/', views.ReportDetailView.as_view(), name='detail'),
    
    # API endpoints
    path('api/chart-data/', views.chart_data_api, name='chart_data_api'),
]