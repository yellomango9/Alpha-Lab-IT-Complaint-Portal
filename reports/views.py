"""
Reports app views for generating and displaying complaint analytics.
Provides dashboard, report generation, and export functionality.
"""

import json
import csv
from datetime import datetime, timedelta
from io import StringIO, BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, TemplateView
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from django.core.paginator import Paginator

from complaints.models import Complaint, ComplaintMetrics, Status, ComplaintType
from core.models import Department, UserProfile
from feedback.models import Feedback
from .models import ReportTemplate, GeneratedReport
from .utils import ReportGenerator, ChartDataGenerator


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only admins and engineers can access certain views."""
    
    def test_func(self):
        return (
            self.request.user.is_authenticated and 
            (self.request.user.is_staff or 
             (hasattr(self.request.user, 'profile') and 
              (self.request.user.profile.is_admin or self.request.user.profile.is_engineer)))
        )


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard view showing key metrics and charts.
    Displays real-time complaint statistics and trends.
    """
    template_name = 'reports/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range (default to last 30 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Basic metrics
        context.update({
            'total_complaints': self.get_total_complaints(),
            'open_complaints': self.get_open_complaints(),
            'resolved_today': self.get_resolved_today(),
            'avg_resolution_time': self.get_avg_resolution_time(),
            'recent_complaints': self.get_recent_complaints(),
            'status_distribution': self.get_status_distribution(),
            'department_stats': self.get_department_stats(),
            'monthly_trends': self.get_monthly_trends(),
            'urgency_breakdown': self.get_urgency_breakdown(),
        })
        
        return context
    
    def get_total_complaints(self):
        """Get total number of complaints."""
        return Complaint.objects.count()
    
    def get_open_complaints(self):
        """Get number of open complaints."""
        return Complaint.objects.filter(status__is_closed=False).count()
    
    def get_resolved_today(self):
        """Get number of complaints resolved today."""
        today = timezone.now().date()
        return Complaint.objects.filter(
            resolved_at__date=today,
            status__is_closed=True
        ).count()
    
    def get_avg_resolution_time(self):
        """Get average resolution time in hours."""
        resolved_complaints = Complaint.objects.filter(
            status__is_closed=True,
            resolved_at__isnull=False
        )
        
        if not resolved_complaints.exists():
            return 0
        
        total_hours = 0
        count = 0
        
        for complaint in resolved_complaints:
            if complaint.resolved_at and complaint.created_at:
                hours = (complaint.resolved_at - complaint.created_at).total_seconds() / 3600
                total_hours += hours
                count += 1
        
        return round(total_hours / count, 1) if count > 0 else 0
    
    def get_recent_complaints(self):
        """Get recent complaints for the user."""
        user = self.request.user
        queryset = Complaint.objects.select_related('user', 'type', 'status')
        
        # Filter based on user role
        if hasattr(user, 'profile') and user.profile.is_engineer:
            # Engineers see all recent complaints
            queryset = queryset.all()
        else:
            # Regular users see only their complaints
            queryset = queryset.filter(user=user)
        
        return queryset.order_by('-created_at')[:10]
    
    def get_status_distribution(self):
        """Get complaint distribution by status."""
        return list(
            Status.objects.annotate(
                count=Count('complaint')
            ).values('name', 'count')
        )
    
    def get_department_stats(self):
        """Get complaint statistics by department."""
        return list(
            Department.objects.annotate(
                total_complaints=Count('userprofile__user__complaints'),
                resolved_complaints=Count(
                    'userprofile__user__complaints',
                    filter=Q(userprofile__user__complaints__status__is_closed=True)
                )
            ).values('name', 'total_complaints', 'resolved_complaints')
        )
    
    def get_monthly_trends(self):
        """Get monthly complaint trends for the last 12 months."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        
        # Get monthly metrics
        monthly_data = []
        current_date = start_date.replace(day=1)
        
        while current_date <= end_date:
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            
            month_complaints = Complaint.objects.filter(
                created_at__date__gte=current_date,
                created_at__date__lt=next_month
            ).count()
            
            month_resolved = Complaint.objects.filter(
                resolved_at__date__gte=current_date,
                resolved_at__date__lt=next_month,
                status__is_closed=True
            ).count()
            
            monthly_data.append({
                'month': current_date.strftime('%Y-%m'),
                'month_name': current_date.strftime('%B %Y'),
                'complaints': month_complaints,
                'resolved': month_resolved
            })
            
            current_date = next_month
        
        return monthly_data
    
    def get_urgency_breakdown(self):
        """Get complaint breakdown by urgency."""
        urgency_stats = []
        for urgency_code, urgency_name in Complaint.URGENCY_CHOICES:
            count = Complaint.objects.filter(urgency=urgency_code).count()
            urgency_stats.append({
                'urgency': urgency_name,
                'count': count
            })
        return urgency_stats


class ReportsListView(AdminRequiredMixin, ListView):
    """
    List view for generated reports.
    Shows all available reports with filtering and pagination.
    """
    model = GeneratedReport
    template_name = 'reports/list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = GeneratedReport.objects.select_related('template', 'generated_by')
        
        # Apply filters
        template_filter = self.request.GET.get('template')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if template_filter:
            queryset = queryset.filter(template_id=template_filter)
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(date_from__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(date_to__lte=date_to)
            except ValueError:
                pass
        
        return queryset.order_by('-generated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = ReportTemplate.objects.filter(is_active=True)
        context['current_filters'] = {
            'template': self.request.GET.get('template', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        }
        return context


@login_required
def generate_report(request):
    """
    Generate a new report based on user parameters.
    Supports different report types and export formats.
    """
    if not (request.user.is_staff or 
            (hasattr(request.user, 'profile') and 
             (request.user.profile.is_admin or request.user.profile.is_engineer))):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        try:
            # Get parameters from request
            report_type = request.POST.get('report_type', 'daily')
            date_from = datetime.strptime(request.POST.get('date_from'), '%Y-%m-%d').date()
            date_to = datetime.strptime(request.POST.get('date_to'), '%Y-%m-%d').date()
            export_format = request.POST.get('export_format', 'json')
            
            # Generate report
            generator = ReportGenerator()
            report_data = generator.generate_report(
                report_type=report_type,
                date_from=date_from,
                date_to=date_to,
                filters=request.POST.dict()
            )
            
            # Handle different export formats
            if export_format == 'csv':
                return export_csv_report(report_data, f"{report_type}_report_{date_from}_{date_to}")
            elif export_format == 'json':
                response = JsonResponse(report_data)
                response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{date_from}_{date_to}.json"'
                return response
            else:
                # Return JSON for AJAX requests
                return JsonResponse(report_data)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    # GET request - show report generation form
    context = {
        'report_types': ReportTemplate.REPORT_TYPES,
        'departments': Department.objects.filter(is_active=True),
        'complaint_types': ComplaintType.objects.filter(is_active=True),
        'statuses': Status.objects.filter(is_active=True),
    }
    
    return render(request, 'reports/generate.html', context)


def export_csv_report(report_data, filename):
    """
    Export report data as CSV file.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    writer = csv.writer(response)
    
    # Write summary data
    if 'summary' in report_data:
        writer.writerow(['Summary'])
        for key, value in report_data['summary'].items():
            writer.writerow([key.replace('_', ' ').title(), value])
        writer.writerow([])  # Empty row
    
    # Write complaint details if available
    if 'complaints' in report_data:
        writer.writerow(['Complaint Details'])
        writer.writerow([
            'ID', 'Title', 'User', 'Department', 'Type', 'Status', 
            'Urgency', 'Created', 'Resolved', 'Resolution Time (hours)'
        ])
        
        for complaint in report_data['complaints']:
            writer.writerow([
                complaint.get('id', ''),
                complaint.get('title', ''),
                complaint.get('user', ''),
                complaint.get('department', ''),
                complaint.get('type', ''),
                complaint.get('status', ''),
                complaint.get('urgency', ''),
                complaint.get('created_at', ''),
                complaint.get('resolved_at', ''),
                complaint.get('resolution_time_hours', ''),
            ])
    
    return response


@login_required
def chart_data_api(request):
    """
    API endpoint for chart data.
    Returns JSON data for various dashboard charts.
    """
    chart_type = request.GET.get('type', 'status_distribution')
    
    generator = ChartDataGenerator()
    
    try:
        if chart_type == 'status_distribution':
            data = generator.get_status_distribution()
        elif chart_type == 'monthly_trends':
            data = generator.get_monthly_trends()
        elif chart_type == 'department_stats':
            data = generator.get_department_stats()
        elif chart_type == 'urgency_breakdown':
            data = generator.get_urgency_breakdown()
        elif chart_type == 'resolution_times':
            data = generator.get_resolution_times()
        else:
            data = {'error': 'Invalid chart type'}
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


class ReportDetailView(AdminRequiredMixin, DetailView):
    """
    Detail view for individual generated reports.
    Shows report data and provides download links.
    """
    model = GeneratedReport
    template_name = 'reports/detail.html'
    context_object_name = 'report'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Parse report data for display
        report_data = self.object.data
        context['report_summary'] = report_data.get('summary', {})
        context['report_charts'] = report_data.get('charts', {})
        
        return context