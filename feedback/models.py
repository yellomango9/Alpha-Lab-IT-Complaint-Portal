from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from complaints.models import Complaint


class Feedback(models.Model):
    """Model for collecting user feedback on resolved complaints."""
    
    complaint = models.OneToOneField(
        Complaint, 
        on_delete=models.CASCADE, 
        related_name='feedback',
        help_text="The complaint this feedback is for"
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text="User who submitted the feedback"
    )
    
    # Rating and Comments
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 (Poor) to 5 (Excellent)"
    )
    comment = models.TextField(
        blank=True, 
        max_length=1000,
        help_text="Optional comments about the resolution"
    )
    
    # Specific feedback areas
    resolution_quality = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How satisfied are you with the resolution quality?",
        null=True,
        blank=True
    )
    response_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How satisfied are you with the response time?",
        null=True,
        blank=True
    )
    staff_helpfulness = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How helpful was the IT staff?",
        null=True,
        blank=True
    )
    
    # Additional feedback
    would_recommend = models.BooleanField(
        null=True,
        blank=True,
        help_text="Would you recommend our IT support to others?"
    )
    suggestions = models.TextField(
        blank=True,
        max_length=500,
        help_text="Any suggestions for improvement?"
    )
    
    # Metadata
    is_anonymous = models.BooleanField(
        default=False,
        help_text="Keep this feedback anonymous"
    )
    is_public = models.BooleanField(
        default=False,
        help_text="Allow this feedback to be displayed publicly"
    )
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedback'

    def __str__(self):
        return f"Feedback for Complaint #{self.complaint.id} - {self.rating}/5 stars"

    @property
    def rating_display(self):
        """Return star rating display."""
        return "★" * self.rating + "☆" * (5 - self.rating)

    @property
    def average_detailed_rating(self):
        """Calculate average of detailed ratings."""
        ratings = [
            self.resolution_quality,
            self.response_time,
            self.staff_helpfulness
        ]
        valid_ratings = [r for r in ratings if r is not None]
        if valid_ratings:
            return sum(valid_ratings) / len(valid_ratings)
        return None


class FeedbackTemplate(models.Model):
    """Template for feedback questions and categories."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    questions = models.JSONField(
        default=list,
        help_text="List of questions for this feedback template"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Feedback Template'
        verbose_name_plural = 'Feedback Templates'

    def __str__(self):
        return self.name
