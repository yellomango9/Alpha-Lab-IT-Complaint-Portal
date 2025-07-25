from django.db import models
from django.contrib.auth.models import User


class FAQCategory(models.Model):
    """Categories for organizing FAQs."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'FAQ Category'
        verbose_name_plural = 'FAQ Categories'

    def __str__(self):
        return self.name


class FAQ(models.Model):
    """Frequently Asked Questions model."""
    category = models.ForeignKey(
        FAQCategory, 
        on_delete=models.CASCADE, 
        related_name='faqs',
        null=True,
        blank=True
    )
    question = models.CharField(max_length=512, help_text="The question being asked")
    answer = models.TextField(help_text="Detailed answer to the question")
    
    # Metadata
    is_featured = models.BooleanField(default=False, help_text="Show in featured FAQs")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order within category")
    
    # Tracking
    view_count = models.PositiveIntegerField(default=0, help_text="Number of times this FAQ was viewed")
    helpful_count = models.PositiveIntegerField(default=0, help_text="Number of users who found this helpful")
    
    # Authorship
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_faqs'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='updated_faqs'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__order', 'order', 'question']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question

    def increment_view_count(self):
        """Increment the view count for this FAQ."""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def mark_helpful(self):
        """Increment the helpful count for this FAQ."""
        self.helpful_count += 1
        self.save(update_fields=['helpful_count'])
