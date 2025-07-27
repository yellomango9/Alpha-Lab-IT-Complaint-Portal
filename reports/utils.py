"""
Utility classes for report generation and data processing.
Provides functionality for creating various types of reports and charts.
"""

from datetime import datetime, timedelta
from django.db.models import Count, Avg, Q, F
from django.utils import timezone

from complaints.models import Complaint, Status, ComplaintType
from core.models import Department
from feedback.models import Feedback


class ReportGenerator:
    """
    Main class for generating different types of reports.
    Handles data aggregation and formatting for various report types.
    """
    
    def generate_report(self, report_type, date_from, date_to, filters=None):
        """
        Generate a report based on the specified type and parameters.
        
        Args:
            report_type (str): Type of report to generate
            date_from (date): Start date for the report
            date_to (date): End date for the report
            filters (dict): Additional filters to apply
            
        Returns:
            dict: Report data with summary, details, and charts
        """
        if filters is None:
            filters = {}
        
        # Base queryset
        queryset = Complaint.objects.filter(
            created_at__date__gte=date_from,
            created_at__date__lte=date_to
        ).select_related('user', 'type', 'status', 'assigned_to', 'user__profile__department')
        
        # Apply additional filters
        queryset = self._apply_filters(queryset, filters)
        
        # Generate report based on type
        if report_type == 'daily':
            return self._generate_daily_report(queryset, date_from, date_to)
        elif report_type == 'weekly':
            return self._generate_weekly_report(queryset, date_from, date_to)
        elif report_type == 'monthly':
            return self._generate_monthly_report(queryset, date_from, date_to)
        elif report_type == 'department':
            return self._generate_department_report(queryset, date_from, date_to)
        elif report_type == 'performance':
            return self._generate_performance_report(queryset, date_from, date_to)
        else:
            return self._generate_custom_report(queryset, date_from, date_to)
    
    def _apply_filters(self, queryset, filters):
        """Apply additional filters to the queryset."""
        if filters.get('department'):
            queryset = queryset.filter(user__profile__department_id=filters['department'])
        
        if filters.get('complaint_type'):
            queryset = queryset.filter(type_id=filters['complaint_type'])
        
        if filters.get('status'):
            queryset = queryset.filter(status_id=filters['status'])
        
        if filters.get('urgency'):
            queryset = queryset.filter(urgency=filters['urgency'])
        
        if filters.get('assigned_to'):
            queryset = queryset.filter(assigned_to_id=filters['assigned_to'])
        
        return queryset
    
    def _generate_daily_report(self, queryset, date_from, date_to):
        """Generate a daily report with day-by-day breakdown."""
        report_data = {
            'type': 'daily',
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'summary': self._get_summary_stats(queryset),
            'daily_breakdown': [],
            'charts': {}
        }
        
        # Generate daily breakdown
        current_date = date_from
        while current_date <= date_to:
            day_complaints = queryset.filter(created_at__date=current_date)
            day_resolved = queryset.filter(
                resolved_at__date=current_date,
                status__is_closed=True
            )
            
            report_data['daily_breakdown'].append({
                'date': current_date.isoformat(),
                'new_complaints': day_complaints.count(),
                'resolved_complaints': day_resolved.count(),
                'total_open': queryset.filter(
                    created_at__date__lte=current_date,
                    status__is_closed=False
                ).count()
            })
            
            current_date += timedelta(days=1)
        
        # Add chart data
        report_data['charts'] = {
            'daily_trends': report_data['daily_breakdown'],
            'status_distribution': self._get_status_distribution(queryset),
            'type_breakdown': self._get_type_breakdown(queryset)
        }
        
        return report_data
    
    def _generate_weekly_report(self, queryset, date_from, date_to):
        """Generate a weekly report with week-by-week breakdown."""
        report_data = {
            'type': 'weekly',
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'summary': self._get_summary_stats(queryset),
            'weekly_breakdown': [],
            'charts': {}
        }
        
        # Generate weekly breakdown
        current_date = date_from
        week_number = 1
        
        while current_date <= date_to:
            week_end = min(current_date + timedelta(days=6), date_to)
            week_complaints = queryset.filter(
                created_at__date__gte=current_date,
                created_at__date__lte=week_end
            )
            week_resolved = queryset.filter(
                resolved_at__date__gte=current_date,
                resolved_at__date__lte=week_end,
                status__is_closed=True
            )
            
            report_data['weekly_breakdown'].append({
                'week': week_number,
                'date_from': current_date.isoformat(),
                'date_to': week_end.isoformat(),
                'new_complaints': week_complaints.count(),
                'resolved_complaints': week_resolved.count(),
                'avg_resolution_time': self._calculate_avg_resolution_time(week_resolved)
            })
            
            current_date = week_end + timedelta(days=1)
            week_number += 1
        
        # Add chart data
        report_data['charts'] = {
            'weekly_trends': report_data['weekly_breakdown'],
            'department_stats': self._get_department_stats(queryset),
            'urgency_breakdown': self._get_urgency_breakdown(queryset)
        }
        
        return report_data
    
    def _generate_monthly_report(self, queryset, date_from, date_to):
        """Generate a monthly report with comprehensive statistics."""
        report_data = {
            'type': 'monthly',
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'summary': self._get_summary_stats(queryset),
            'monthly_breakdown': [],
            'performance_metrics': {},
            'charts': {}
        }
        
        # Generate monthly breakdown
        current_date = date_from.replace(day=1)
        
        while current_date <= date_to:
            # Calculate end of month
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1)
            else:
                next_month = current_date.replace(month=current_date.month + 1)
            
            month_end = min((next_month - timedelta(days=1)), date_to)
            
            month_complaints = queryset.filter(
                created_at__date__gte=current_date,
                created_at__date__lte=month_end
            )
            month_resolved = queryset.filter(
                resolved_at__date__gte=current_date,
                resolved_at__date__lte=month_end,
                status__is_closed=True
            )
            
            report_data['monthly_breakdown'].append({
                'month': current_date.strftime('%Y-%m'),
                'month_name': current_date.strftime('%B %Y'),
                'new_complaints': month_complaints.count(),
                'resolved_complaints': month_resolved.count(),
                'resolution_rate': self._calculate_resolution_rate(month_complaints, month_resolved),
                'avg_resolution_time': self._calculate_avg_resolution_time(month_resolved)
            })
            
            current_date = next_month
        
        # Performance metrics
        report_data['performance_metrics'] = {
            'overall_resolution_rate': self._calculate_resolution_rate(
                queryset, 
                queryset.filter(status__is_closed=True)
            ),
            'avg_resolution_time_hours': self._calculate_avg_resolution_time(
                queryset.filter(status__is_closed=True)
            ),
            'customer_satisfaction': self._get_customer_satisfaction(queryset),
            'top_complaint_types': self._get_top_complaint_types(queryset),
            'busiest_departments': self._get_busiest_departments(queryset)
        }
        
        # Add comprehensive chart data
        report_data['charts'] = {
            'monthly_trends': report_data['monthly_breakdown'],
            'status_distribution': self._get_status_distribution(queryset),
            'department_comparison': self._get_department_stats(queryset),
            'type_analysis': self._get_type_breakdown(queryset),
            'urgency_analysis': self._get_urgency_breakdown(queryset),
            'resolution_time_trends': self._get_resolution_time_trends(queryset)
        }
        
        return report_data
    
    def _generate_department_report(self, queryset, date_from, date_to):
        """Generate a department-focused report."""
        report_data = {
            'type': 'department',
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'summary': self._get_summary_stats(queryset),
            'department_analysis': [],
            'charts': {}
        }
        
        # Analyze each department
        departments = Department.objects.filter(is_active=True)
        
        for dept in departments:
            dept_complaints = queryset.filter(user__profile__department=dept)
            dept_resolved = dept_complaints.filter(status__is_closed=True)
            
            if dept_complaints.exists():
                report_data['department_analysis'].append({
                    'department': dept.name,
                    'total_complaints': dept_complaints.count(),
                    'resolved_complaints': dept_resolved.count(),
                    'resolution_rate': self._calculate_resolution_rate(dept_complaints, dept_resolved),
                    'avg_resolution_time': self._calculate_avg_resolution_time(dept_resolved),
                    'top_complaint_types': self._get_top_complaint_types(dept_complaints, limit=3),
                    'urgency_breakdown': self._get_urgency_breakdown(dept_complaints)
                })
        
        # Sort by total complaints
        report_data['department_analysis'].sort(
            key=lambda x: x['total_complaints'], 
            reverse=True
        )
        
        # Add chart data
        report_data['charts'] = {
            'department_comparison': report_data['department_analysis'],
            'department_resolution_rates': [
                {
                    'department': dept['department'],
                    'resolution_rate': dept['resolution_rate']
                }
                for dept in report_data['department_analysis']
            ]
        }
        
        return report_data
    
    def _generate_performance_report(self, queryset, date_from, date_to):
        """Generate a performance-focused report."""
        report_data = {
            'type': 'performance',
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'summary': self._get_summary_stats(queryset),
            'performance_metrics': {},
            'engineer_performance': [],
            'charts': {}
        }
        
        # Overall performance metrics
        resolved_complaints = queryset.filter(status__is_closed=True)
        
        report_data['performance_metrics'] = {
            'total_complaints': queryset.count(),
            'resolved_complaints': resolved_complaints.count(),
            'resolution_rate': self._calculate_resolution_rate(queryset, resolved_complaints),
            'avg_resolution_time_hours': self._calculate_avg_resolution_time(resolved_complaints),
            'customer_satisfaction_avg': self._get_customer_satisfaction(queryset),
            'sla_compliance': self._calculate_sla_compliance(resolved_complaints),
            'first_response_time': self._calculate_first_response_time(queryset)
        }
        
        # Engineer performance analysis
        engineers = queryset.filter(assigned_to__isnull=False).values_list(
            'assigned_to', flat=True
        ).distinct()
        
        for engineer_id in engineers:
            engineer_complaints = queryset.filter(assigned_to_id=engineer_id)
            engineer_resolved = engineer_complaints.filter(status__is_closed=True)
            
            if engineer_complaints.exists():
                engineer = engineer_complaints.first().assigned_to
                report_data['engineer_performance'].append({
                    'engineer_name': engineer.get_full_name() or engineer.username,
                    'total_assigned': engineer_complaints.count(),
                    'resolved': engineer_resolved.count(),
                    'resolution_rate': self._calculate_resolution_rate(
                        engineer_complaints, engineer_resolved
                    ),
                    'avg_resolution_time': self._calculate_avg_resolution_time(engineer_resolved),
                    'customer_satisfaction': self._get_customer_satisfaction(engineer_complaints)
                })
        
        # Sort by resolution rate
        report_data['engineer_performance'].sort(
            key=lambda x: x['resolution_rate'], 
            reverse=True
        )
        
        # Add chart data
        report_data['charts'] = {
            'resolution_trends': self._get_resolution_time_trends(queryset),
            'engineer_comparison': report_data['engineer_performance'],
            'sla_compliance_trends': self._get_sla_compliance_trends(queryset)
        }
        
        return report_data
    
    def _generate_custom_report(self, queryset, date_from, date_to):
        """Generate a custom report with all available data."""
        return {
            'type': 'custom',
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'summary': self._get_summary_stats(queryset),
            'complaints': self._get_complaint_details(queryset),
            'charts': {
                'status_distribution': self._get_status_distribution(queryset),
                'type_breakdown': self._get_type_breakdown(queryset),
                'department_stats': self._get_department_stats(queryset),
                'urgency_breakdown': self._get_urgency_breakdown(queryset)
            }
        }
    
    # Helper methods for calculations
    
    def _get_summary_stats(self, queryset):
        """Get basic summary statistics."""
        resolved_queryset = queryset.filter(status__is_closed=True)
        
        return {
            'total_complaints': queryset.count(),
            'resolved_complaints': resolved_queryset.count(),
            'open_complaints': queryset.filter(status__is_closed=False).count(),
            'resolution_rate': self._calculate_resolution_rate(queryset, resolved_queryset),
            'avg_resolution_time_hours': self._calculate_avg_resolution_time(resolved_queryset)
        }
    
    def _calculate_resolution_rate(self, total_queryset, resolved_queryset):
        """Calculate resolution rate as percentage."""
        total = total_queryset.count()
        resolved = resolved_queryset.count()
        return round((resolved / total * 100), 2) if total > 0 else 0
    
    def _calculate_avg_resolution_time(self, resolved_queryset):
        """Calculate average resolution time in hours."""
        total_hours = 0
        count = 0
        
        for complaint in resolved_queryset:
            if complaint.resolved_at and complaint.created_at:
                hours = (complaint.resolved_at - complaint.created_at).total_seconds() / 3600
                total_hours += hours
                count += 1
        
        return round(total_hours / count, 2) if count > 0 else 0
    
    def _get_status_distribution(self, queryset):
        """Get complaint distribution by status."""
        return list(
            queryset.values('status__name').annotate(
                count=Count('id')
            ).values_list('status__name', 'count')
        )
    
    def _get_type_breakdown(self, queryset):
        """Get complaint breakdown by type."""
        return list(
            queryset.values('type__name').annotate(
                count=Count('id')
            ).values_list('type__name', 'count')
        )
    
    def _get_department_stats(self, queryset):
        """Get complaint statistics by department."""
        return list(
            queryset.values('user__profile__department__name').annotate(
                count=Count('id')
            ).values_list('user__profile__department__name', 'count')
        )
    
    def _get_urgency_breakdown(self, queryset):
        """Get complaint breakdown by urgency."""
        return list(
            queryset.values('urgency').annotate(
                count=Count('id')
            ).values_list('urgency', 'count')
        )
    
    def _get_customer_satisfaction(self, queryset):
        """Get average customer satisfaction rating."""
        feedback_queryset = Feedback.objects.filter(complaint__in=queryset)
        if feedback_queryset.exists():
            return round(feedback_queryset.aggregate(Avg('rating'))['rating__avg'], 2)
        return None
    
    def _get_top_complaint_types(self, queryset, limit=5):
        """Get top complaint types by count."""
        return list(
            queryset.values('type__name').annotate(
                count=Count('id')
            ).order_by('-count')[:limit].values_list('type__name', 'count')
        )
    
    def _get_busiest_departments(self, queryset, limit=5):
        """Get departments with most complaints."""
        return list(
            queryset.values('user__profile__department__name').annotate(
                count=Count('id')
            ).order_by('-count')[:limit].values_list('user__profile__department__name', 'count')
        )
    
    def _get_complaint_details(self, queryset):
        """Get detailed complaint information for export."""
        complaints = []
        for complaint in queryset:
            complaints.append({
                'id': complaint.id,
                'title': complaint.title,
                'user': complaint.user.get_full_name() or complaint.user.username,
                'department': complaint.user.profile.department.name if (
                    complaint.user.profile and complaint.user.profile.department
                ) else 'Unknown',
                'type': complaint.type.name if complaint.type else 'Unknown',
                'status': complaint.status.name if complaint.status else 'Unknown',
                'urgency': complaint.get_urgency_display(),
                'created_at': complaint.created_at.isoformat(),
                'resolved_at': complaint.resolved_at.isoformat() if complaint.resolved_at else None,
                'resolution_time_hours': self._calculate_single_resolution_time(complaint)
            })
        return complaints
    
    def _calculate_single_resolution_time(self, complaint):
        """Calculate resolution time for a single complaint."""
        if complaint.resolved_at and complaint.created_at:
            return round(
                (complaint.resolved_at - complaint.created_at).total_seconds() / 3600, 2
            )
        return None
    
    def _calculate_sla_compliance(self, resolved_queryset):
        """Calculate SLA compliance rate (assuming 24-hour SLA)."""
        sla_hours = 24
        compliant_count = 0
        total_count = 0
        
        for complaint in resolved_queryset:
            if complaint.resolved_at and complaint.created_at:
                resolution_hours = (complaint.resolved_at - complaint.created_at).total_seconds() / 3600
                if resolution_hours <= sla_hours:
                    compliant_count += 1
                total_count += 1
        
        return round((compliant_count / total_count * 100), 2) if total_count > 0 else 0
    
    def _calculate_first_response_time(self, queryset):
        """Calculate average first response time (placeholder - would need status history)."""
        # This would require status history to calculate properly
        return 0
    
    def _get_resolution_time_trends(self, queryset):
        """Get resolution time trends over the period."""
        # Simplified implementation - would be enhanced with more detailed analysis
        return []
    
    def _get_sla_compliance_trends(self, queryset):
        """Get SLA compliance trends over the period."""
        # Simplified implementation - would be enhanced with more detailed analysis
        return []


