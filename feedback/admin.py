from django.contrib import admin
from django.utils.html import format_html
from .models import Feedback, FeedbackTemplate


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Admin configuration for Feedback model."""
    list_display = [
        'complaint', 'user', 'template', 'rating_display', 'submitted_at'
    ]
    list_filter = [
        'template', 'submitted_at'
    ]
    search_fields = [
        'complaint__title', 'user__username', 'comment'
    ]
    ordering = ['-submitted_at']
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Feedback Information', {
            'fields': ('complaint', 'user', 'template')
        }),
        ('Responses', {
            'fields': ('responses', 'comment')
        }),
        ('Timestamps', {
            'fields': ('submitted_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['submitted_at']
    
    def rating_display(self, obj):
        """Display overall rating as stars."""
        rating = obj.overall_rating
        if rating is None:
            return "No rating"
        
        full_stars = int(rating)
        stars = "★" * full_stars + "☆" * (5 - full_stars)
        return format_html('<span style="color: gold; font-size: 16px;">{}</span>', stars)
    rating_display.short_description = 'Overall Rating'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('complaint', 'user', 'template')


@admin.register(FeedbackTemplate)
class FeedbackTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for Feedback Template model."""
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Questions', {
            'fields': ('questions',),
            'description': 'JSON format: [{"key": "field_name", "label": "Question text", "type": "rating|text|boolean|textarea", "required": true/false}]'
        }),
    )
