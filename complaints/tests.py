"""
Comprehensive test suite for the complaints app.
Tests models, views, forms, and business logic.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta

from .models import Complaint, ComplaintType, Status, FileAttachment
from .forms import ComplaintForm, ComplaintUpdateForm
from core.models import Department, Role, UserProfile


class ComplaintModelTest(TestCase):
    """Test cases for Complaint model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.department = Department.objects.create(
            name='IT Department',
            description='Information Technology'
        )
        
        self.complaint_type = ComplaintType.objects.create(
            name='Hardware Issue',
            description='Hardware problems'
        )
        
        self.status = Status.objects.create(
            name='Open',
            description='New complaint',
            order=1
        )
    
    def test_complaint_creation(self):
        """Test complaint creation."""
        complaint = Complaint.objects.create(
            user=self.user,
            type=self.complaint_type,
            status=self.status,
            title='Test Complaint',
            description='This is a test complaint',
            urgency='medium'
        )
        
        self.assertEqual(complaint.user, self.user)
        self.assertEqual(complaint.title, 'Test Complaint')
        self.assertEqual(complaint.urgency, 'medium')
        self.assertIsNotNone(complaint.created_at)
        self.assertIsNotNone(complaint.updated_at)
    
    def test_complaint_str_method(self):
        """Test complaint string representation."""
        complaint = Complaint.objects.create(
            user=self.user,
            type=self.complaint_type,
            status=self.status,
            title='Test Complaint',
            description='Test description'
        )
        
        expected_str = f"#{complaint.id} - Test Complaint"
        self.assertEqual(str(complaint), expected_str)
    
    def test_is_resolved_property(self):
        """Test is_resolved property."""
        # Create closed status
        closed_status = Status.objects.create(
            name='Resolved',
            description='Complaint resolved',
            order=2,
            is_closed=True
        )
        
        complaint = Complaint.objects.create(
            user=self.user,
            type=self.complaint_type,
            status=self.status,
            title='Test Complaint',
            description='Test description'
        )
        
        # Initially not resolved
        self.assertFalse(complaint.is_resolved)
        
        # Mark as resolved
        complaint.status = closed_status
        complaint.save()
        
        self.assertTrue(complaint.is_resolved)