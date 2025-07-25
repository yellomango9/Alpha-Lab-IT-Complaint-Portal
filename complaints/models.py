import os
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
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
    resolution_notes = models.TextField(blank=True, help_text="Notes about how the issue was resolved")
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

    def mark_resolved(self, resolution_notes="", resolved_by=None):
        """Mark complaint as resolved."""
        resolved_status = Status.objects.filter(is_closed=True).first()
        if resolved_status:
            self.status = resolved_status
            self.resolved_at = timezone.now()
            if resolution_notes:
                self.resolution_notes = resolution_notes
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


class ComplaintMetrics(models.Model):
    """
    Model to store pre-calculated metrics for reporting performance.
    Updated via signals when complaints are created/updated.
    """
    date = models.DateField(unique=True, help_text="Date for these metrics")
    
    # Daily counts
    total_complaints = models.PositiveIntegerField(default=0)
    new_complaints = models.PositiveIntegerField(default=0)
    resolved_complaints = models.PositiveIntegerField(default=0)
    closed_complaints = models.PositiveIntegerField(default=0)
    
    # Resolution metrics
    avg_resolution_time_hours = models.FloatField(
        null=True, 
        blank=True,
        help_text="Average time to resolve complaints in hours"
    )
    
    # Department breakdown (JSON field for flexibility)
    department_stats = models.JSONField(
        default=dict,
        help_text="Breakdown of complaints by department"
    )
    type_stats = models.JSONField(
        default=dict,
        help_text="Breakdown of complaints by type"
    )
    urgency_stats = models.JSONField(
        default=dict,
        help_text="Breakdown of complaints by urgency"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Complaint Metrics'
        verbose_name_plural = 'Complaint Metrics'

    def __str__(self):
        return f"Metrics for {self.date}: {self.total_complaints} complaints"
