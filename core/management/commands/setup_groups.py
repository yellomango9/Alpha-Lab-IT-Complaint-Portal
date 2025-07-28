"""
Management command to set up required user groups for the AMC Portal.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User
from django.db import transaction


class Command(BaseCommand):
    help = 'Set up required user groups for the AMC Portal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-test-users',
            action='store_true',
            help='Create test users for development',
        )

    def handle(self, *args, **options):
        """Create required groups and optionally test users."""
        
        # Define required groups
        required_groups = [
            {
                'name': 'Admin',
                'description': 'System administrators with full access'
            },
            {
                'name': 'AMC Admin', 
                'description': 'AMC administrators with specialized access'
            },
            {
                'name': 'Engineer',
                'description': 'IT engineers who handle complaint resolution'
            }
        ]

        with transaction.atomic():
            # Create groups
            created_groups = []
            for group_data in required_groups:
                group, created = Group.objects.get_or_create(
                    name=group_data['name']
                )
                if created:
                    created_groups.append(group.name)
                    self.stdout.write(
                        self.style.SUCCESS(f'Created group: {group.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Group already exists: {group.name}')
                    )

            # Create test users if requested
            if options['create_test_users']:
                self.create_test_users()

        if created_groups:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully created {len(created_groups)} groups: '
                    f'{", ".join(created_groups)}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nAll required groups already exist.')
            )

        self.stdout.write(
            self.style.SUCCESS(
                '\nGroup setup complete! Users must be assigned to one of these groups '
                'to access the portal: Admin, AMC Admin, Engineer'
            )
        )

    def create_test_users(self):
        """Create test users for development."""
        test_users = [
            {
                'username': 'admin',
                'password': 'admin123',
                'email': 'admin@alphalab.com',
                'first_name': 'System',
                'last_name': 'Administrator',
                'groups': ['Admin']
            },
            {
                'username': 'amc_admin',
                'password': 'testpass123',
                'email': 'amc.admin@alphalab.com',
                'first_name': 'AMC',
                'last_name': 'Administrator',
                'groups': ['AMC Admin']
            },
            {
                'username': 'engineer1',
                'password': 'testpass123',
                'email': 'engineer1@alphalab.com',
                'first_name': 'John',
                'last_name': 'Engineer',
                'groups': ['Engineer']
            },
            {
                'username': 'engineer2',
                'password': 'testpass123',
                'email': 'engineer2@alphalab.com',
                'first_name': 'Jane',
                'last_name': 'Engineer',
                'groups': ['Engineer']
            }
        ]

        self.stdout.write('\nCreating test users...')
        
        for user_data in test_users:
            username = user_data['username']
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'User already exists: {username}')
                )
                continue

            # Create user
            user = User.objects.create_user(
                username=username,
                password=user_data['password'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )

            # Add to groups
            for group_name in user_data['groups']:
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created user: {username} (added to {group_name} group)'
                        )
                    )
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Group {group_name} does not exist for user {username}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                '\nTest users created! You can now log in with:'
                '\n- admin / admin123 (Admin)'
                '\n- amc_admin / testpass123 (AMC Admin)'
                '\n- engineer1 / testpass123 (Engineer)'
                '\n- engineer2 / testpass123 (Engineer)'
            )
        )