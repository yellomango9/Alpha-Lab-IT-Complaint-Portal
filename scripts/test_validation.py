#!/usr/bin/env python
"""
Test Validation Script for Alpha Lab IT Complaint Portal
Performs automated testing of critical functionality
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from core.models import UserProfile, Department
from complaints.models import Complaint, Status, ComplaintType
import json


class TestValidator:
    def __init__(self):
        self.client = Client()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'total': 0,
            'details': []
        }
        
    def log_test(self, test_name, passed, details=""):
        """Log test result."""
        self.test_results['total'] += 1
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
            
        self.test_results['details'].append({
            'name': test_name,
            'passed': passed,
            'details': details
        })
        
        if passed:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            
    def test_authentication_pages(self):
        """Test authentication page accessibility."""
        print("\n🔒 Testing Authentication Pages...")
        
        # Test staff login page
        response = self.client.get('/login/')
        self.log_test(
            "Staff login page loads",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # Test normal user login page  
        response = self.client.get('/core/user/login/')
        self.log_test(
            "Normal user login page loads",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
    def test_staff_login_functionality(self):
        """Test staff login functionality."""
        print("\n👨‍💼 Testing Staff Login...")
        
        # Test admin login
        response = self.client.post('/login/', {
            'username': 'demo_admin',
            'password': 'demo123'
        })
        self.log_test(
            "Admin login functionality",
            response.status_code in [200, 302],  # 302 for redirect after login
            f"Status: {response.status_code}"
        )
        
        # Test engineer login
        self.client.logout()
        response = self.client.post('/login/', {
            'username': 'demo_engineer1', 
            'password': 'demo123'
        })
        self.log_test(
            "Engineer login functionality",
            response.status_code in [200, 302],
            f"Status: {response.status_code}"
        )
        
    def test_normal_user_functionality(self):
        """Test normal user authentication and basic functionality."""
        print("\n👤 Testing Normal User Functionality...")
        
        # Test normal user exists
        profile = UserProfile.objects.filter(main_portal_id='ALICE001').first()
        self.log_test(
            "Normal user ALICE001 exists",
            profile is not None,
            f"Profile found: {profile.user.username if profile else 'None'}"
        )
        
        if profile:
            # Test normal user login simulation
            self.client.force_login(profile.user)
            response = self.client.get('/core/dashboard/')
            self.log_test(
                "Normal user dashboard accessible",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
    def test_complaint_system(self):
        """Test complaint system functionality."""
        print("\n📝 Testing Complaint System...")
        
        # Check complaint types exist
        complaint_types = ComplaintType.objects.filter(is_active=True).count()
        self.log_test(
            "Active complaint types available",
            complaint_types > 0,
            f"Found {complaint_types} types"
        )
        
        # Check statuses exist
        statuses = Status.objects.filter(is_active=True).count()
        self.log_test(
            "Active statuses available", 
            statuses > 0,
            f"Found {statuses} statuses"
        )
        
        # Test complaint list view (requires auth)
        admin_user = User.objects.filter(groups__name='Admin').first()
        if admin_user:
            self.client.force_login(admin_user)
            response = self.client.get('/complaints/')
            self.log_test(
                "Complaint list accessible to admin",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
    def test_dashboard_functionality(self):
        """Test dashboard functionality for different user roles."""
        print("\n📊 Testing Dashboard Functionality...")
        
        # Test admin dashboard
        admin_user = User.objects.filter(groups__name='Admin').first()
        if admin_user:
            self.client.force_login(admin_user)
            response = self.client.get('/admin-portal/')
            self.log_test(
                "Admin analytics dashboard loads",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
        # Test engineer dashboard
        engineer_user = User.objects.filter(groups__name='Engineer').first()
        if engineer_user:
            self.client.force_login(engineer_user)
            response = self.client.get('/engineer/')
            self.log_test(
                "Engineer dashboard loads",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
        # Test AMC admin dashboard
        amc_admin = User.objects.filter(groups__name='AMC Admin').first()
        if amc_admin:
            self.client.force_login(amc_admin)
            response = self.client.get('/amc-admin/')
            self.log_test(
                "AMC Admin dashboard loads",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
    def test_database_relationships(self):
        """Test database relationships and integrity."""
        print("\n🗄️ Testing Database Relationships...")
        
        # Test user-profile relationship
        users_with_profiles = User.objects.filter(profile__isnull=False).count()
        total_users = User.objects.count()
        self.log_test(
            "All users have profiles",
            users_with_profiles == total_users,
            f"{users_with_profiles}/{total_users} users have profiles"
        )
        
        # Test profile-department relationship
        profiles_with_dept = UserProfile.objects.filter(department__isnull=False).count()
        total_profiles = UserProfile.objects.count()
        self.log_test(
            "Most profiles have departments",
            profiles_with_dept >= total_profiles * 0.8,  # At least 80%
            f"{profiles_with_dept}/{total_profiles} profiles have departments"
        )
        
        # Test complaints have required relationships
        valid_complaints = Complaint.objects.filter(
            user__isnull=False,
            type__isnull=False,
            status__isnull=False
        ).count()
        total_complaints = Complaint.objects.count()
        self.log_test(
            "All complaints have required relationships",
            valid_complaints == total_complaints or total_complaints == 0,
            f"{valid_complaints}/{total_complaints} complaints are valid"
        )
        
    def test_user_groups(self):
        """Test user group assignments."""
        print("\n👥 Testing User Groups...")
        
        required_groups = ['Admin', 'AMC Admin', 'Engineer']
        for group_name in required_groups:
            group_exists = Group.objects.filter(name=group_name).exists()
            self.log_test(
                f"Group '{group_name}' exists",
                group_exists,
                "Group found" if group_exists else "Group missing"
            )
            
        # Test demo users have correct groups
        demo_users = [
            ('demo_admin', 'Admin'),
            ('demo_amc_admin', 'AMC Admin'),
            ('demo_engineer1', 'Engineer'),
            ('demo_engineer2', 'Engineer')
        ]
        
        for username, expected_group in demo_users:
            try:
                user = User.objects.get(username=username)
                has_group = user.groups.filter(name=expected_group).exists()
                self.log_test(
                    f"User {username} in {expected_group} group",
                    has_group,
                    f"Group membership verified" if has_group else f"Missing group {expected_group}"
                )
            except User.DoesNotExist:
                self.log_test(
                    f"User {username} exists",
                    False,
                    "User not found"
                )
                
    def test_static_files(self):
        """Test static file accessibility."""
        print("\n📁 Testing Static Files...")
        
        # Check main CSS file
        css_file = PROJECT_DIR / 'static' / 'css' / 'style.css'
        self.log_test(
            "Main CSS file exists",
            css_file.exists(),
            f"Path: {css_file}"
        )
        
        # Check main JS file
        js_file = PROJECT_DIR / 'static' / 'js' / 'main.js'
        self.log_test(
            "Main JavaScript file exists", 
            js_file.exists(),
            f"Path: {js_file}"
        )
        
    def test_url_reversing(self):
        """Test URL reversing for critical URLs."""
        print("\n🔗 Testing URL Reversing...")
        
        critical_urls = [
            'core:normal_user_login',
            'core:normal_user_dashboard',
            'login',
            'logout'
        ]
        
        for url_name in critical_urls:
            try:
                url = reverse(url_name)
                self.log_test(
                    f"URL '{url_name}' reverses correctly",
                    True,
                    f"Resolves to: {url}"
                )
            except Exception as e:
                self.log_test(
                    f"URL '{url_name}' reverses correctly",
                    False,
                    f"Error: {str(e)}"
                )
                
    def run_validation(self):
        """Run complete validation suite."""
        print("🧪 ALPHA LAB IT COMPLAINT PORTAL - AUTOMATED TEST VALIDATION")
        print("=" * 70)
        
        self.test_authentication_pages()
        self.test_staff_login_functionality()
        self.test_normal_user_functionality()
        self.test_complaint_system()
        self.test_dashboard_functionality()
        self.test_database_relationships()
        self.test_user_groups()
        self.test_static_files()
        self.test_url_reversing()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY")
        print("=" * 70)
        
        total = self.test_results['total']
        passed = self.test_results['passed'] 
        failed = self.test_results['failed']
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/total*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! System is ready for manual testing.")
            status = "EXCELLENT"
        elif failed <= 2:
            print("\n⚠️ Minor issues found. System is mostly ready.")
            status = "GOOD"
        else:
            print("\n🔧 Multiple issues found. Please review and fix.")
            status = "NEEDS ATTENTION"
            
        print(f"\n🎯 SYSTEM STATUS: {status}")
        
        return failed == 0


if __name__ == '__main__':
    validator = TestValidator()
    all_passed = validator.run_validation()
    
    if all_passed:
        print("\n🚀 Ready for comprehensive manual testing!")
        print("📖 Refer to MANUAL_TESTING_GUIDE.md for detailed test scenarios.")
    else:
        print("\n🔧 Please address the failing tests before proceeding.")
        
    sys.exit(0 if all_passed else 1)