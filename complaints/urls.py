from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    # List and detail views
    path('', views.ComplaintListView.as_view(), name='list'),
    path('<int:pk>/', views.ComplaintDetailView.as_view(), name='detail'),
    
    # Create and edit views
    path('create/', views.ComplaintCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ComplaintUpdateView.as_view(), name='edit'),
    
    # AJAX endpoints
    path('<int:pk>/assign/', views.assign_complaint, name='assign'),
    
    # Legacy URLs for backward compatibility
    path('submit/', views.submit_complaint, name='submit'),
]
