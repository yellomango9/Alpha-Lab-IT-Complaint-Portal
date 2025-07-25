"""
Admin configuration for the reports app.
Provides admin interface for managing report templates and generated reports.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import ReportTemplate, GeneratedReport, ReportSchedule


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for ReportTemplate model."""
    list_display = [
        'name', 'report_type', 'is_scheduled', 'schedule_frequency', 
        'is_active', 'created_by', 'created_at'
    ]
    list_filter = ['report_type', 'is_scheduled', 'schedule_frequency', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'report_type', 'description')
        }),
        ('Configuration', {
            'fields': ('config',),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('is_scheduled', 'schedule_frequency', 'email_recipients')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ['created_by']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    """Admin configuration for GeneratedReport model."""
    list_display = [
        'template', 'date_range_display', 'generated_by', 
        'generated_at', 'has_files', 'file_size_display'
    ]
    list_filter = ['template', 'generated_at', 'generated_by']
    search_fields = ['template__name']
    ordering = ['-generated_at']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('template', 'date_from', 'date_to', 'filters')
        }),
        ('Generated Files', {
            'fields': ('pdf_file', 'csv_file', 'file_size'),
            'classes': ('collapse',)
        }),
        ('Data', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('generated_by', 'generated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['generated_by', 'generated_at', 'file_size']
    
    def has_files(self, obj):
        """Check if report has generated files."""
        has_pdf = bool(obj.pdf_file)
        has_csv = bool(obj.csv_file)
        
        if has_pdf and has_csv:
            return format_html('<span style="color: green;">✓ PDF & CSV</span>')
        elif has_pdf:
            return format_html('<span style="color: blue;">✓ PDF</span>')
        elif has_csv:
            return format_html('<span style="color: orange;">✓ CSV</span>')
        else:
            return format_html('<span style="color: red;">✗ No files</span>')
    
    has_files.short_description = 'Files'
    
    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        if obj.file_size == 0:
            return '-'
        
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    file_size_display.short_description = 'File Size'


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    """Admin configuration for ReportSchedule model."""
    list_display = [
        'template', 'next_run', 'last_run', 'run_count', 
        'is_active', 'has_errors'
    ]
    list_filter = ['is_active', 'template__report_type', 'next_run', 'last_run']
    search_fields = ['template__name']
    ordering = ['next_run']
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('template', 'is_active')
        }),
        ('Timing', {
            'fields': ('next_run', 'last_run', 'run_count')
        }),
        ('Error Tracking', {
            'fields': ('last_error',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['last_run', 'run_count']
    
    def has_errors(self, obj):
        """Check if schedule has recent errors."""
        if obj.last_error:
            return format_html('<span style="color: red;">✗ Has errors</span>')
        return format_html('<span style="color: green;">✓ No errors</span>')
    
    has_errors.short_description = 'Status'