from django.core.management.base import BaseCommand
from django.db import transaction
from complaints.models import Status, ComplaintType
from core.models import Department


class Command(BaseCommand):
    help = 'Setup initial data for the complaint system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        with transaction.atomic():
            # Create Status objects
            self.create_statuses()
            
            # Create ComplaintType objects
            self.create_complaint_types()
            
            # Create basic departments if they don't exist
            self.create_departments()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up initial data!')
        )

    def create_statuses(self):
        """Create default status objects."""
        statuses = [
            {'name': 'Open', 'description': 'Complaint has been submitted and is awaiting review', 'is_closed': False, 'order': 1},
            {'name': 'In Progress', 'description': 'Complaint is being worked on', 'is_closed': False, 'order': 2},
            {'name': 'Waiting for User', 'description': 'Waiting for response from user', 'is_closed': False, 'order': 3},
            {'name': 'Resolved', 'description': 'Complaint has been resolved', 'is_closed': True, 'order': 4},
            {'name': 'Closed', 'description': 'Complaint has been closed', 'is_closed': True, 'order': 5},
            {'name': 'Rejected', 'description': 'Complaint has been rejected', 'is_closed': True, 'order': 6},
        ]
        
        for status_data in statuses:
            status, created = Status.objects.get_or_create(
                name=status_data['name'],
                defaults=status_data
            )
            if created:
                self.stdout.write(f'  ✅ Created status: {status.name}')
            else:
                self.stdout.write(f'  ℹ️  Status already exists: {status.name}')

    def create_complaint_types(self):
        """Create default complaint types."""
        complaint_types = [
            {'name': 'Hardware Issue', 'description': 'Problems with computer hardware, peripherals, etc.'},
            {'name': 'Software Issue', 'description': 'Problems with software applications, operating system, etc.'},
            {'name': 'Network Issue', 'description': 'Problems with internet connectivity, network access, etc.'},
            {'name': 'Email Issue', 'description': 'Problems with email access, sending/receiving emails, etc.'},
            {'name': 'Account Access', 'description': 'Problems with user account access, password issues, etc.'},
            {'name': 'Printer Issue', 'description': 'Problems with printers, printing, etc.'},
            {'name': 'Other', 'description': 'Other IT-related issues not covered above'},
        ]
        
        for type_data in complaint_types:
            complaint_type, created = ComplaintType.objects.get_or_create(
                name=type_data['name'],
                defaults=type_data
            )
            if created:
                self.stdout.write(f'  ✅ Created complaint type: {complaint_type.name}')
            else:
                self.stdout.write(f'  ℹ️  Complaint type already exists: {complaint_type.name}')

    def create_departments(self):
        """Create basic departments."""
        departments = [
            {'name': 'IT Department', 'description': 'Information Technology Department'},
            {'name': 'Administration', 'description': 'Administrative Department'},
            {'name': 'Finance', 'description': 'Finance Department'},
            {'name': 'HR', 'description': 'Human Resources Department'},
            {'name': 'Operations', 'description': 'Operations Department'},
        ]
        
        for dept_data in departments:
            department, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults=dept_data
            )
            if created:
                self.stdout.write(f'  ✅ Created department: {department.name}')
            else:
                self.stdout.write(f'  ℹ️  Department already exists: {department.name}')