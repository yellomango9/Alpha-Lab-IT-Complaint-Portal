"""
Reports app models for generating and storing report data.
Provides functionality for complaint analytics and reporting.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta


class ReportTemplate(models.Model):
    """
    Template for generating different types of reports.
    Allows admins to create custom report configurations.
    """
    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('custom', 'Custom Date Range'),
        ('department', 'Department Analysis'),
        ('performance', 'Performance Metrics'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Report configuration (JSON field for flexibility)
    config = models.JSONField(
        default=dict,
        help_text="Configuration parameters for this report type"
    )
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        blank=True,
        null=True
    )
    
    # Recipients
    email_recipients = models.TextField(
        blank=True,
        help_text="Comma-separated list of email addresses"
    )
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Report Template'
        verbose_name_plural = 'Report Templates'

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class GeneratedReport(models.Model):
    """
    Stores generated reports for caching and historical purposes.
    Allows users to download previously generated reports.
    """
    template = models.ForeignKey(
        ReportTemplate, 
        on_delete=models.CASCADE,
        related_name='generated_reports'
    )
    
    # Report parameters
    date_from = models.DateField()
    date_to = models.DateField()
    filters = models.JSONField(
        default=dict,
        help_text="Filters applied when generating this report"
    )
    
    # Report data
    data = models.JSONField(
        default=dict,
        help_text="Generated report data in JSON format"
    )
    
    # File exports
    pdf_file = models.FileField(
        upload_to='reports/pdf/',
        blank=True,
        null=True,
        help_text="PDF version of the report"
    )
    csv_file = models.FileField(
        upload_to='reports/csv/',
        blank=True,
        null=True,
        help_text="CSV version of the report"
    )
    
    # Metadata
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(default=0, help_text="Total file size in bytes")
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Generated Report'
        verbose_name_plural = 'Generated Reports'

    def __str__(self):
        return f"{self.template.name} - {self.date_from} to {self.date_to}"

    @property
    def date_range_display(self):
        """Return formatted date range."""
        if self.date_from == self.date_to:
            return self.date_from.strftime('%B %d, %Y')
        return f"{self.date_from.strftime('%B %d, %Y')} - {self.date_to.strftime('%B %d, %Y')}"


class ReportSchedule(models.Model):
    """
    Manages scheduled report generation and delivery.
    Handles automatic report generation based on templates.
    """
    template = models.OneToOneField(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name='schedule'
    )
    
    # Scheduling details
    next_run = models.DateTimeField()
    last_run = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    run_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Report Schedule'
        verbose_name_plural = 'Report Schedules'

    def __str__(self):
        return f"Schedule for {self.template.name}"

    def calculate_next_run(self):
        """Calculate the next run time based on frequency."""
        if not self.template.schedule_frequency:
            return None
        
        now = timezone.now()
        
        if self.template.schedule_frequency == 'daily':
            return now + timedelta(days=1)
        elif self.template.schedule_frequency == 'weekly':
            return now + timedelta(weeks=1)
        elif self.template.schedule_frequency == 'monthly':
            # Add one month (approximate)
            return now + timedelta(days=30)
        
        return None

    def update_next_run(self):
        """Update the next run time."""
        self.next_run = self.calculate_next_run()
        self.save(update_fields=['next_run'])