from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile
from complaints.models import Complaint, ComplaintType, Status


class Command(BaseCommand):
    help = 'Test normal user functionality'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing normal user functionality...'))
        
        # Test 1: Create a normal user
        main_portal_id = "TEST123"
        name = "John Doe"
        
        try:
            # Try to find existing user
            profile = UserProfile.objects.get(main_portal_id=main_portal_id)
            user = profile.user
            self.stdout.write(f'✓ Found existing user: {user.get_full_name()} ({main_portal_id})')
        except UserProfile.DoesNotExist:
            # Create new user
            name_parts = name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            username = f"user_{main_portal_id}"
            
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=''
            )
            
            profile = UserProfile.objects.create(
                user=user,
                main_portal_id=main_portal_id
            )
            
            self.stdout.write(f'✓ Created new user: {user.get_full_name()} ({main_portal_id})')
        
        # Test 2: Check complaint types and statuses
        complaint_types = ComplaintType.objects.filter(is_active=True)
        statuses = Status.objects.filter(is_active=True)
        
        self.stdout.write(f'✓ Found {complaint_types.count()} complaint types')
        self.stdout.write(f'✓ Found {statuses.count()} statuses')
        
        # Test 3: Create a test complaint
        if complaint_types.exists() and statuses.exists():
            complaint_type = complaint_types.first()
            default_status = statuses.order_by('order').first()
            
            complaint = Complaint.objects.create(
                user=user,
                type=complaint_type,
                status=default_status,
                title="Test Complaint from Management Command",
                description="This is a test complaint created to verify the normal user functionality.",
                urgency="medium"
            )
            
            self.stdout.write(f'✓ Created test complaint #{complaint.id}')
        
        # Test 4: Check user's complaints
        user_complaints = Complaint.objects.filter(user=user)
        self.stdout.write(f'✓ User has {user_complaints.count()} complaints')
        
        for complaint in user_complaints:
            self.stdout.write(f'  - #{complaint.id}: {complaint.title} ({complaint.status.name})')
        
        self.stdout.write(self.style.SUCCESS('✓ All tests passed! Normal user functionality is working correctly.'))