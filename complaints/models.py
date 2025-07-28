import os
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Department


def complaint_file_upload_path(instance, filename):
    """Generate upload path for complaint attachments."""
    return f'complaints/{instance.complaint.id}/{filename}'


class ComplaintType(models.Model):
    """Model for categorizing different types of IT complaints."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, help_text="Optional description of this complaint type")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Complaint Type'
        verbose_name_plural = 'Complaint Types'

    def __str__(self):
        return self.name


class Status(models.Model):
    """Model for tracking complaint status progression."""
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Normal'),
        (3, 'High'),
        (4, 'Critical'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_closed = models.BooleanField(default=False, help_text="Mark as True if this status indicates complaint is closed")
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Statuses'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Complaint(models.Model):
    """Main model for IT complaints submitted by users."""
    URGENCY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    # Basic Information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='complaints',
        help_text="User who submitted the complaint"
    )
    type = models.ForeignKey(ComplaintType, on_delete=models.PROTECT, verbose_name="Complaint Type")
    status = models.ForeignKey(Status, on_delete=models.PROTECT, default=1)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_complaints',
        help_text="Engineer assigned to handle this complaint"
    )
    
    # Complaint Details
    title = models.CharField(max_length=255, help_text="Brief title describing the issue")
    description = models.TextField(help_text="Detailed description of the problem")
    urgency = models.CharField(
        max_length=10, 
        choices=URGENCY_CHOICES, 
        default='medium',
        help_text="How urgent is this issue?"
    )
    
    # Location and Contact
    location = models.CharField(max_length=255, blank=True, help_text="Physical location where issue occurred")
    contact_number = models.CharField(max_length=20, blank=True, help_text="Alternative contact number")
    
    # Resolution
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'

    def __str__(self):
        return f"#{self.id} - {self.title}"

    def get_absolute_url(self):
        return reverse('complaints:detail', kwargs={'pk': self.pk})

    @property
    def is_resolved(self):
        """Check if complaint is in a resolved status."""
        return self.status.is_closed if self.status else False

    @property
    def days_open(self):
        """Calculate how many days the complaint has been open."""
        end_date = self.resolved_at or timezone.now()
        return (end_date - self.created_at).days

    def mark_resolved(self, resolved_by=None):
        """Mark complaint as resolved."""
        resolved_status = Status.objects.filter(is_closed=True).first()
        if resolved_status:
            self.status = resolved_status
            self.resolved_at = timezone.now()
            self.save()


class FileAttachment(models.Model):
    """Model for file attachments related to complaints."""
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=complaint_file_upload_path, max_length=500)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    content_type = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        help_text="User who uploaded this file"
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'File Attachment'
        verbose_name_plural = 'File Attachments'

    def __str__(self):
        return f"{self.original_filename} - Complaint #{self.complaint.id}"

    @property
    def file_size_formatted(self):
        """Return human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def delete(self, *args, **kwargs):
        """Override delete to remove file from filesystem."""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class Remark(models.Model):
    """
    Stores a single comment or action log in a complaint's conversation thread.
    
    This model enables threaded conversations on complaints, allowing users and IT staff
    to communicate about the complaint resolution process. Remarks can be either public
    (visible to the complaint submitter) or internal notes (visible only to IT staff).
    """
    complaint = models.ForeignKey(
        'Complaint', 
        on_delete=models.CASCADE, 
        related_name='remarks',
        help_text="The complaint this remark belongs to"
    )
    user = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="The user who made the remark"
    )
    text = models.TextField(
        help_text="The content of the remark"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the remark was created"
    )
    is_internal_note = models.BooleanField(
        default=False,
        help_text="True if this note is only visible to internal IT staff"
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Remark'
        verbose_name_plural = 'Remarks'

    def __str__(self):
        user_name = self.user.get_full_name() or self.user.username if self.user else "System"
        note_type = " (Internal)" if self.is_internal_note else ""
        return f"Remark by {user_name} on Complaint #{self.complaint.id}{note_type}"

    @property
    def is_system_remark(self):
        """
        Check if this is a system-generated remark.
        
        Returns:
            bool: True if the remark was created by the system (no user)
        """
        return self.user is None


class StatusHistory(models.Model):
    """
    Model to track detailed history of complaint status changes.
    Provides audit trail for all status transitions with timestamps and user info.
    """
    complaint = models.ForeignKey(
        Complaint, 
        on_delete=models.CASCADE, 
        related_name='status_history',
        help_text="The complaint this status change belongs to"
    )
    previous_status = models.ForeignKey(
        Status, 
        on_delete=models.PROTECT, 
        related_name='previous_status_changes',
        null=True, 
        blank=True,
        help_text="Previous status before this change"
    )
    new_status = models.ForeignKey(
        Status, 
        on_delete=models.PROTECT, 
        related_name='new_status_changes',
        help_text="New status after this change"
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        help_text="User who made this status change"
    )
    notes = models.TextField(
        blank=True, 
        help_text="Optional notes about why the status was changed"
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Status History'
        verbose_name_plural = 'Status Histories'

    def __str__(self):
        return f"Complaint #{self.complaint.id}: {self.previous_status} → {self.new_status}"


class ComplaintFeedback(models.Model):
    """
    Model to store user feedback when they close a resolved complaint.
    This helps track user satisfaction with the IT support.
    """
    complaint = models.OneToOneField(
        Complaint, 
        on_delete=models.CASCADE, 
        related_name='user_feedback',
        help_text="The complaint this feedback is for"
    )
    rating = models.IntegerField(
        choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')],
        help_text="User rating from 1 to 5 stars"
    )
    feedback_text = models.TextField(
        blank=True,
        help_text="User's detailed feedback"
    )
    is_satisfied = models.BooleanField(
        default=True,
        help_text="Whether user is satisfied with the resolution"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the feedback was submitted"
    )

    class Meta:
        verbose_name = 'Complaint Feedback'
        verbose_name_plural = 'Complaint Feedback'

    def __str__(self):
        return f"Feedback for Complaint #{self.complaint.id} - Rating: {self.rating}/5"

    @property
    def rating_text(self):
        """Return human-readable rating text."""
        ratings = {
            1: 'Very Unhappy',
            2: 'Unhappy', 
            3: 'Neutral',
            4: 'Happy',
            5: 'Very Happy'
        }
        return ratings.get(self.rating, 'Unknown')


class ComplaintClosing(models.Model):
    """
    Model to track complaint closing details and user satisfaction.
    """
    complaint = models.OneToOneField(
        Complaint, 
        on_delete=models.CASCADE, 
        related_name='closing_details',
        help_text="The complaint being closed"
    )
    closed_by_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='staff_closings',
        help_text="Staff member who closed the complaint"
    )
    staff_closing_remark = models.TextField(
        help_text="Staff remark when closing the complaint"
    )
    staff_closed_at = models.DateTimeField(auto_now_add=True)
    
    # User response after staff closes
    user_satisfied = models.BooleanField(
        null=True,
        blank=True,
        help_text="True if user is satisfied, False if not satisfied, None if no response yet"
    )
    user_closing_remark = models.TextField(
        blank=True,
        help_text="User's remark if not satisfied"
    )
    user_closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user finally closed the complaint"
    )

    class Meta:
        verbose_name = 'Complaint Closing'
        verbose_name_plural = 'Complaint Closings'

    def __str__(self):
        return f"Closing for Complaint #{self.complaint.id}"


