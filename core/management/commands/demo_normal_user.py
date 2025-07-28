from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile
from complaints.models import Complaint, ComplaintType, Status
from faq.models import FAQ, FAQCategory


class Command(BaseCommand):
    help = 'Demo normal user workflow'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Normal User Portal Demo ==='))
        
        # Simulate user login flow
        self.stdout.write('\n1. User Login Simulation:')
        demo_users = [
            ('Alice Johnson', 'ALICE001'),
            ('Bob Smith', 'BOB002'),
            ('Carol Davis', 'CAROL003')
        ]
        
        created_users = []
        for name, portal_id in demo_users:
            try:
                profile = UserProfile.objects.get(main_portal_id=portal_id)
                user = profile.user
                self.stdout.write(f'   ✓ Existing user: {name} ({portal_id})')
            except UserProfile.DoesNotExist:
                name_parts = name.split(' ', 1)
                username = f"user_{portal_id}"
                
                user = User.objects.create_user(
                    username=username,
                    first_name=name_parts[0],
                    last_name=name_parts[1] if len(name_parts) > 1 else '',
                    email=''
                )
                
                profile = UserProfile.objects.create(
                    user=user,
                    main_portal_id=portal_id
                )
                
                self.stdout.write(f'   ✓ Created user: {name} ({portal_id})')
            
            created_users.append((user, profile))
        
        # Simulate complaint submissions
        self.stdout.write('\n2. Complaint Submission Simulation:')
        complaint_scenarios = [
            ('My laptop screen is flickering', 'Hardware Issue', 'high', 'The laptop screen keeps flickering and sometimes goes completely black.'),
            ('Cannot access email', 'Email Issue', 'medium', 'I keep getting authentication errors when trying to access my email.'),
            ('Printer not responding', 'Printer Issue', 'low', 'The office printer is not responding to print commands.'),
            ('WiFi connection drops frequently', 'Network Issue', 'medium', 'The WiFi connection keeps dropping every few minutes.'),
            ('Software installation request', 'Software Issue', 'low', 'Need to install Adobe Acrobat for document processing.'),
        ]
        
        complaint_types = {ct.name: ct for ct in ComplaintType.objects.filter(is_active=True)}
        default_status = Status.objects.filter(is_active=True).order_by('order').first()
        
        for i, (title, type_name, urgency, description) in enumerate(complaint_scenarios):
            if i < len(created_users):
                user, profile = created_users[i % len(created_users)]
                complaint_type = complaint_types.get(type_name)
                
                if complaint_type:
                    complaint = Complaint.objects.create(
                        user=user,
                        type=complaint_type,
                        status=default_status,
                        title=title,
                        description=description,
                        urgency=urgency
                    )
                    self.stdout.write(f'   ✓ Created complaint #{complaint.id}: {title} by {user.get_full_name()}')
        
        # Display user complaints summary
        self.stdout.write('\n3. User Complaints Summary:')
        for user, profile in created_users:
            user_complaints = Complaint.objects.filter(user=user)
            self.stdout.write(f'   • {user.get_full_name()} ({profile.main_portal_id}): {user_complaints.count()} complaints')
            for complaint in user_complaints:
                self.stdout.write(f'     - #{complaint.id}: {complaint.title} [{complaint.urgency}] ({complaint.status.name})')
        
        # Display available complaint types
        self.stdout.write('\n4. Available Complaint Types:')
        for ct in ComplaintType.objects.filter(is_active=True).order_by('name'):
            self.stdout.write(f'   • {ct.name}: {ct.description}')
        
        # Display FAQ summary
        self.stdout.write('\n5. FAQ System:')
        categories = FAQCategory.objects.filter(is_active=True).order_by('order', 'name')
        for category in categories:
            faqs = category.faqs.filter(is_active=True)
            self.stdout.write(f'   • {category.name}: {faqs.count()} FAQs')
            for faq in faqs[:2]:  # Show first 2 FAQs per category
                self.stdout.write(f'     - {faq.question}')
        
        # Display access URLs
        self.stdout.write('\n6. Portal Access URLs:')
        self.stdout.write('   • Normal User Login: http://127.0.0.1:8000/core/user/login/')
        self.stdout.write('   • Direct Access: http://127.0.0.1:8000/ (redirects to user login)')
        self.stdout.write('   • Staff Login: http://127.0.0.1:8000/login/')
        self.stdout.write('   • Admin Panel: http://127.0.0.1:8000/admin/')
        
        self.stdout.write(self.style.SUCCESS('\n=== Demo completed successfully! ==='))
        self.stdout.write('You can now test the portal by visiting: http://127.0.0.1:8000/')
        self.stdout.write('Try logging in with any of the demo users:')
        for name, portal_id in demo_users:
            self.stdout.write(f'  - Name: {name}, Portal ID: {portal_id}')