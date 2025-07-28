from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta, datetime
from django.template.loader import get_template
from io import BytesIO
import csv

from .models import UserProfile, Department
from complaints.models import Complaint, Status, ComplaintType


def amc_admin_required(view_func):
    """Decorator to check if user is AMC admin or admin."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user is AMC admin or admin
        if not (request.user.groups.filter(name__in=['AMC ADMIN', 'ADMIN']).exists() or 
                request.user.is_staff):
            messages.error(request, 'Access denied. You need AMC admin or admin privileges.')
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


@amc_admin_required
def amc_admin_dashboard(request):
    """AMC Admin dashboard with all open complaints and filtering options."""
    
    # Get filter parameters
    complaint_type = request.GET.get('type')
    status_filter = request.GET.get('status')
    engineer_filter = request.GET.get('engineer')
    department_filter = request.GET.get('department')
    
    # Base queryset for open complaints
    complaints = Complaint.objects.filter(
        status__is_closed=False
    ).select_related('user', 'type', 'status', 'assigned_to', 'user__profile__department')
    
    # Apply filters
    if complaint_type:
        complaints = complaints.filter(type_id=complaint_type)
    if status_filter:
        complaints = complaints.filter(status_id=status_filter)
    if engineer_filter:
        if engineer_filter == 'unassigned':
            complaints = complaints.filter(assigned_to__isnull=True)
        else:
            complaints = complaints.filter(assigned_to_id=engineer_filter)
    if department_filter:
        complaints = complaints.filter(user__profile__department_id=department_filter)
    
    complaints = complaints.order_by('-created_at')
    
    # Get issues (complaints unresolved for more than 2 days)
    two_days_ago = timezone.now() - timedelta(days=2)
    issues = Complaint.objects.filter(
        status__is_closed=False,
        created_at__lt=two_days_ago
    ).select_related('user', 'type', 'status', 'assigned_to', 'user__profile__department').order_by('created_at')
    
    # Get filter options
    complaint_types = ComplaintType.objects.filter(is_active=True).order_by('name')
    statuses = Status.objects.filter(is_active=True, is_closed=False).order_by('order')
    engineers = User.objects.filter(
        groups__name__in=['ENGINEER'],  # Only engineers for assignment
        is_active=True
    ).order_by('first_name', 'last_name')
    departments = Department.objects.filter(is_active=True).order_by('name')
    
    context = {
        'complaints': complaints,
        'issues': issues,
        'complaint_types': complaint_types,
        'statuses': statuses,
        'engineers': engineers,
        'departments': departments,
        'total_complaints': complaints.count(),
        'total_issues': issues.count(),
        # Current filter values
        'current_type': complaint_type,
        'current_status': status_filter,
        'current_engineer': engineer_filter,
        'current_department': department_filter,
    }
    
    return render(request, 'core/amc_admin_dashboard.html', context)


@amc_admin_required
def complaint_detail(request, complaint_id):
    """Detailed view of a complaint for AMC admins."""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    # Get complaint history
    status_history = complaint.status_history.all().order_by('-changed_at')
    remarks = complaint.remarks.all().order_by('-created_at')  # Show all remarks
    attachments = complaint.attachments.all().order_by('-uploaded_at')
    
    # Check if complaint has closing details
    closing_details = getattr(complaint, 'closing_details', None)
    
    # Get available status options for updates
    status_options = Status.objects.filter(is_active=True).order_by('order')
    
    # Get engineers for assignment
    engineers = User.objects.filter(
        groups__name__in=['ENGINEER'],
        is_active=True
    ).order_by('first_name', 'last_name')
    
    context = {
        'complaint': complaint,
        'status_history': status_history,
        'remarks': remarks,
        'attachments': attachments,
        'closing_details': closing_details,
        'status_options': status_options,
        'engineers': engineers,
        'is_amc_admin': True,  # Flag to show AMC admin specific options
    }
    
    return render(request, 'core/amc_admin_complaint_detail.html', context)


@amc_admin_required
def update_complaint_priority(request, complaint_id):
    """Update complaint priority via AJAX."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    new_priority = request.POST.get('priority')
    
    if new_priority not in ['low', 'medium', 'high', 'critical']:
        return JsonResponse({'success': False, 'error': 'Invalid priority level'})
    
    complaint.urgency = new_priority
    complaint.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Priority updated to {new_priority.title()}',
        'new_priority': new_priority,
        'new_priority_display': complaint.get_urgency_display()
    })