class ComplaintFeedback(models.Model):
    """
    Model to store user feedback when closing a complaint
    """
    complaint = models.OneToOneField(
        'Complaint',
        on_delete=models.CASCADE,
        related_name='user_feedback',
        help_text="The complaint this feedback is for"
    )
    rating = models.IntegerField(
        choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)],
        help_text="User rating from 1 to 5 stars"
    )
    feedback_text = models.TextField(
        blank=True,
        help_text="User's detailed feedback"
    )
    is_satisfied = models.BooleanField(
        default=True,
        help_text="Whether user is satisfied with the resolution"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the feedback was submitted"
    )

    class Meta:
        verbose_name = 'Complaint Feedback'
        verbose_name_plural = 'Complaint Feedbacks'

    def __str__(self):
        return f"Feedback for Complaint #{self.complaint.id} - {self.rating} stars"


class ComplaintRemark(models.Model):
    """
    Model to store user remarks when not satisfied with resolution
    """
    complaint = models.ForeignKey(
        'Complaint',
        on_delete=models.CASCADE,
        related_name='user_remarks',
        help_text="The complaint this remark is for"
    )
    remark = models.TextField(
        help_text="User's remark about the resolution"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the remark was added"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User who created the remark"
    )
    is_read_by_engineer = models.BooleanField(
        default=False,
        help_text="Whether the assigned engineer has read this remark"
    )

    class Meta:
        verbose_name = 'Complaint Remark'
        verbose_name_plural = 'Complaint Remarks'
        ordering = ['-created_at']

    def __str__(self):
        return f"Remark for Complaint #{self.complaint.id} by {self.created_by.username}"



