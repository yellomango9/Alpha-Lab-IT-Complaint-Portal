from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import UserProfile, Department, Role
from .forms import UserProfileForm
from complaints.models import Complaint, Status


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard view showing user statistics and recent activity."""
    template_name = 'core/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's complaints statistics
        user_complaints = Complaint.objects.filter(user=user)
        
        context.update({
            'total_complaints': user_complaints.count(),
            'open_complaints': user_complaints.filter(status__is_closed=False).count(),
            'resolved_complaints': user_complaints.filter(status__is_closed=True).count(),
            'recent_complaints': user_complaints[:5],
        })
        
        # If user is engineer/admin, show assigned complaints
        if hasattr(user, 'profile') and user.profile.is_engineer:
            assigned_complaints = Complaint.objects.filter(assigned_to=user)
            context.update({
                'assigned_complaints': assigned_complaints.count(),
                'pending_assignments': assigned_complaints.filter(status__is_closed=False).count(),
                'recent_assignments': assigned_complaints[:5],
            })
        
        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view."""
    template_name = 'core/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        context['profile'] = profile
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile view."""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'core/profile_edit.html'
    success_url = '/core/profile/'
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)