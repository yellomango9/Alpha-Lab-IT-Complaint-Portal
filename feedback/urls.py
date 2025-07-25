from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('', views.FeedbackListView.as_view(), name='list'),
    path('<int:pk>/', views.FeedbackDetailView.as_view(), name='detail'),
    path('complaint/<int:complaint_pk>/create/', views.FeedbackCreateView.as_view(), name='create'),
    path('stats/', views.feedback_stats, name='stats'),
]