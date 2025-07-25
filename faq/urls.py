from django.urls import path
from . import views

app_name = 'faq'

urlpatterns = [
    path('', views.FAQListView.as_view(), name='list'),
    path('<int:pk>/', views.FAQDetailView.as_view(), name='detail'),
    path('<int:pk>/helpful/', views.mark_faq_helpful, name='mark_helpful'),
]