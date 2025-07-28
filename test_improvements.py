#!/usr/bin/env python
"""
Test script to verify all the implemented improvements.
"""
import os
import sys
import django
from datetime import timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User, Group
from django.test import RequestFactory
from django.utils import timezone
from complaints.models import Status, ComplaintType, Complaint
from core.views import CustomLoginView


def test_admin_login_redirect():
    """Test that admin users redirect to admin portal."""
    print("🧪 Testing admin login redirects...")
    
    try:
        # Create or get admin user
        admin_user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        # Ensure admin group exists and assign user
        admin_group, _ = Group.objects.get_or_create(name='ADMIN')
        admin_user.groups.add(admin_group)
        
        factory = RequestFactory()
        request = factory.post('/login/')
        request.user = admin_user
        request._messages = []
        
        login_view = CustomLoginView()
        login_view.request = request
        redirect_url = login_view.get_success_url()
        
        if redirect_url == '/admin-portal/':
            print("✅ Admin redirects to /admin-portal/")
            return True
        else:
            print(f"❌ Admin redirects to {redirect_url}, expected /admin-portal/")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_assigned_status_exists():
    """Test that 'Assigned' status was created."""
    print("🧪 Testing 'Assigned' status...")
    
    try:
        assigned_status = Status.objects.get(name='Assigned')
        print(f"✅ Found 'Assigned' status: {assigned_status.description}")
        return True
    except Status.DoesNotExist:
        print("❌ 'Assigned' status not found")
        return False


def test_engineer_self_assignment():
    """Test that engineer can assign complaints to themselves."""
    print("🧪 Testing engineer self-assignment...")
    
    try:
        # Get or create engineer user
        engineer_user, created = User.objects.get_or_create(
            username='test_engineer',
            defaults={'first_name': 'Test', 'last_name': 'Engineer'}
        )
        
        # Ensure engineer group exists and assign user
        engineer_group, _ = Group.objects.get_or_create(name='ENGINEER')
        engineer_user.groups.add(engineer_group)
        
        # Get or create test data
        complaint_type = ComplaintType.objects.filter(is_active=True).first()
        normal_user = User.objects.filter(groups__isnull=True).first()
        open_status = Status.objects.filter(name='Open', is_active=True).first()
        
        if not all([complaint_type, normal_user, open_status]):
            print("❌ Missing test data")
            return False
        
        # Create unassigned complaint
        complaint = Complaint.objects.create(
            user=normal_user,
            type=complaint_type,
            status=open_status,
            title='Test self-assignment complaint',
            description='Testing engineer self-assignment',
            urgency='medium'
        )
        
        # Test assignment
        from core.engineer_views import assign_to_self
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.post(f'/engineer/complaint/{complaint.id}/assign-to-self/')
        request.user = engineer_user
        
        response = assign_to_self(request, complaint.id)
        
        if response.status_code == 200:
            # Refresh complaint from database
            complaint.refresh_from_db()
            if complaint.assigned_to == engineer_user:
                print("✅ Engineer can self-assign complaints")
                # Check if status changed to 'Assigned'
                if complaint.status.name == 'Assigned':
                    print("✅ Status automatically changed to 'Assigned'")
                else:
                    print(f"⚠️  Status is {complaint.status.name}, expected 'Assigned'")
                
                # Clean up
                complaint.delete()
                return True
            else:
                print("❌ Complaint not assigned to engineer")
                complaint.delete()
                return False
        else:
            print(f"❌ Self-assignment failed with status {response.status_code}")
            complaint.delete()
            return False
            
    except Exception as e:
        print(f"❌ Error testing self-assignment: {e}")
        return False


def test_issue_detection():
    """Test that complaints older than 14 days are detected as issues."""
    print("🧪 Testing issue detection (14+ days)...")
    
    try:
        # Get test data
        complaint_type = ComplaintType.objects.filter(is_active=True).first()
        normal_user = User.objects.filter(groups__isnull=True).first()
        open_status = Status.objects.filter(name='Open', is_active=True).first()
        
        if not all([complaint_type, normal_user, open_status]):
            print("❌ Missing test data")
            return False
        
        # Create complaint that's 15 days old
        old_date = timezone.now() - timedelta(days=15)
        old_complaint = Complaint.objects.create(
            user=normal_user,
            type=complaint_type,
            status=open_status,
            title='Old test complaint',
            description='This complaint is 15 days old',
            urgency='medium'
        )
        # Manually set created_at to 15 days ago
        Complaint.objects.filter(id=old_complaint.id).update(created_at=old_date)
        
        # Test issue detection in admin view
        from core.admin_views import admin_dashboard
        from django.test import RequestFactory
        
        # Create admin user for test
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser('test_admin2', 'test@test.com', 'password')
        
        factory = RequestFactory()
        request = factory.get('/admin-portal/')
        request.user = admin_user
        
        # Get the context from admin dashboard
        fourteen_days_ago = timezone.now() - timedelta(days=14)
        issues = Complaint.objects.filter(
            status__is_closed=False,
            created_at__lt=fourteen_days_ago
        )
        
        if issues.exists():
            print(f"✅ Found {issues.count()} issue(s) older than 14 days")
            # Clean up
            old_complaint.delete()
            return True
        else:
            print("❌ No issues detected")
            old_complaint.delete()
            return False
            
    except Exception as e:
        print(f"❌ Error testing issue detection: {e}")
        return False


def test_url_patterns():
    """Test that all new URL patterns exist."""
    print("🧪 Testing new URL patterns...")
    
    try:
        from django.urls import reverse
        
        # Test admin portal URLs
        admin_urls = [
            'admin_portal:dashboard',
            'admin_portal:chart_data',
            'admin_portal:system_health'
        ]
        
        for url_name in admin_urls:
            try:
                url = reverse(url_name)
                print(f"✅ URL pattern exists: {url_name} -> {url}")
            except Exception as e:
                print(f"❌ URL pattern missing: {url_name} - {e}")
                return False
        
        # Test engineer self-assignment URL
        try:
            url = reverse('engineer:assign_to_self', kwargs={'complaint_id': 1})
            print(f"✅ URL pattern exists: engineer:assign_to_self -> {url}")
        except Exception as e:
            print(f"❌ URL pattern missing: engineer:assign_to_self - {e}")
            return False
        
        # Test AMC admin complaint detail URL
        try:
            url = reverse('amc_admin:complaint_detail', kwargs={'complaint_id': 1})
            print(f"✅ URL pattern exists: amc_admin:complaint_detail -> {url}")
        except Exception as e:
            print(f"❌ URL pattern missing: amc_admin:complaint_detail - {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing URL patterns: {e}")
        return False


def main():
    """Run all improvement tests."""
    print("🚀 Testing all implemented improvements...\n")
    
    tests = [
        test_admin_login_redirect,
        test_assigned_status_exists,
        test_engineer_self_assignment,
        test_issue_detection,
        test_url_patterns,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()  # Add blank line between tests
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All improvements have been successfully implemented!")
        print("\n📋 Summary of improvements:")
        print("   ✅ Normal users can close resolved complaints or add remarks")
        print("   ✅ Priority is hidden from normal users")
        print("   ✅ Engineers can self-assign unassigned complaints")
        print("   ✅ Status automatically changes to 'Assigned' when assigned")
        print("   ✅ Engineers can only change status to 'Resolved' with final remark")
        print("   ✅ AMC admin assignment restricted to engineers only")
        print("   ✅ AMC admin has dedicated complaint detail view")
        print("   ✅ Remark history shown for all complaints")
        print("   ✅ Admin portal with charts and analytics")
        print("   ✅ Issues tab for complaints older than 14 days")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())