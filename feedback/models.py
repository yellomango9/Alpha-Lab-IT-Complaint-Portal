from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from complaints.models import Complaint


class Feedback(models.Model):
    """
    Stores user feedback for a resolved complaint, with dynamic responses.
    
    This model uses a flexible approach where feedback questions and responses are stored
    dynamically based on a FeedbackTemplate. This allows for customizable feedback forms
    without requiring schema changes for new question types.
    """
    complaint = models.OneToOneField(
        'complaints.Complaint', 
        on_delete=models.CASCADE, 
        related_name='feedback',
        help_text="The complaint this feedback is for"
    )
    user = models.ForeignKey(
        'auth.User', 
        on_delete=models.CASCADE,
        help_text="User who submitted the feedback"
    )
    template = models.ForeignKey(
        'FeedbackTemplate', 
        on_delete=models.PROTECT, 
        null=True,
        help_text="The feedback template used for this submission"
    )
    responses = models.JSONField(
        default=dict,
        help_text="Key-value pairs of questions and user-provided ratings/answers"
    )
    comment = models.TextField(
        blank=True, 
        max_length=1000,
        help_text="General-purpose comment field"
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the feedback was submitted"
    )

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedback'

    def __str__(self):
        template_name = self.template.name if self.template else "No Template"
        return f"Feedback for Complaint #{self.complaint.id} using {template_name}"

    def get_response(self, question_key, default=None):
        """
        Get a specific response from the feedback.
        
        Args:
            question_key (str): The key for the question
            default: Default value if key not found
            
        Returns:
            The response value or default
        """
        return self.responses.get(question_key, default)

    def set_response(self, question_key, value):
        """
        Set a specific response in the feedback.
        
        Args:
            question_key (str): The key for the question
            value: The response value
        """
        self.responses[question_key] = value

    @property
    def overall_rating(self):
        """
        Calculate overall rating if available in responses.
        
        Returns:
            float or None: Average rating or None if no ratings found
        """
        ratings = []
        for key, value in self.responses.items():
            if isinstance(value, (int, float)) and 1 <= value <= 5:
                ratings.append(value)
        
        if ratings:
            return sum(ratings) / len(ratings)
        return None

    @property
    def rating_display(self):
        """
        Return star rating display for overall rating.
        
        Returns:
            str: Star representation of the rating
        """
        rating = self.overall_rating
        if rating is None:
            return "No rating"
        
        full_stars = int(rating)
        return "★" * full_stars + "☆" * (5 - full_stars)


class FeedbackTemplate(models.Model):
    """
    Template for feedback questions and categories.
    
    This model defines the structure and questions for feedback forms. It allows
    administrators to create different types of feedback forms for different
    complaint types or scenarios. The questions are stored as JSON to provide
    flexibility in question types and formats.
    """
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Name of the feedback template"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of when and how this template should be used"
    )
    questions = models.JSONField(
        default=list,
        help_text="List of questions for this feedback template in JSON format"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this template is currently active and available for use"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the template was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the template was last updated"
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Feedback Template'
        verbose_name_plural = 'Feedback Templates'

    def __str__(self):
        return self.name

    def get_question_count(self):
        """
        Get the number of questions in this template.
        
        Returns:
            int: Number of questions
        """
        return len(self.questions) if isinstance(self.questions, list) else 0

    def get_questions_by_type(self, question_type):
        """
        Get questions of a specific type from the template.
        
        Args:
            question_type (str): Type of questions to filter by
            
        Returns:
            list: Questions matching the specified type
        """
        if not isinstance(self.questions, list):
            return []
        
        return [q for q in self.questions if q.get('type') == question_type]
