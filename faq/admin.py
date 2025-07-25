from django.contrib import admin
from django.utils.html import format_html
from .models import FAQ, FAQCategory


@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for FAQ Category model."""
    list_display = ['name', 'order', 'is_active', 'faq_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'order', 'is_active')
        }),
    )
    
    def faq_count(self, obj):
        count = obj.faqs.filter(is_active=True).count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    faq_count.short_description = 'Active FAQs'


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin configuration for FAQ model."""
    list_display = [
        'question', 'category', 'is_featured', 'is_active', 
        'view_count', 'helpful_count', 'created_at'
    ]
    list_filter = [
        'category', 'is_featured', 'is_active', 'created_at',
        'created_by', 'updated_by'
    ]
    search_fields = ['question', 'answer']
    ordering = ['category__order', 'order', 'question']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('FAQ Content', {
            'fields': ('category', 'question', 'answer')
        }),
        ('Settings', {
            'fields': ('is_featured', 'is_active', 'order')
        }),
        ('Statistics', {
            'fields': ('view_count', 'helpful_count'),
            'classes': ('collapse',)
        }),
        ('Authorship', {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['view_count', 'helpful_count', 'created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new FAQ
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'created_by', 'updated_by'
        )
