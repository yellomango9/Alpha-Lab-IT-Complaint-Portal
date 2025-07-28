from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
from core.models import UserProfile, Department
from complaints.models import Complaint, ComplaintType, Status


class Command(BaseCommand):
    help = 'Set up demo users and groups for testing the complaint system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all demo data before creating new ones',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Resetting demo data...')
            User.objects.filter(username__startswith='demo_').delete()
            Group.objects.all().delete()

        with transaction.atomic():
            # Create groups if they don't exist
            groups = ['Engineer', 'AMC Admin', 'Admin']
            created_groups = {}
            
            for group_name in groups:
                group, created = Group.objects.get_or_create(name=group_name)
                created_groups[group_name] = group
                if created:
                    self.stdout.write(f'Created group: {group_name}')

            # Create departments if they don't exist
            departments_data = [
                ('IT Department', 'Information Technology'),
                ('HR Department', 'Human Resources'),
                ('Finance Department', 'Finance and Accounting'),
                ('Marketing Department', 'Marketing and Sales'),
                ('Operations Department', 'Operations and Logistics'),
            ]
            
            created_departments = {}
            for name, desc in departments_data:
                dept, created = Department.objects.get_or_create(
                    name=name,
                    defaults={'description': desc, 'is_active': True}
                )
                created_departments[name] = dept
                if created:
                    self.stdout.write(f'Created department: {name}')

            # Create demo users
            demo_users = [
                {
                    'username': 'demo_engineer1',
                    'first_name': 'John',
                    'last_name': 'Engineer',
                    'email': 'john.engineer@alphalab.com',
                    'password': 'demo123',
                    'groups': ['Engineer'],
                    'department': 'IT Department'
                },
                {
                    'username': 'demo_engineer2',
                    'first_name': 'Sarah',
                    'last_name': 'Tech',
                    'email': 'sarah.tech@alphalab.com',
                    'password': 'demo123',
                    'groups': ['Engineer'],
                    'department': 'IT Department'
                },
                {
                    'username': 'demo_amc_admin',
                    'first_name': 'Mike',
                    'last_name': 'Admin',
                    'email': 'mike.admin@alphalab.com',
                    'password': 'demo123',
                    'groups': ['AMC Admin'],
                    'department': 'IT Department'
                },
                {
                    'username': 'demo_admin',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'email': 'admin@alphalab.com',
                    'password': 'demo123',
                    'groups': ['Admin'],
                    'department': 'IT Department',
                    'is_staff': True,
                    'is_superuser': True
                }
            ]

            for user_data in demo_users:
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults={
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'email': user_data['email'],
                        'is_staff': user_data.get('is_staff', False),
                        'is_superuser': user_data.get('is_superuser', False)
                    }
                )
                
                if created:
                    user.set_password(user_data['password'])
                    user.save()
                    
                    # Add to groups
                    for group_name in user_data['groups']:
                        user.groups.add(created_groups[group_name])
                    
                    # Create profile
                    UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'department': created_departments[user_data['department']]
                        }
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created demo user: {user.username} ({", ".join(user_data["groups"])})'
                        )
                    )
                else:
                    self.stdout.write(f'User {user.username} already exists')

            # Create some demo normal users
            normal_users_data = [
                {
                    'username': 'user_ALICE001',
                    'first_name': 'Alice',
                    'last_name': 'Johnson',
                    'main_portal_id': 'ALICE001',
                    'department': 'HR Department'
                },
                {
                    'username': 'user_BOB002',
                    'first_name': 'Bob',
                    'last_name': 'Smith',
                    'main_portal_id': 'BOB002',
                    'department': 'Finance Department'
                },
                {
                    'username': 'user_CAROL003',
                    'first_name': 'Carol',
                    'last_name': 'Davis',
                    'main_portal_id': 'CAROL003',
                    'department': 'Marketing Department'
                }
            ]

            for user_data in normal_users_data:
                user, created = User.objects.get_or_create(
                    username=user_data['username'],
                    defaults={
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'email': ''
                    }
                )
                
                if created:
                    # Create profile with main_portal_id
                    UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'main_portal_id': user_data['main_portal_id'],
                            'department': created_departments[user_data['department']]
                        }
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created normal user: {user_data["main_portal_id"]} - {user.get_full_name()}'
                        )
                    )

            # Create some demo complaints
            if Complaint.objects.count() < 5:
                self.create_demo_complaints(created_departments)

        self.stdout.write(
            self.style.SUCCESS(
                '\n=== Demo Setup Complete ===\n'
                'Staff Users (login at /login/):\n'
                '  - demo_engineer1 / demo123 (Engineer)\n'
                '  - demo_engineer2 / demo123 (Engineer)\n'
                '  - demo_amc_admin / demo123 (AMC Admin)\n'
                '  - demo_admin / demo123 (Admin)\n\n'
                'Normal Users (login at /core/user/login/):\n'
                '  - Alice Johnson / ALICE001\n'
                '  - Bob Smith / BOB002\n'
                '  - Carol Davis / CAROL003\n'
            )
        )

    def create_demo_complaints(self, departments):
        """Create some demo complaints for testing."""
        # Get necessary objects
        complaint_types = list(ComplaintType.objects.filter(is_active=True)[:3])
        statuses = list(Status.objects.filter(is_active=True))
        normal_users = User.objects.filter(profile__main_portal_id__isnull=False)
        engineers = User.objects.filter(groups__name='Engineer')

        if not complaint_types or not statuses or not normal_users:
            self.stdout.write('Skipping demo complaints - missing required data')
            return

        demo_complaints = [
            {
                'description': 'My computer is running very slowly and freezing frequently. I cannot complete my work efficiently.',
                'urgency': 'medium',
                'user_index': 0,
                'type_index': 0,
                'assign_engineer': True
            },
            {
                'description': 'Unable to access my email account. Getting authentication error when trying to log in.',
                'urgency': 'high',
                'user_index': 1,
                'type_index': 1,
                'assign_engineer': False
            },
            {
                'description': 'The printer in our department is not working. Paper jams frequently and print quality is poor.',
                'urgency': 'low',
                'user_index': 2,
                'type_index': 2,
                'assign_engineer': True
            }
        ]

        for i, complaint_data in enumerate(demo_complaints):
            user = list(normal_users)[complaint_data['user_index']]
            complaint_type = complaint_types[complaint_data['type_index']]
            status = statuses[0]  # Use first status (usually "New")
            
            complaint = Complaint.objects.create(
                user=user,
                type=complaint_type,
                title=complaint_data['description'][:50] + '...',
                description=complaint_data['description'],
                urgency=complaint_data['urgency'],
                status=status
            )

            if complaint_data['assign_engineer'] and engineers:
                complaint.assigned_to = list(engineers)[i % len(engineers)]
                complaint.save()

            self.stdout.write(f'Created demo complaint #{complaint.id}')