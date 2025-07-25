from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone

from .models import Complaint, FileAttachment, Status, ComplaintType
from .forms import ComplaintForm, ComplaintUpdateForm, FileAttachmentForm
from core.models import UserProfile


class ComplaintListView(LoginRequiredMixin, ListView):
    """List view for complaints with role-based functionality."""
    model = Complaint
    context_object_name = 'complaints'
    paginate_by = 10
    
    def get_template_names(self):
        """Return template based on user role."""
        user = self.request.user
        if hasattr(user, 'profile'):
            if user.profile.is_admin:
                return ['complaints/admin_list.html']
            elif user.profile.is_engineer:
                return ['complaints/engineer_list.html']
        return ['complaints/user_list.html']
    
    def get_queryset(self):
        queryset = Complaint.objects.select_related('user', 'type', 'status', 'assigned_to')
        user = self.request.user
        
        # Role-based filtering
        if hasattr(user, 'profile'):
            if user.profile.is_admin:
                # Admins see all complaints with full details
                pass
            elif user.profile.is_engineer:
                # Engineers see all complaints they can work on
                pass
            elif user.profile.role and user.profile.role.name.lower() == 'amc_admin':
                # AMC Admins see only AMC-related complaints
                queryset = queryset.filter(
                    Q(type__name__icontains='hardware') | 
                    Q(type__name__icontains='maintenance') |
                    Q(type__name__icontains='amc')
                )
        else:
            # Regular users see only their complaints
            queryset = queryset.filter(user=user)
        
        # Apply filters only for admin/engineer views
        if hasattr(user, 'profile') and (user.profile.is_admin or user.profile.is_engineer):
            status_filter = self.request.GET.get('status')
            type_filter = self.request.GET.get('type')
            urgency_filter = self.request.GET.get('urgency')
            search_query = self.request.GET.get('search')
            assigned_filter = self.request.GET.get('assigned_to')
            
            if status_filter:
                queryset = queryset.filter(status_id=status_filter)
            if type_filter:
                queryset = queryset.filter(type_id=type_filter)
            if urgency_filter:
                queryset = queryset.filter(urgency=urgency_filter)
            if assigned_filter:
                queryset = queryset.filter(assigned_to_id=assigned_filter)
            if search_query:
                queryset = queryset.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(id__icontains=search_query)
                )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Basic context for all users
        context['user_role'] = 'user'  # default
        
        if hasattr(user, 'profile') and user.profile.role:
            context['user_role'] = user.profile.role.name.lower()
        
        # Add role-specific context
        if hasattr(user, 'profile') and (user.profile.is_admin or user.profile.is_engineer):
            context.update({
                'statuses': Status.objects.filter(is_active=True),
                'complaint_types': ComplaintType.objects.filter(is_active=True),
                'urgency_choices': Complaint.URGENCY_CHOICES,
                'engineers': UserProfile.objects.filter(
                    role__name__icontains='engineer'
                ).select_related('user'),
                'current_filters': {
                    'status': self.request.GET.get('status', ''),
                    'type': self.request.GET.get('type', ''),
                    'urgency': self.request.GET.get('urgency', ''),
                    'search': self.request.GET.get('search', ''),
                    'assigned_to': self.request.GET.get('assigned_to', ''),
                }
            })
        
        # Status counts for all roles
        if hasattr(user, 'profile') and user.profile.is_admin:
            all_complaints = Complaint.objects.all()
        elif hasattr(user, 'profile') and user.profile.is_engineer:
            all_complaints = Complaint.objects.all()
        else:
            all_complaints = Complaint.objects.filter(user=user)
            
        context.update({
            'total_count': all_complaints.count(),
            'open_count': all_complaints.filter(status__name='Open').count(),
            'in_progress_count': all_complaints.filter(status__name='In Progress').count(),
            'resolved_count': all_complaints.filter(status__is_closed=True).count(),
        })
        
        return context


