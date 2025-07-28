"""
Management command to generate complaint statistics and reports.
Usage: python manage.py generate_report [--format html|json] [--output filename]
"""

import json
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Count, Avg, Q
from complaints.models import Complaint, Status, ComplaintType
from feedback.models import Feedback


class Command(BaseCommand):
    help = 'Generate complaint statistics and reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['html', 'json'],
            default='html',
            help='Output format (html or json)'
        )
        
        parser.add_argument(
            '--output',
            type=str,
            help='Output filename (optional)'
        )
        
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to include in the report (default: 30)'
        )

    def handle(self, *args, **options):
        try:
            # Calculate date range
            end_date = timezone.now()
            start_date = end_date - timedelta(days=options['days'])
            
            # Generate statistics
            stats = self.generate_statistics(start_date, end_date)
            
            # Output based on format
            if options['format'] == 'json':
                self.output_json(stats, options.get('output'))
            else:
                self.output_html(stats, options.get('output'))
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating report: {str(e)}')
            )

    def generate_statistics(self, start_date, end_date):
        """Generate comprehensive statistics."""
        
        # Basic counts
        total_complaints = Complaint.objects.count()
        period_complaints = Complaint.objects.filter(
            created_at__range=[start_date, end_date]
        ).count()
        
        # Status distribution
        status_distribution = list(
            Complaint.objects.values('status__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Type distribution
        type_distribution = list(
            Complaint.objects.values('type__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Urgency distribution
        urgency_distribution = list(
            Complaint.objects.values('urgency')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Resolution statistics
        resolved_complaints = Complaint.objects.filter(
            status__is_closed=True,
            resolved_at__isnull=False
        )
        
        avg_resolution_time = None
        if resolved_complaints.exists():
            # Calculate average resolution time in hours
            resolution_times = []
            for complaint in resolved_complaints:
                if complaint.resolved_at and complaint.created_at:
                    delta = complaint.resolved_at - complaint.created_at
                    resolution_times.append(delta.total_seconds() / 3600)  # Convert to hours
            
            if resolution_times:
                avg_resolution_time = sum(resolution_times) / len(resolution_times)
        
        # Top assignees
        top_assignees = list(
            Complaint.objects.filter(assigned_to__isnull=False)
            .values('assigned_to__first_name', 'assigned_to__last_name', 'assigned_to__username')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        # Recent activity
        recent_complaints = list(
            Complaint.objects.select_related('user', 'type', 'status')
            .order_by('-created_at')[:10]
            .values(
                'id', 'title', 'user__username', 'type__name', 
                'status__name', 'created_at', 'urgency'
            )
        )
        
        # Feedback statistics
        feedback_stats = {
            'total_feedback': Feedback.objects.count(),
            'avg_rating': Feedback.objects.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0,
            'rating_distribution': list(
                Feedback.objects.values('rating')
                .annotate(count=Count('id'))
                .order_by('rating')
            )
        }
        
        return {
            'generated_at': timezone.now().isoformat(),
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days
            },
            'summary': {
                'total_complaints': total_complaints,
                'period_complaints': period_complaints,
                'resolved_complaints': resolved_complaints.count(),
                'avg_resolution_time_hours': round(avg_resolution_time, 2) if avg_resolution_time else None
            },
            'distributions': {
                'status': status_distribution,
                'type': type_distribution,
                'urgency': urgency_distribution
            },
            'top_assignees': top_assignees,
            'recent_complaints': recent_complaints,
            'feedback': feedback_stats
        }

    def output_json(self, stats, filename=None):
        """Output statistics as JSON."""
        if not filename:
            filename = f'complaint_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # Convert datetime objects to strings for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, default=json_serializer, ensure_ascii=False)
        
        self.stdout.write(
            self.style.SUCCESS(f'JSON report generated: {filename}')
        )

    def output_html(self, stats, filename=None):
        """Output statistics as HTML."""
        if not filename:
            filename = f'complaint_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.html'
        
        # Create HTML report template content
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AMC Complaint Portal - Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #007bff; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AMC Complaint Portal - Report</h1>
        <p>Generated on: {stats['generated_at']}</p>
        <p>Period: {stats['period']['start_date']} to {stats['period']['end_date']} ({stats['period']['days']} days)</p>
    </div>
    
    <div class="section">
        <h2>Summary Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats['summary']['total_complaints']}</div>
                <div>Total Complaints</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['summary']['period_complaints']}</div>
                <div>Period Complaints</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['summary']['resolved_complaints']}</div>
                <div>Resolved Complaints</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['summary']['avg_resolution_time_hours'] or 'N/A'}</div>
                <div>Avg Resolution Time (hours)</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Status Distribution</h2>
        <table>
            <tr><th>Status</th><th>Count</th></tr>
            {''.join([f"<tr><td>{item['status__name'] or 'Unknown'}</td><td>{item['count']}</td></tr>" for item in stats['distributions']['status']])}
        </table>
    </div>
    
    <div class="section">
        <h2>Type Distribution</h2>
        <table>
            <tr><th>Type</th><th>Count</th></tr>
            {''.join([f"<tr><td>{item['type__name'] or 'Unknown'}</td><td>{item['count']}</td></tr>" for item in stats['distributions']['type']])}
        </table>
    </div>
    
    <div class="section">
        <h2>Feedback Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats['feedback']['total_feedback']}</div>
                <div>Total Feedback</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{round(stats['feedback']['avg_rating'], 2)}</div>
                <div>Average Rating</div>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.stdout.write(
            self.style.SUCCESS(f'HTML report generated: {filename}')
        )