@amc_admin_required
def assign_engineer(request, complaint_id):
    """Assign engineer to complaint via AJAX."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    complaint = get_object_or_404(Complaint, id=complaint_id)
    engineer_id = request.POST.get('engineer_id')
    
    if engineer_id:
        try:
            engineer = User.objects.get(
                id=engineer_id,
                groups__name__in=['ENGINEER'],  # Only engineers
                is_active=True
            )
            complaint.assigned_to = engineer
            
            # Set status to "Assigned" when someone is assigned
            assigned_status = Status.objects.filter(name='Assigned', is_active=True).first()
            if assigned_status:
                complaint.status = assigned_status
                
            complaint.save()
            
            # Create a remark about the assignment
            from complaints.models import Remark
            Remark.objects.create(
                complaint=complaint,
                user=request.user,
                text=f"Complaint assigned to {engineer.get_full_name() or engineer.username} by {request.user.get_full_name() or request.user.username}",
                is_internal_note=True
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Assigned to {engineer.get_full_name() or engineer.username}',
                'engineer_name': engineer.get_full_name() or engineer.username,
                'status': complaint.status.name
            })
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Engineer not found'})
    else:
        # Unassign engineer
        complaint.assigned_to = None
        complaint.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Engineer unassigned',
            'engineer_name': 'Unassigned'
        })


@amc_admin_required
def download_complaints_report(request):
    """Download complaints report as CSV."""
    
    # Get filter parameters
    complaint_type = request.GET.get('type')
    status_filter = request.GET.get('status')
    engineer_filter = request.GET.get('engineer')
    department_filter = request.GET.get('department')
    include_closed = request.GET.get('include_closed', 'false') == 'true'
    
    # Base queryset
    complaints = Complaint.objects.select_related(
        'user', 'type', 'status', 'assigned_to', 'user__profile__department'
    )
    
    if not include_closed:
        complaints = complaints.filter(status__is_closed=False)
    
    # Apply filters
    if complaint_type:
        complaints = complaints.filter(type_id=complaint_type)
    if status_filter:
        complaints = complaints.filter(status_id=status_filter)
    if engineer_filter:
        if engineer_filter == 'unassigned':
            complaints = complaints.filter(assigned_to__isnull=True)
        else:
            complaints = complaints.filter(assigned_to_id=engineer_filter)
    if department_filter:
        complaints = complaints.filter(user__profile__department_id=department_filter)
    
    complaints = complaints.order_by('-created_at')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="complaints_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'Complaint ID',
        'Type',
        'Description',
        'User',
        'Department',
        'Priority',
        'Status',
        'Assigned Engineer',
        'Created Date',
        'Resolved Date',
        'Days Open/Closed'
    ])
    
    # Write data
    for complaint in complaints:
        writer.writerow([
            f'#{complaint.id}',
            complaint.type.name,
            complaint.description[:100] + '...' if len(complaint.description) > 100 else complaint.description,
            complaint.user.get_full_name() or complaint.user.username,
            complaint.user.profile.department.name if complaint.user.profile.department else 'N/A',
            complaint.get_urgency_display(),
            complaint.status.name,
            (complaint.assigned_to.get_full_name() or complaint.assigned_to.username) if complaint.assigned_to else 'Unassigned',
            complaint.created_at.strftime('%Y-%m-%d %H:%M'),
            complaint.resolved_at.strftime('%Y-%m-%d %H:%M') if complaint.resolved_at else 'N/A',
            complaint.days_open if not complaint.is_resolved else f'{complaint.days_open} (closed)'
        ])
    
    return response


@amc_admin_required
def bulk_actions(request):
    """Handle bulk actions on multiple complaints."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    complaint_ids = request.POST.getlist('complaint_ids[]')
    action = request.POST.get('action')
    
    if not complaint_ids:
        return JsonResponse({'success': False, 'error': 'No complaints selected'})
    
    complaints = Complaint.objects.filter(id__in=complaint_ids)
    
    if action == 'assign_engineer':
        engineer_id = request.POST.get('engineer_id')
        if engineer_id:
            try:
                engineer = User.objects.get(
                    id=engineer_id,
                    groups__name__in=['ENGINEER', 'AMC ADMIN', 'ADMIN'],
                    is_active=True
                )
                complaints.update(assigned_to=engineer)
                return JsonResponse({
                    'success': True,
                    'message': f'{complaints.count()} complaints assigned to {engineer.get_full_name() or engineer.username}'
                })
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Engineer not found'})
    
    elif action == 'update_priority':
        priority = request.POST.get('priority')
        if priority in ['low', 'medium', 'high', 'critical']:
            complaints.update(urgency=priority)
            return JsonResponse({
                'success': True,
                'message': f'{complaints.count()} complaints priority updated to {priority.title()}'
            })
    
    elif action == 'update_status':
        status_id = request.POST.get('status_id')
        try:
            status = Status.objects.get(id=status_id, is_active=True)
            complaints.update(status=status)
            return JsonResponse({
                'success': True,
                'message': f'{complaints.count()} complaints status updated to {status.name}'
            })
        except Status.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Status not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid action'})