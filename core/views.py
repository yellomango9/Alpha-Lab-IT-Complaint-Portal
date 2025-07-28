from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User, Group
from django.views.generic import TemplateView, UpdateView
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import timedelta

from .models import UserProfile, Department
from .forms import UserProfileForm, NormalUserLoginForm
from complaints.models import Complaint, Status, ComplaintType, FileAttachment
from complaints.forms import ComplaintForm
from faq.models import FAQ, FAQCategory


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
        """Redirect based on user type after successful login."""
        user = self.request.user
        
        # Check user groups to determine redirect
        if user.groups.filter(name='AMC Admin').exists() or user.is_superuser:
            return '/core/admin/'
        elif user.groups.filter(name__in=['Engineer', 'Admin']).exists() or user.is_staff:
            return '/core/engineer/'
        else:
            # Default to engineer dashboard for any authenticated staff
            return '/core/engineer/'
    
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


# Normal User Views
def normal_user_login(request):
    """Login view for normal users (non-staff) using name and main_portal_id."""
    if request.method == 'POST':
        form = NormalUserLoginForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            main_portal_id = form.cleaned_data['main_portal_id']
            department = form.cleaned_data['department']
            
            # Try to find existing user profile by main_portal_id
            try:
                profile = UserProfile.objects.get(main_portal_id=main_portal_id)
                # Update name and department if different
                if profile.user.get_full_name() != name:
                    name_parts = name.split(' ', 1)
                    profile.user.first_name = name_parts[0]
                    profile.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
                    profile.user.save()
                
                # Update department
                profile.department = department
                profile.save()
                
                user_data = {
                    'user_id': profile.user.id,
                    'name': name,
                    'main_portal_id': main_portal_id,
                    'department': department.name,
                    'is_normal_user': True
                }
            except UserProfile.DoesNotExist:
                # Create new user and profile for first-time users
                name_parts = name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                # Create username from main_portal_id
                username = f"user_{main_portal_id}"
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=''  # No email required for normal users
                )
                
                # Create profile
                profile = UserProfile.objects.create(
                    user=user,
                    main_portal_id=main_portal_id,
                    department=department
                )
                
                user_data = {
                    'user_id': user.id,
                    'name': name,
                    'main_portal_id': main_portal_id,
                    'department': department.name,
                    'is_normal_user': True
                }
            
            # Store user data in session
            request.session['normal_user'] = user_data
            messages.success(request, f'Welcome to IT Complaint Portal, {name}!')
            return redirect('core:normal_user_dashboard')
    else:
        form = NormalUserLoginForm()
    
    return render(request, 'core/normal_user_login.html', {'form': form})


def normal_user_logout(request):
    """Logout view for normal users."""
    if 'normal_user' in request.session:
        del request.session['normal_user']
    messages.info(request, 'You have been logged out successfully.')
    return redirect('core:normal_user_login')


def normal_user_required(view_func):
    """Decorator to check if user is logged in as normal user."""
    def wrapper(request, *args, **kwargs):
        if 'normal_user' not in request.session:
            messages.error(request, 'Please log in to access this page.')
            return redirect('core:normal_user_login')
        return view_func(request, *args, **kwargs)
    return wrapper


@normal_user_required
def normal_user_dashboard(request):
    """Dashboard view for normal users showing complaint form, status, and FAQ."""
    user_data = request.session.get('normal_user', {})
    user_id = user_data.get('user_id')
    
    if not user_id:
        return redirect('core:normal_user_login')
    
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        return redirect('core:normal_user_login')
    
    # Get user's complaints
    user_complaints = Complaint.objects.filter(user=user).order_by('-created_at')
    
    # Get complaint types and statuses for form
    complaint_types = ComplaintType.objects.filter(is_active=True).order_by('name')
    
    # Get FAQs grouped by category
    faq_categories = FAQCategory.objects.filter(is_active=True).prefetch_related('faqs').order_by('order', 'name')
    
    context = {
        'user_data': user_data,
        'user_complaints': user_complaints,
        'complaint_types': complaint_types,
        'faq_categories': faq_categories,
        'profile': profile,
    }
    
    return render(request, 'core/normal_user_dashboard.html', context)


