#!/usr/bin/env python
"""
Test script to verify that the reported issues are fixed.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory, Client
from django.urls import reverse
from complaints.models import Status, ComplaintType


def test_status_objects_exist():
    """Test that Status objects exist in database."""
    print("🧪 Testing Status objects...")
    
    status_count = Status.objects.count()
    if status_count > 0:
        print(f"✅ Found {status_count} Status objects")
        
        # Check for default status
        default_status = Status.objects.filter(is_active=True).order_by('order').first()
        if default_status:
            print(f"✅ Default status found: {default_status.name}")
            return True
        else:
            print("❌ No default status found")
            return False
    else:
        print("❌ No Status objects found")
        return False


def test_complaint_types_exist():
    """Test that ComplaintType objects exist."""
    print("🧪 Testing ComplaintType objects...")
    
    type_count = ComplaintType.objects.count()
    if type_count > 0:
        print(f"✅ Found {type_count} ComplaintType objects")
        return True
    else:
        print("❌ No ComplaintType objects found")
        return False


def test_staff_login_redirect():
    """Test that staff login redirects properly."""
    print("🧪 Testing staff login redirects...")
    
    try:
        # Get demo users
        engineer = User.objects.get(username='demo_engineer1')
        amc_admin = User.objects.get(username='demo_amc_admin')
        
        print(f"Engineer groups: {list(engineer.groups.values_list('name', flat=True))}")
        print(f"AMC Admin groups: {list(amc_admin.groups.values_list('name', flat=True))}")
        
        # Test engineer login redirect
        from core.views import CustomLoginView
        factory = RequestFactory()
        
        # Create a mock request and login view
        request = factory.post('/login/')
        request.user = engineer
        request._messages = []  # Mock messages framework
        
        login_view = CustomLoginView()
        login_view.request = request
        
        redirect_url = login_view.get_success_url()
        print(f"Engineer redirect URL: {redirect_url}")
        if redirect_url == '/engineer/':
            print("✅ Engineer login redirects to /engineer/")
        else:
            print(f"❌ Engineer login redirects to {redirect_url}, expected /engineer/")
            # Let's debug why
            print(f"Engineer is_superuser: {engineer.is_superuser}")
            print(f"Engineer is_staff: {engineer.is_staff}")
            return False
        
        # Test AMC admin login redirect
        request.user = amc_admin
        redirect_url = login_view.get_success_url()
        print(f"AMC Admin redirect URL: {redirect_url}")
        if redirect_url == '/amc-admin/':
            print("✅ AMC Admin login redirects to /amc-admin/")
        else:
            print(f"❌ AMC Admin login redirects to {redirect_url}, expected /amc-admin/")
            # Let's debug why
            print(f"AMC Admin is_superuser: {amc_admin.is_superuser}")
            print(f"AMC Admin is_staff: {amc_admin.is_staff}")
            return False
        
        return True
        
    except User.DoesNotExist:
        print("❌ Demo users not found. Please run 'python manage.py setup_demo_users' first.")
        return False
    except Exception as e:
        print(f"❌ Error testing login redirects: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_url_patterns():
    """Test that URL patterns exist."""
    print("🧪 Testing URL patterns...")
    
    try:
        # Test engineer URLs
        engineer_urls = [
            'engineer:dashboard',
            'engineer:complaint_detail', 
            'engineer:update_complaint_status',
            'engineer:download_complaint_pdf'
        ]
        
        for url_name in engineer_urls:
            try:
                if 'complaint_detail' in url_name or 'update_complaint_status' in url_name or 'download_complaint_pdf' in url_name:
                    url = reverse(url_name, kwargs={'complaint_id': 1})
                else:
                    url = reverse(url_name)
                print(f"✅ URL pattern exists: {url_name} -> {url}")
            except Exception as e:
                print(f"❌ URL pattern missing: {url_name} - {e}")
                return False
        
        # Test AMC admin URLs
        amc_admin_urls = [
            'amc_admin:dashboard',
            'amc_admin:download_complaints_report',
            'amc_admin:bulk_actions'
        ]
        
        for url_name in amc_admin_urls:
            try:
                url = reverse(url_name)
                print(f"✅ URL pattern exists: {url_name} -> {url}")
            except Exception as e:
                print(f"❌ URL pattern missing: {url_name} - {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing URL patterns: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Running fix verification tests...\n")
    
    tests = [
        test_status_objects_exist,
        test_complaint_types_exist,
        test_staff_login_redirect,
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
        print("🎉 All tests passed! The issues have been fixed.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())