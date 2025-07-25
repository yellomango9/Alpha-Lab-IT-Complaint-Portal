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
    """List view for complaints with filtering and pagination."""
    model = Complaint
    template_name = 'complaints/list.html'
    context_object_name = 'complaints'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Complaint.objects.select_related('user', 'type', 'status', 'assigned_to')
        
        # Filter by user role
        user = self.request.user
        if user.is_staff or (hasattr(user, 'profile') and (user.profile.is_engineer or user.profile.is_admin)):
            # Engineers/admins see all complaints
            pass
        else:
            # Regular users see only their complaints
            queryset = queryset.filter(user=user)
        
        # Apply filters
        status_filter = self.request.GET.get('status')
        type_filter = self.request.GET.get('type')
        urgency_filter = self.request.GET.get('urgency')
        search_query = self.request.GET.get('search')
        
        if status_filter:
            queryset = queryset.filter(status_id=status_filter)
        
        if type_filter:
            queryset = queryset.filter(type_id=type_filter)
        
        if urgency_filter:
            queryset = queryset.filter(urgency=urgency_filter)
        
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(id__icontains=search_query)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'statuses': Status.objects.filter(is_active=True),
            'complaint_types': ComplaintType.objects.filter(is_active=True),
            'urgency_choices': Complaint.URGENCY_CHOICES,
            'current_filters': {
                'status': self.request.GET.get('status', ''),
                'type': self.request.GET.get('type', ''),
                'urgency': self.request.GET.get('urgency', ''),
                'search': self.request.GET.get('search', ''),
            }
        })
        return context


class ComplaintDetailView(LoginRequiredMixin, DetailView):
    """Detail view for individual complaints."""
    model = Complaint
    template_name = 'complaints/detail.html'
    context_object_name = 'complaint'
    
    def get_queryset(self):
        queryset = Complaint.objects.select_related('user', 'type', 'status', 'assigned_to')
        
        # Users can only view their own complaints unless they're engineers/admins
        user = self.request.user
        if not (user.is_staff or (hasattr(user, 'profile') and (user.profile.is_engineer or user.profile.is_admin))):
            queryset = queryset.filter(user=user)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attachments'] = self.object.attachments.all()
        context['can_edit'] = self.can_edit_complaint()
        return context
    
    def can_edit_complaint(self):
        """Check if user can edit this complaint."""
        user = self.request.user
        complaint = self.object
        
        # Owner can edit if not resolved
        if complaint.user == user and not complaint.is_resolved:
            return True
        
        # Engineers/admins can always edit
        if hasattr(user, 'profile') and user.profile.is_engineer:
            return True
        
        return False


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
    form_class = ComplaintUpdateForm
    template_name = 'complaints/edit.html'
    
    def get_queryset(self):
        queryset = Complaint.objects.select_related('user', 'type', 'status')
        
        # Users can only edit their own complaints unless they're engineers/admins
        user = self.request.user
        if not (hasattr(user, 'profile') and user.profile.is_engineer):
            queryset = queryset.filter(user=user, status__is_closed=False)
        
        return queryset
    
    def get_form_class(self):
        """Return appropriate form based on user role."""
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.is_engineer:
            return ComplaintUpdateForm  # Full form for engineers
        else:
            return ComplaintForm  # Limited form for regular users
    
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