@normal_user_required
def submit_complaint(request):
    """AJAX view to handle complaint submission from normal users."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
        
    user_data = request.session.get('normal_user', {})
    user_id = user_data.get('user_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'error': 'User not authenticated'})
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})
    
    form = ComplaintForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            # Create complaint
            complaint = form.save(commit=False)
            complaint.user = user
            
            # Generate title from description (first 50 chars)
            description = form.cleaned_data.get('description', '')
            complaint.title = description[:50] + '...' if len(description) > 50 else description
            
            # Force urgency to low for normal users
            complaint.urgency = 'low'
            
            # Set default status (first active status)
            default_status = Status.objects.filter(is_active=True).order_by('order').first()
            if default_status:
                complaint.status = default_status
            
            complaint.save()
            
            # Handle file attachments
            files = request.FILES.getlist('attachments')
            if files:
                for file in files:
                    attachment = FileAttachment.objects.create(
                        complaint=complaint,
                        file=file,
                        original_filename=file.name,
                        file_size=file.size,
                        content_type=file.content_type,
                        uploaded_by=user
                    )
            
            return JsonResponse({
                'success': True,
                'message': f'Complaint #{complaint.id} submitted successfully!',
                'complaint_id': complaint.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error creating complaint: {str(e)}'})
    
    else:
        # Return form errors
        errors = {}
        for field, field_errors in form.errors.items():
            errors[field] = field_errors
        return JsonResponse({'success': False, 'errors': errors})


@normal_user_required
def get_user_complaints(request):
    """AJAX view to get user's complaints."""
    user_data = request.session.get('normal_user', {})
    user_id = user_data.get('user_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'error': 'User not authenticated'})
    
    try:
        user = User.objects.get(id=user_id)
        complaints = Complaint.objects.filter(user=user).select_related(
            'type', 'status', 'assigned_to'
        ).prefetch_related('closing_details').order_by('-created_at')
        
        complaints_data = []
        for complaint in complaints:
            # Get closing details if available
            closing_details = getattr(complaint, 'closing_details', None)
            
            complaints_data.append({
                'id': complaint.id,
                'title': complaint.title or complaint.description[:50] + '...',
                'type': complaint.type.name,
                'status': complaint.status.name,
                'urgency': complaint.get_urgency_display(),
                'created_at': complaint.created_at.strftime('%Y-%m-%d %H:%M'),
                'is_resolved': complaint.is_resolved,
                'days_open': complaint.days_open,
                'staff_closing_remark': closing_details.staff_closing_remark if closing_details else None,
                'closed_by_staff': closing_details.closed_by_staff.get_full_name() if closing_details else None,
                'staff_closed_at': closing_details.staff_closed_at.strftime('%b %d, %Y at %I:%M %p') if closing_details else None,
                'user_satisfied': closing_details.user_satisfied if closing_details else None,
            })
        
        return JsonResponse({'success': True, 'complaints': complaints_data})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})


@normal_user_required
def get_complaint_detail(request, complaint_id):
    """AJAX view to get detailed complaint information."""
    user_data = request.session.get('normal_user', {})
    user_id = user_data.get('user_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'error': 'User not authenticated'})
    
    try:
        user = User.objects.get(id=user_id)
        complaint = get_object_or_404(Complaint, id=complaint_id, user=user)
        
        # Get attachments
        attachments = []
        for attachment in complaint.attachments.all():
            attachments.append({
                'id': attachment.id,
                'filename': attachment.original_filename,
                'size': attachment.file_size_formatted,
                'uploaded_at': attachment.uploaded_at.strftime('%Y-%m-%d %H:%M')
            })
        
        complaint_data = {
            'id': complaint.id,
            'title': complaint.title,
            'description': complaint.description,
            'type': complaint.type.name,
            'status': complaint.status.name,
            'urgency': complaint.get_urgency_display(),
            'location': complaint.location,
            'contact_number': complaint.contact_number,
            'created_at': complaint.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': complaint.updated_at.strftime('%Y-%m-%d %H:%M'),
            'is_resolved': complaint.is_resolved,
            'days_open': complaint.days_open,
            'attachments': attachments,
            'assigned_to': complaint.assigned_to.get_full_name() if complaint.assigned_to else 'Unassigned'
        }
        
        return JsonResponse({'success': True, 'complaint': complaint_data})
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})


@normal_user_required
def handle_complaint_response(request, complaint_id):
    """Handle user response when staff closes a complaint."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    user_data = request.session.get('normal_user', {})
    user_id = user_data.get('user_id')
    
    try:
        user = User.objects.get(id=user_id)
        complaint = Complaint.objects.get(id=complaint_id, user=user)
    except (User.DoesNotExist, Complaint.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Complaint not found'})
    
    # Check if complaint has closing details
    closing_details = getattr(complaint, 'closing_details', None)
    if not closing_details:
        return JsonResponse({'success': False, 'error': 'Complaint not closed by staff yet'})
    
    action = request.POST.get('action')
    
    if action == 'satisfied':
        # User is satisfied, ask for feedback
        closing_details.user_satisfied = True
        closing_details.user_closed_at = timezone.now()
        closing_details.save()
        
        return JsonResponse({
            'success': True, 
            'action': 'feedback',
            'message': 'Thank you! Please provide your feedback.'
        })
    
    elif action == 'not_satisfied':
        # User is not satisfied, collect remark
        user_remark = request.POST.get('user_remark', '').strip()
        if not user_remark:
            return JsonResponse({'success': False, 'error': 'Please provide a remark about why you are not satisfied'})
        
        closing_details.user_satisfied = False
        closing_details.user_closing_remark = user_remark
        closing_details.save()
        
        # Reopen the complaint
        open_status = Status.objects.filter(is_active=True, is_closed=False).order_by('order').first()
        if open_status:
            complaint.status = open_status
            complaint.resolved_at = None
            complaint.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Your complaint has been reopened. We will review your concerns.'
        })
    
    elif action == 'submit_feedback':
        # Submit final feedback
        rating = request.POST.get('rating')
        feedback_text = request.POST.get('feedback_text', '').strip()
        
        if not rating or not rating.isdigit() or int(rating) not in range(1, 6):
            return JsonResponse({'success': False, 'error': 'Please provide a valid rating (1-5)'})
        
        from complaints.models import ComplaintFeedback
        
        # Create or update feedback
        feedback, created = ComplaintFeedback.objects.get_or_create(
            complaint=complaint,
            defaults={
                'user': user,
                'rating': int(rating),
                'feedback_text': feedback_text
            }
        )
        
        if not created:
            feedback.rating = int(rating)
            feedback.feedback_text = feedback_text
            feedback.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your feedback! Your complaint is now closed.'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid action'})