class ComplaintDetailView(LoginRequiredMixin, DetailView):
    """Detail view for individual complaints with role-based functionality."""
    model = Complaint
    context_object_name = 'complaint'
    
    def get_template_names(self):
        """Return template based on user role."""
        user = self.request.user
        if hasattr(user, 'profile'):
            if user.profile.is_admin:
                return ['complaints/admin_detail.html']
            elif user.profile.is_engineer:
                return ['complaints/engineer_detail.html']
        return ['complaints/user_detail.html']
    
    def get_queryset(self):
        queryset = Complaint.objects.select_related('user', 'type', 'status', 'assigned_to')
        
        # Users can only view their own complaints unless they're engineers/admins
        user = self.request.user
        if not (user.is_staff or (hasattr(user, 'profile') and (user.profile.is_engineer or user.profile.is_admin))):
            queryset = queryset.filter(user=user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Basic context for all users
        context.update({
            'attachments': self.object.attachments.all(),
            'status_history': StatusHistory.objects.filter(
                complaint=self.object
            ).select_related('changed_by').order_by('-created_at'),
        })
        
        # Role-specific context
        if hasattr(user, 'profile'):
            if user.profile.is_admin:
                context.update({
                    'can_edit': True,
                    'can_assign': True,
                    'can_change_status': True,
                    'can_delete': True,
                    'available_statuses': Status.objects.filter(is_active=True),
                    'engineers': UserProfile.objects.filter(
                        role__name__icontains='engineer'
                    ).select_related('user'),
                })
            elif user.profile.is_engineer:
                context.update({
                    'can_edit': True,
                    'can_assign': False,  # Engineers typically can't reassign
                    'can_change_status': True,
                    'can_delete': False,
                    'available_statuses': Status.objects.filter(
                        is_active=True, 
                        name__in=['In Progress', 'Resolved', 'Closed']
                    ),
                })
        else:
            # Regular user context
            context.update({
                'can_edit': self.object.user == user and not self.object.status.is_closed,
                'can_assign': False,
                'can_change_status': False,
                'can_delete': False,
                'can_provide_feedback': (
                    self.object.status.is_closed and 
                    self.object.user == user and 
                    not hasattr(self.object, 'feedback')
                ),
            })
        
        return context


class ComplaintCreateView(LoginRequiredMixin, CreateView):
    """Create view for new complaints."""
    model = Complaint
    form_class = ComplaintForm
    template_name = 'complaints/submit.html'
    
    def form_valid(self, form):
        complaint = form.save(commit=False)
        complaint.user = self.request.user
        
        # Set default status (first active status or create one)
        default_status, created = Status.objects.get_or_create(
            name='Open',
            defaults={'description': 'Complaint submitted and awaiting review', 'order': 1}
        )
        complaint.status = default_status
        complaint.save()
        
        # Handle file attachments
        files = self.request.FILES.getlist('attachments')
        for file in files:
            FileAttachment.objects.create(
                complaint=complaint,
                file=file,
                original_filename=file.name,
                file_size=file.size,
                content_type=file.content_type,
                uploaded_by=self.request.user
            )
        
        messages.success(self.request, f'Complaint #{complaint.id} submitted successfully!')
        return redirect('complaints:detail', pk=complaint.pk)


class ComplaintUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for existing complaints."""
    model = Complaint
    template_name = 'complaints/edit.html'
    
    def get_form_class(self):
        """Return appropriate form based on user role."""
        user = self.request.user
        if hasattr(user, 'profile') and (user.profile.is_engineer or user.profile.is_admin):
            return ComplaintUpdateForm
        else:
            return ComplaintForm
    
    def get_queryset(self):
        queryset = Complaint.objects.select_related('user', 'type', 'status')
        
        # Users can only edit their own complaints unless they're engineers/admins
        user = self.request.user
        if not (hasattr(user, 'profile') and (user.profile.is_engineer or user.profile.is_admin)):
            queryset = queryset.filter(user=user, status__is_closed=False)
        
        return queryset
    
    def form_valid(self, form):
        complaint = form.save(commit=False)
        
        # If status changed to resolved, set resolved_at
        if complaint.status and complaint.status.is_closed and not complaint.resolved_at:
            complaint.resolved_at = timezone.now()
        
        complaint.save()
        
        messages.success(self.request, 'Complaint updated successfully!')
        return redirect('complaints:detail', pk=complaint.pk)


@login_required
def assign_complaint(request, pk):
    """Assign complaint to an engineer (AJAX endpoint)."""
    if not (hasattr(request.user, 'profile') and request.user.profile.is_engineer):
        return HttpResponseForbidden()
    
    complaint = get_object_or_404(Complaint, pk=pk)
    engineer_id = request.POST.get('engineer_id')
    
    if engineer_id:
        try:
            engineer = UserProfile.objects.get(id=engineer_id, role__name__icontains='engineer').user
            complaint.assigned_to = engineer
            complaint.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Complaint assigned to {engineer.get_full_name() or engineer.username}'
            })
        except UserProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Engineer not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


# Legacy function-based view for backward compatibility
@login_required
def submit_complaint(request):
    """Legacy submit complaint view - redirects to class-based view."""
    return redirect('complaints:create')
