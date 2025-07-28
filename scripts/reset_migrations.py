#!/usr/bin/env python
"""
Script to reset and recreate migrations for the AMC Complaint Portal.
This should be run when there are migration conflicts or when setting up fresh.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from django.conf import settings

def reset_migrations():
    """Reset all migrations and recreate them."""
    
    print("🔄 Resetting migrations for AMC Complaint Portal...")
    
    # Apps to reset
    apps = ['core', 'complaints', 'faq', 'feedback']
    
    # Remove existing migration files (except __init__.py)
    for app in apps:
        migrations_dir = project_root / app / 'migrations'
        if migrations_dir.exists():
            for file in migrations_dir.glob('*.py'):
                if file.name != '__init__.py':
                    print(f"  Removing {file}")
                    file.unlink()
    
    print("\n📝 Creating fresh migrations...")
    
    # Create new migrations
    try:
        execute_from_command_line(['manage.py', 'makemigrations', 'core'])
        execute_from_command_line(['manage.py', 'makemigrations', 'complaints'])
        execute_from_command_line(['manage.py', 'makemigrations', 'faq'])
        execute_from_command_line(['manage.py', 'makemigrations', 'feedback'])
        
        print("✅ Migrations created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating migrations: {e}")
        return False
    
    return True

def create_initial_data():
    """Create initial data for the system."""
    
    print("\n🌱 Creating initial data...")
    
    from django.contrib.auth.models import User
    from core.models import Department, Role
    from complaints.models import Status, ComplaintType
    from faq.models import FAQCategory
    
    # Create departments
    departments = [
        {'name': 'Information Technology', 'description': 'IT Support and Infrastructure'},
        {'name': 'Human Resources', 'description': 'HR Department'},
        {'name': 'Finance', 'description': 'Finance Department'},
        {'name': 'Operations', 'description': 'Operations Department'},
    ]
    
    for dept_data in departments:
        dept, created = Department.objects.get_or_create(
            name=dept_data['name'],
            defaults={'description': dept_data['description']}
        )
        if created:
            print(f"  Created department: {dept.name}")
    
    # Create roles
    roles = [
        {'name': 'User', 'description': 'Regular system user'},
        {'name': 'IT Engineer', 'description': 'IT support engineer'},
        {'name': 'IT Manager', 'description': 'IT department manager'},
        {'name': 'Administrator', 'description': 'System administrator'},
    ]
    
    for role_data in roles:
        role, created = Role.objects.get_or_create(
            name=role_data['name'],
            defaults={'description': role_data['description']}
        )
        if created:
            print(f"  Created role: {role.name}")
    
    # Create complaint statuses
    statuses = [
        {'name': 'Open', 'description': 'Complaint submitted and awaiting review', 'order': 1, 'is_closed': False},
        {'name': 'In Progress', 'description': 'Complaint is being worked on', 'order': 2, 'is_closed': False},
        {'name': 'Pending User', 'description': 'Waiting for user response', 'order': 3, 'is_closed': False},
        {'name': 'Resolved', 'description': 'Complaint has been resolved', 'order': 4, 'is_closed': True},
        {'name': 'Closed', 'description': 'Complaint is closed', 'order': 5, 'is_closed': True},
    ]
    
    for status_data in statuses:
        status, created = Status.objects.get_or_create(
            name=status_data['name'],
            defaults=status_data
        )
        if created:
            print(f"  Created status: {status.name}")
    
    # Create complaint types
    complaint_types = [
        {'name': 'Hardware Issue', 'description': 'Problems with computer hardware'},
        {'name': 'Software Issue', 'description': 'Problems with software applications'},
        {'name': 'Network Issue', 'description': 'Internet or network connectivity problems'},
        {'name': 'Email Issue', 'description': 'Email-related problems'},
        {'name': 'Printer Issue', 'description': 'Printer and printing problems'},
        {'name': 'Account Access', 'description': 'Login or account access issues'},
        {'name': 'Other', 'description': 'Other IT-related issues'},
    ]
    
    for type_data in complaint_types:
        comp_type, created = ComplaintType.objects.get_or_create(
            name=type_data['name'],
            defaults={'description': type_data['description']}
        )
        if created:
            print(f"  Created complaint type: {comp_type.name}")
    
    # Create FAQ categories
    faq_categories = [
        {'name': 'General', 'description': 'General questions', 'order': 1},
        {'name': 'Hardware', 'description': 'Hardware-related questions', 'order': 2},
        {'name': 'Software', 'description': 'Software-related questions', 'order': 3},
        {'name': 'Network', 'description': 'Network-related questions', 'order': 4},
        {'name': 'Account', 'description': 'Account and access questions', 'order': 5},
    ]
    
    for cat_data in faq_categories:
        category, created = FAQCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        if created:
            print(f"  Created FAQ category: {category.name}")
    
    print("✅ Initial data created successfully!")

if __name__ == '__main__':
    if reset_migrations():
        create_initial_data()
        print("\n🎉 Migration reset and initial data setup completed!")
        print("\nNext steps:")
        print("1. Run: python manage.py migrate")
        print("2. Run: python manage.py createsuperuser")
        print("3. Start the development server: python manage.py runserver")
    else:
        print("\n❌ Migration reset failed!")
        sys.exit(1)