class ChartDataGenerator:
    """
    Utility class for generating chart data for the dashboard.
    Provides formatted data for various chart types.
    """
    
    def get_status_distribution(self):
        """Get data for status distribution pie chart."""
        data = list(
            Status.objects.annotate(
                count=Count('complaint')
            ).values('name', 'count')
        )
        
        return {
            'labels': [item['name'] for item in data],
            'data': [item['count'] for item in data],
            'type': 'pie'
        }
    
    def get_monthly_trends(self, months=12):
        """Get data for monthly trends line chart."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30 * months)
        
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
                'month': current_date.strftime('%b %Y'),
                'complaints': month_complaints,
                'resolved': month_resolved
            })
            
            current_date = next_month
        
        return {
            'labels': [item['month'] for item in monthly_data],
            'datasets': [
                {
                    'label': 'New Complaints',
                    'data': [item['complaints'] for item in monthly_data],
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)'
                },
                {
                    'label': 'Resolved',
                    'data': [item['resolved'] for item in monthly_data],
                    'borderColor': 'rgb(54, 162, 235)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)'
                }
            ],
            'type': 'line'
        }
    
    def get_department_stats(self):
        """Get data for department statistics bar chart."""
        data = list(
            Department.objects.annotate(
                total_complaints=Count('userprofile__user__complaints'),
                resolved_complaints=Count(
                    'userprofile__user__complaints',
                    filter=Q(userprofile__user__complaints__status__is_closed=True)
                )
            ).values('name', 'total_complaints', 'resolved_complaints')
        )
        
        return {
            'labels': [item['name'] for item in data],
            'datasets': [
                {
                    'label': 'Total Complaints',
                    'data': [item['total_complaints'] for item in data],
                    'backgroundColor': 'rgba(255, 99, 132, 0.5)'
                },
                {
                    'label': 'Resolved',
                    'data': [item['resolved_complaints'] for item in data],
                    'backgroundColor': 'rgba(54, 162, 235, 0.5)'
                }
            ],
            'type': 'bar'
        }
    
    def get_urgency_breakdown(self):
        """Get data for urgency breakdown doughnut chart."""
        urgency_stats = []
        for urgency_code, urgency_name in Complaint.URGENCY_CHOICES:
            count = Complaint.objects.filter(urgency=urgency_code).count()
            urgency_stats.append({
                'urgency': urgency_name,
                'count': count
            })
        
        return {
            'labels': [item['urgency'] for item in urgency_stats],
            'data': [item['count'] for item in urgency_stats],
            'backgroundColor': [
                'rgba(255, 99, 132, 0.8)',
                'rgba(54, 162, 235, 0.8)',
                'rgba(255, 205, 86, 0.8)',
                'rgba(75, 192, 192, 0.8)'
            ],
            'type': 'doughnut'
        }
    
    def get_resolution_times(self):
        """Get data for resolution time analysis."""
        # This would be enhanced with more detailed resolution time analysis
        return {
            'labels': ['< 1 hour', '1-4 hours', '4-24 hours', '> 24 hours'],
            'data': [10, 25, 40, 15],  # Placeholder data
            'type': 'bar'
        }