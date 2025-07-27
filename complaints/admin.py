from django.contrib import admin
from django.utils.html import format_html
from .models import Complaint, ComplaintType, Status, FileAttachment, Remark


class FileAttachmentInline(admin.TabularInline):
    """Inline admin for file attachments."""
    model = FileAttachment
    extra = 0
    readonly_fields = ['original_filename', 'file_size_formatted', 'uploaded_at', 'uploaded_by']
    
    def file_size_formatted(self, obj):
        return obj.file_size_formatted if obj else '-'
    file_size_formatted.short_description = 'File Size'


class RemarkInline(admin.TabularInline):
    """Inline admin for remarks."""
    model = Remark
    extra = 0
    readonly_fields = ['created_at']
    fields = ['user', 'text', 'is_internal_note', 'created_at']


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    """Admin configuration for Complaint model."""
    list_display = [
        'id', 'title', 'user', 'type', 'status', 'urgency', 
        'assigned_to', 'created_at', 'is_resolved'
    ]
    list_filter = [
        'status', 'type', 'urgency', 'created_at', 
        'resolved_at', 'assigned_to'
    ]
    search_fields = [
        'title', 'description', 'user__username', 
        'user__first_name', 'user__last_name'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    inlines = [FileAttachmentInline, RemarkInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'type', 'status', 'assigned_to')
        }),
        ('Complaint Details', {
            'fields': ('title', 'description', 'urgency', 'location', 'contact_number')
        }),
        ('Resolution', {
            'fields': ('resolved_at',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def is_resolved(self, obj):
        if obj.status and obj.status.is_closed:
            return format_html('<span style="color: green;">✓ Resolved</span>')
        return format_html('<span style="color: orange;">⏳ Open</span>')
    is_resolved.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'user', 'type', 'status', 'assigned_to'
        )


@admin.register(ComplaintType)
class ComplaintTypeAdmin(admin.ModelAdmin):
    """Admin configuration for ComplaintType model."""
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
    )


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    """Admin configuration for Status model."""
    list_display = ['name', 'order', 'is_active', 'is_closed', 'created_at']
    list_filter = ['is_active', 'is_closed', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'order')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_closed')
        }),
    )


@admin.register(FileAttachment)
class FileAttachmentAdmin(admin.ModelAdmin):
    """Admin configuration for FileAttachment model."""
    list_display = [
        'original_filename', 'complaint', 'file_size_formatted', 
        'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['content_type', 'uploaded_at']
    search_fields = [
        'original_filename', 'complaint__title', 
        'uploaded_by__username'
    ]
    ordering = ['-uploaded_at']
    readonly_fields = ['file_size_formatted', 'uploaded_at']
    
    def file_size_formatted(self, obj):
        return obj.file_size_formatted if obj else '-'
    file_size_formatted.short_description = 'File Size'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'complaint', 'uploaded_by'
        )


@admin.register(Remark)
class RemarkAdmin(admin.ModelAdmin):
    """Admin configuration for Remark model."""
    list_display = [
        'complaint', 'user', 'text_preview', 'is_internal_note', 'created_at'
    ]
    list_filter = ['is_internal_note', 'created_at']
    search_fields = [
        'text', 'complaint__title', 'user__username'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'complaint', 'user'
        )
