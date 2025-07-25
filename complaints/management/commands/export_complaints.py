"""
Management command to export complaints data to CSV format.
Usage: python manage.py export_complaints [--output filename.csv] [--date-from YYYY-MM-DD] [--date-to YYYY-MM-DD]
"""

import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from complaints.models import Complaint


class Command(BaseCommand):
    help = 'Export complaints data to CSV format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=f'complaints_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv',
            help='Output CSV filename (default: complaints_export_YYYYMMDD_HHMMSS.csv)'
        )
        
        parser.add_argument(
            '--date-from',
            type=str,
            help='Export complaints from this date (YYYY-MM-DD format)'
        )
        
        parser.add_argument(
            '--date-to',
            type=str,
            help='Export complaints up to this date (YYYY-MM-DD format)'
        )
        
        parser.add_argument(
            '--status',
            type=str,
            help='Filter by status name'
        )
        
        parser.add_argument(
            '--type',
            type=str,
            help='Filter by complaint type name'
        )

    def handle(self, *args, **options):
        try:
            # Build queryset with filters
            queryset = Complaint.objects.select_related(
                'user', 'type', 'status', 'assigned_to'
            ).order_by('-created_at')
            
            # Apply date filters
            if options['date_from']:
                date_from = datetime.strptime(options['date_from'], '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
                
            if options['date_to']:
                date_to = datetime.strptime(options['date_to'], '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            
            # Apply status filter
            if options['status']:
                queryset = queryset.filter(status__name__icontains=options['status'])
            
            # Apply type filter
            if options['type']:
                queryset = queryset.filter(type__name__icontains=options['type'])
            
            # Export to CSV
            filename = options['output']
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'ID', 'Title', 'Description', 'Type', 'Status', 'Urgency',
                    'User', 'User Email', 'Assigned To', 'Location', 'Contact Number',
                    'Created At', 'Updated At', 'Resolved At', 'Resolution Notes'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                count = 0
                for complaint in queryset:
                    writer.writerow({
                        'ID': complaint.id,
                        'Title': complaint.title,
                        'Description': complaint.description,
                        'Type': complaint.type.name if complaint.type else '',
                        'Status': complaint.status.name if complaint.status else '',
                        'Urgency': complaint.get_urgency_display(),
                        'User': complaint.user.get_full_name() or complaint.user.username,
                        'User Email': complaint.user.email,
                        'Assigned To': complaint.assigned_to.get_full_name() if complaint.assigned_to else '',
                        'Location': complaint.location or '',
                        'Contact Number': complaint.contact_number or '',
                        'Created At': complaint.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'Updated At': complaint.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'Resolved At': complaint.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if complaint.resolved_at else '',
                        'Resolution Notes': complaint.resolution_notes or '',
                    })
                    count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully exported {count} complaints to {filename}'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Error exporting complaints: {str(e)}')