"""
Admin-specific views for the Alpha Lab IT Complaint Portal.
"""
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone

from .models import UserProfile, Department
from complaints.models import Complaint, Status, ComplaintType


def admin_required(view_func):
    """Decorator to check if user is admin."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user is admin
        if not (request.user.groups.filter(name__in=['Admin', 'ADMIN']).exists() or 
                request.user.is_superuser):
            messages.error(request, 'Access denied. You need admin privileges.')
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):
    """Admin dashboard with comprehensive analytics and charts."""
    
    # Get date ranges
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    fourteen_days_ago = timezone.now() - timedelta(days=14)
    
    # Basic statistics
    total_complaints = Complaint.objects.count()
    open_complaints = Complaint.objects.filter(status__is_closed=False).count()
    resolved_complaints = Complaint.objects.filter(status__is_closed=True).count()
    unassigned_complaints = Complaint.objects.filter(assigned_to__isnull=True, status__is_closed=False).count()
    
    # Issues (complaints older than 14 days and not closed)
    issues = Complaint.objects.filter(
        status__is_closed=False,
        created_at__lt=fourteen_days_ago
    ).select_related('user', 'type', 'status', 'assigned_to').order_by('created_at')
    
    # Recent activity (last 7 days)
    recent_complaints = Complaint.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    # Complaints by status
    status_data = Status.objects.annotate(
        complaint_count=Count('complaint')
    ).order_by('order')
    
    # Complaints by type
    type_data = ComplaintType.objects.annotate(
        complaint_count=Count('complaint')
    ).filter(complaint_count__gt=0).order_by('-complaint_count')
    
    # Complaints by urgency
    urgency_data = Complaint.objects.values('urgency').annotate(
        count=Count('id')
    ).order_by('urgency')
    
    # Engineer workload
    engineer_workload = User.objects.filter(
        groups__name__in=['Engineer', 'ENGINEER'],
        is_active=True
    ).annotate(
        active_complaints=Count('assigned_complaints', filter=Q(assigned_complaints__status__is_closed=False)),
        resolved_count=Count('assigned_complaints', filter=Q(assigned_complaints__status__is_closed=True))
    ).order_by('-active_complaints')
    
    # Monthly trend (last 12 months)
    monthly_data = []
    for i in range(12):
        month_start = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        
        month_complaints = Complaint.objects.filter(
            created_at__gte=month_start,
            created_at__lt=next_month
        ).count()
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'complaints': month_complaints
        })
    
    monthly_data.reverse()  # Show chronologically
    
    # Department-wise statistics
    department_data = Department.objects.annotate(
        complaint_count=Count('userprofile__user__complaints')
    ).filter(complaint_count__gt=0).order_by('-complaint_count')
    
    # Response time analysis
    resolved_with_time = Complaint.objects.filter(
        status__is_closed=True,
        resolved_at__isnull=False
    )
    
    avg_resolution_days = 0
    if resolved_with_time.exists():
        total_days = sum([
            (complaint.resolved_at.date() - complaint.created_at.date()).days 
            for complaint in resolved_with_time
        ])
        avg_resolution_days = total_days / resolved_with_time.count()
    
    context = {
        # Basic stats
        'total_complaints': total_complaints,
        'open_complaints': open_complaints,
        'resolved_complaints': resolved_complaints,
        'unassigned_complaints': unassigned_complaints,
        'recent_complaints': recent_complaints,
        'issues_count': issues.count(),
        'avg_resolution_days': round(avg_resolution_days, 1),
        
        # Issues (complaints older than 14 days)
        'issues': issues,
        
        # Chart data
        'status_data': status_data,
        'type_data': type_data,
        'urgency_data': urgency_data,
        'engineer_workload': engineer_workload,
        'monthly_data': monthly_data,
        'department_data': department_data,
        
        # Date filters
        'today': today,
        'last_7_days': last_7_days,
        'last_30_days': last_30_days,
    }
    
    return render(request, 'core/admin_dashboard.html', context)


@admin_required
def get_chart_data(request):
    """AJAX endpoint to provide chart data."""
    chart_type = request.GET.get('type', 'status')
    
    if chart_type == 'status':
        data = list(Status.objects.annotate(
            complaint_count=Count('complaint')
        ).values('name', 'complaint_count'))
        
    elif chart_type == 'type':
        data = list(ComplaintType.objects.annotate(
            complaint_count=Count('complaint')
        ).filter(complaint_count__gt=0).values('name', 'complaint_count'))
        
    elif chart_type == 'urgency':
        data = list(Complaint.objects.values('urgency').annotate(
            complaint_count=Count('id')
        ).values('urgency', 'complaint_count'))
        
    elif chart_type == 'monthly':
        # Monthly trend for last 12 months
        today = timezone.now().date()
        monthly_data = []
        
        for i in range(12):
            month_start = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            
            month_complaints = Complaint.objects.filter(
                created_at__gte=month_start,
                created_at__lt=next_month
            ).count()
            
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'complaints': month_complaints
            })
        
        monthly_data.reverse()
        data = monthly_data
        
    elif chart_type == 'department':
        data = list(Department.objects.annotate(
            complaint_count=Count('userprofile__user__complaints')
        ).filter(complaint_count__gt=0).values('name', 'complaint_count'))
    
    else:
        data = []
    
    return JsonResponse({'data': data})


@admin_required
def system_health(request):
    """System health and metrics endpoint."""
    
    # Calculate various health metrics
    fourteen_days_ago = timezone.now() - timedelta(days=14)
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    # Issues
    critical_issues = Complaint.objects.filter(
        status__is_closed=False,
        created_at__lt=fourteen_days_ago
    ).count()
    
    # Recent activity
    recent_activity = Complaint.objects.filter(
        created_at__gte=seven_days_ago
    ).count()
    
    # Engineer availability
    total_engineers = User.objects.filter(
        groups__name__in=['Engineer', 'ENGINEER'],
        is_active=True
    ).count()
    
    overloaded_engineers = User.objects.filter(
        groups__name__in=['Engineer', 'ENGINEER'],
        is_active=True,
        assigned_complaints__status__is_closed=False
    ).annotate(
        workload=Count('assigned_complaints')
    ).filter(workload__gt=10).count()
    
    # System health score (0-100)
    health_score = 100
    if critical_issues > 0:
        health_score -= min(critical_issues * 5, 30)  # Max -30 for issues
    if overloaded_engineers > 0:
        health_score -= min(overloaded_engineers * 10, 25)  # Max -25 for overload
    if recent_activity == 0:
        health_score -= 15  # -15 for no recent activity
    
    health_score = max(health_score, 0)  # Don't go below 0
    
    # Health status
    if health_score >= 80:
        health_status = 'Excellent'
        health_color = 'success'
    elif health_score >= 60:
        health_status = 'Good' 
        health_color = 'info'
    elif health_score >= 40:
        health_status = 'Fair'
        health_color = 'warning'
    else:
        health_status = 'Poor'
        health_color = 'danger'
    
    return JsonResponse({
        'health_score': health_score,
        'health_status': health_status,
        'health_color': health_color,
        'critical_issues': critical_issues,
        'recent_activity': recent_activity,
        'total_engineers': total_engineers,
        'overloaded_engineers': overloaded_engineers,
    })