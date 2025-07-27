from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User, Group
from django.views.generic import TemplateView, UpdateView
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import UserProfile, Department
from .forms import UserProfileForm
from complaints.models import Complaint, Status


class CustomLoginView(LoginView):
    """
    Custom login view with group-based access control.
    Only allows users from Admin, AMC Admin, and Engineer groups to log in.
    """
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    # Define allowed groups for login
    ALLOWED_GROUPS = ['Admin', 'AMC Admin', 'Engineer']
    
    def form_valid(self, form):
        """Validate user credentials and check group membership."""
        user = form.get_user()
        
        # Check if user belongs to allowed groups
        user_groups = user.groups.values_list('name', flat=True)
        has_allowed_group = any(group in self.ALLOWED_GROUPS for group in user_groups)
        
        if not has_allowed_group:
            # User exists but doesn't have required permissions
            messages.error(
                self.request, 
                'Access denied. This portal is restricted to IT staff only. '
                'Please contact your administrator if you believe this is an error.'
            )
            return self.form_invalid(form)
        
        # Create profile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        messages.success(
            self.request, 
            f'Welcome back, {user.get_full_name() or user.username}!'
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirect to dashboard after successful login."""
        return '/dashboard/'
    
    def form_invalid(self, form):
        """Handle invalid login attempts with proper error messages."""
        username = form.cleaned_data.get('username')
        
        if username:
            try:
                user = User.objects.get(username=username)
                # Check if user exists but doesn't have required groups
                user_groups = user.groups.values_list('name', flat=True)
                has_allowed_group = any(group in self.ALLOWED_GROUPS for group in user_groups)
                
                if not has_allowed_group:
                    messages.error(
                        self.request, 
                        'Access denied. This portal is restricted to IT staff only.'
                    )
                else:
                    # User exists and has correct groups, so password must be wrong
                    messages.error(self.request, 'Invalid password. Please try again.')
            except User.DoesNotExist:
                # User doesn't exist
                messages.error(
                    self.request, 
                    'Invalid username or password. Please check your credentials.'
                )
        else:
            messages.error(self.request, 'Please enter both username and password.')
        
        return super().form_invalid(form)


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