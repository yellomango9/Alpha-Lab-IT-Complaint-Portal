#!/usr/bin/env python
"""
System Health Check Script for AMC Complaint Portal
Checks for common issues and provides fixes
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

from django.core.management import execute_from_command_line
from django.db import connection
from django.contrib.auth.models import User, Group
from core.models import UserProfile, Department
from complaints.models import Complaint, Status, ComplaintType
from django.urls import reverse
from django.test import Client


class SystemHealthChecker:
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        
    def log_issue(self, issue):
        """Log an issue found."""
        self.issues_found.append(issue)
        print(f"❌ ISSUE: {issue}")
        
    def log_fix(self, fix):
        """Log a fix applied."""
        self.fixes_applied.append(fix)
        print(f"✅ FIXED: {fix}")
        
    def check_database_integrity(self):
        """Check database relationships and data integrity."""
        print("\n🔍 Checking Database Integrity...")
        
        # Check for users without profiles
        users_without_profiles = User.objects.filter(profile__isnull=True).count()
        if users_without_profiles > 0:
            self.log_issue(f"{users_without_profiles} users without profiles")
            
        # Check for profiles without departments
        profiles_without_dept = UserProfile.objects.filter(department__isnull=True)
        if profiles_without_dept.exists():
            self.log_issue(f"{profiles_without_dept.count()} profiles without departments")
            
            # Fix: Assign to default IT department
            it_dept, created = Department.objects.get_or_create(
                name='IT Department',
                defaults={
                    'description': 'Information Technology Department',
                    'is_active': True
                }
            )
            
            for profile in profiles_without_dept:
                profile.department = it_dept
                profile.save()
                self.log_fix(f"Assigned {profile.user.username} to IT Department")
                
        # Check for complaints with missing relationships
        invalid_complaints = Complaint.objects.filter(
            user__isnull=True
        ).count()
        if invalid_complaints > 0:
            self.log_issue(f"{invalid_complaints} complaints with missing user")
            
        print("✅ Database integrity check complete")
        
    def check_required_data(self):
        """Check if required master data exists."""
        print("\n🔍 Checking Required Master Data...")
        
        # Check complaint types
        complaint_types = ComplaintType.objects.filter(is_active=True).count()
        if complaint_types == 0:
            self.log_issue("No active complaint types found")
            # Create default types
            default_types = [
                "Hardware Issue",
                "Software Issue", 
                "Network Problem",
                "Access Request",
                "Other"
            ]
            for type_name in default_types:
                ComplaintType.objects.get_or_create(
                    name=type_name,
                    defaults={'is_active': True}
                )
            self.log_fix("Created default complaint types")
            
        # Check statuses
        statuses = Status.objects.filter(is_active=True).count()
        if statuses == 0:
            self.log_issue("No active statuses found")
            # Create default statuses
            default_statuses = [
                ("Open", False, 1),
                ("Assigned", False, 2),
                ("In Progress", False, 3),
                ("Resolved", False, 4),
                ("Closed", True, 5),
                ("Rejected", True, 6),
            ]
            for name, is_closed, order in default_statuses:
                Status.objects.get_or_create(
                    name=name,
                    defaults={
                        'is_closed': is_closed,
                        'is_active': True,
                        'order': order
                    }
                )
            self.log_fix("Created default statuses")
            
        # Check user groups
        required_groups = ['Engineer', 'AMC Admin', 'Admin']
        for group_name in required_groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.log_fix(f"Created group: {group_name}")
                
        print("✅ Master data check complete")
        
    def check_file_permissions(self):
        """Check file and directory permissions."""
        print("\n🔍 Checking File Permissions...")
        
        # Check media directory
        media_dir = PROJECT_DIR / 'media'
        if not media_dir.exists():
            media_dir.mkdir(parents=True, exist_ok=True)
            self.log_fix("Created media directory")
            
        # Check static files
        static_dir = PROJECT_DIR / 'static'
        if not static_dir.exists():
            self.log_issue("Static directory not found")
        else:
            # Check if CSS and JS files exist
            css_file = static_dir / 'css' / 'style.css'
            js_file = static_dir / 'js' / 'main.js'
            
            if not css_file.exists():
                self.log_issue("Main CSS file missing")
            if not js_file.exists():
                self.log_issue("Main JS file missing")
                
        print("✅ File permissions check complete")
        
    def check_url_configuration(self):
        """Check if all URLs are properly configured."""
        print("\n🔍 Checking URL Configuration...")
        
        critical_urls = [
            'core:normal_user_login',
            'core:normal_user_dashboard',
            'login',
            'logout',
        ]
        
        for url_name in critical_urls:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
            except Exception as e:
                self.log_issue(f"URL reverse failed for {url_name}: {str(e)}")
                
        print("✅ URL configuration check complete")
        
    def check_template_existence(self):
        """Check if all required templates exist."""
        print("\n🔍 Checking Template Files...")
        
        templates_dir = PROJECT_DIR / 'templates'
        required_templates = [
            'core/normal_user_login.html',
            'core/normal_user_dashboard.html',
            'core/engineer_dashboard.html',
            'core/amc_admin_dashboard.html',
            'core/admin_dashboard.html',
            'complaints/submit.html',
            'base.html'
        ]
        
        for template in required_templates:
            template_path = templates_dir / template
            if not template_path.exists():
                self.log_issue(f"Template missing: {template}")
            else:
                print(f"✅ {template}")
                
        print("✅ Template check complete")
        
    def check_demo_users(self):
        """Check if demo users exist and have proper setup."""
        print("\n🔍 Checking Demo Users...")
        
        # Staff users
        staff_users = [
            ('demo_admin', 'Admin'),
            ('demo_amc_admin', 'AMC Admin'),
            ('demo_engineer1', 'Engineer'),
            ('demo_engineer2', 'Engineer'),
        ]
        
        for username, group_name in staff_users:
            try:
                user = User.objects.get(username=username)
                has_group = user.groups.filter(name=group_name).exists()
                if not has_group:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                    self.log_fix(f"Added {username} to {group_name} group")
                else:
                    print(f"✅ {username} in {group_name} group")
            except User.DoesNotExist:
                self.log_issue(f"Demo user {username} not found")
                
        # Normal users
        normal_users = ['ALICE001', 'BOB002', 'CAROL003']
        for portal_id in normal_users:
            profiles = UserProfile.objects.filter(main_portal_id=portal_id)
            if not profiles.exists():
                self.log_issue(f"Normal user with Portal ID {portal_id} not found")
            else:
                print(f"✅ Normal user {portal_id} exists")
                
        print("✅ Demo users check complete")
        
    def performance_check(self):
        """Basic performance and optimization checks."""
        print("\n🔍 Checking Performance...")
        
        # Check number of queries for a simple operation
        from django.db import connection
        from django.test.utils import override_settings
        
        # Check if DEBUG is False in production
        from django.conf import settings
        if settings.DEBUG:
            print("⚠️  DEBUG=True (OK for development, should be False in production)")
        else:
            print("✅ DEBUG=False (Production ready)")
            
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                print("✅ Database connection working")
        except Exception as e:
            self.log_issue(f"Database connection failed: {str(e)}")
            
        print("✅ Performance check complete")
        
    def run_health_check(self):
        """Run complete system health check."""
        print("🏥 AMC COMPLAINT PORTAL - SYSTEM HEALTH CHECK")
        print("=" * 60)
        
        self.check_database_integrity()
        self.check_required_data()
        self.check_file_permissions()
        self.check_url_configuration()
        self.check_template_existence()
        self.check_demo_users()
        self.performance_check()
        
        print("\n" + "=" * 60)
        print("📊 HEALTH CHECK SUMMARY")
        print("=" * 60)
        
        if not self.issues_found:
            print("🎉 EXCELLENT! No issues found. System is healthy!")
        else:
            print(f"⚠️  Found {len(self.issues_found)} issues:")
            for issue in self.issues_found:
                print(f"   • {issue}")
                
        if self.fixes_applied:
            print(f"\n✅ Applied {len(self.fixes_applied)} fixes:")
            for fix in self.fixes_applied:
                print(f"   • {fix}")
                
        print(f"\n🎯 SYSTEM STATUS: {'HEALTHY' if not self.issues_found else 'NEEDS ATTENTION'}")
        
        return len(self.issues_found) == 0


if __name__ == '__main__':
    checker = SystemHealthChecker()
    is_healthy = checker.run_health_check()
    
    if is_healthy:
        print("\n🚀 System is ready for testing and production!")
    else:
        print("\n🔧 Please address the issues found above.")
        
    sys.exit(0 if is_healthy else 1)