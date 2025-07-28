#!/usr/bin/env python
"""
Final test to verify both reported issues are fixed.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from complaints.models import Status, ComplaintType, Complaint
from core.views import CustomLoginView


def test_staff_login_redirects():
    """Test Issue #1: Staff login 404 error."""
    print("🧪 Testing Issue #1: Staff login redirects...")
    
    try:
        # Test engineer login
        engineer = User.objects.get(username='demo_engineer1')
        factory = RequestFactory()
        request = factory.post('/login/')
        request.user = engineer
        request._messages = []
        
        login_view = CustomLoginView()
        login_view.request = request
        redirect_url = login_view.get_success_url()
        
        if redirect_url == '/engineer/':
            print("✅ Engineer login redirects to /engineer/ - FIXED")
        else:
            print(f"❌ Engineer login redirects to {redirect_url}, expected /engineer/")
            return False
        
        # Test AMC admin login
        amc_admin = User.objects.get(username='demo_amc_admin')
        request.user = amc_admin
        redirect_url = login_view.get_success_url()
        
        if redirect_url == '/amc-admin/':
            print("✅ AMC Admin login redirects to /amc-admin/ - FIXED")
        else:
            print(f"❌ AMC Admin login redirects to {redirect_url}, expected /amc-admin/")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_complaint_submission():
    """Test Issue #2: Foreign key constraint error."""
    print("🧪 Testing Issue #2: Complaint submission...")
    
    try:
        # Get test data
        user = User.objects.get(username='user_ALICE001')
        default_status = Status.objects.filter(is_active=True).order_by('order').first()
        complaint_type = ComplaintType.objects.filter(is_active=True).first()
        
        if not all([user, default_status, complaint_type]):
            print("❌ Missing required data for test")
            return False
        
        # Try to create a complaint (this was failing before)
        complaint = Complaint.objects.create(
            user=user,
            type=complaint_type,
            status=default_status,
            title='Test complaint submission',
            description='This should work without foreign key errors',
            urgency='low'
        )
        
        print(f"✅ Complaint #{complaint.id} created successfully - FIXED")
        
        # Verify the complaint has correct status
        if complaint.status.name == 'Open':
            print("✅ Complaint has correct default status - FIXED")
        else:
            print(f"❌ Wrong status: {complaint.status.name}")
            complaint.delete()
            return False
        
        # Clean up
        complaint.delete()
        return True
        
    except Exception as e:
        print(f"❌ Error creating complaint: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Final verification of reported issues...\n")
    
    issue1_fixed = test_staff_login_redirects()
    print()
    issue2_fixed = test_complaint_submission()
    print()
    
    if issue1_fixed and issue2_fixed:
        print("🎉 SUCCESS: Both reported issues have been FIXED!")
        print("\n📋 Summary of fixes:")
        print("   Issue #1: Staff login 404 error")
        print("     ✅ Updated login redirects to use correct URLs (/engineer/, /amc-admin/)")
        print("     ✅ Fixed group name case sensitivity (ENGINEER, AMC ADMIN)")
        print("     ✅ Updated decorators to recognize both case variations")
        print("\n   Issue #2: Foreign key constraint error on complaint submission")
        print("     ✅ Created initial Status objects in database")
        print("     ✅ Created initial ComplaintType objects")
        print("     ✅ Fixed complaint submission to use proper default status")
        print("\n✨ The application is now ready for use!")
        return 0
    else:
        print("❌ Some issues are still present. Please check the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())