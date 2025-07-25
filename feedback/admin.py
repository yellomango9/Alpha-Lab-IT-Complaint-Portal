from django.contrib import admin
from django.utils.html import format_html
from .models import Feedback, FeedbackTemplate


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Admin configuration for Feedback model."""
    list_display = [
        'complaint', 'user', 'rating_display', 'rating', 
        'is_anonymous', 'is_public', 'submitted_at'
    ]
    list_filter = [
        'rating', 'is_anonymous', 'is_public', 'submitted_at',
        'would_recommend'
    ]
    search_fields = [
        'complaint__title', 'user__username', 'comment', 'suggestions'
    ]
    ordering = ['-submitted_at']
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Feedback Information', {
            'fields': ('complaint', 'user', 'rating')
        }),
        ('Detailed Ratings', {
            'fields': ('resolution_quality', 'response_time', 'staff_helpfulness'),
            'classes': ('collapse',)
        }),
        ('Comments', {
            'fields': ('comment', 'suggestions')
        }),
        ('Additional Questions', {
            'fields': ('would_recommend',),
            'classes': ('collapse',)
        }),
        ('Privacy Settings', {
            'fields': ('is_anonymous', 'is_public')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['submitted_at', 'updated_at']
    
    def rating_display(self, obj):
        stars = "★" * obj.rating + "☆" * (5 - obj.rating)
        return format_html('<span style="color: gold; font-size: 16px;">{}</span>', stars)
    rating_display.short_description = 'Rating'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('complaint', 'user')


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
            'description': 'JSON format: [{"question": "...", "type": "rating|text|boolean"}]'
        }),
    )
