from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver


class Department(models.Model):
    """
    Model for organizational departments within Alpha Labs.
    
    Represents different departments such as IT, HR, Finance, etc.
    Used to categorize users and track complaint distribution across departments.
    """
    name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Name of the department"
    )
    description = models.TextField(
        blank=True, 
        help_text="Description of the department's responsibilities and scope"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this department is currently active"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the department was created"
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """
    Extended user profile model that serves as a lean extension of Django's built-in User model.
    
    This model stores additional information about users that is specific to the Alpha Lab
    IT Complaint Portal, including department affiliation, contact information, and
    integration with the main Alpha Labs portal for SSO functionality.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        help_text="Reference to the Django User model"
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="The department this user belongs to"
    )
    
    # Contact Information
    phone_number = models.CharField(
        max_length=20, 
        blank=True,
        help_text="User's contact phone number"
    )
    
    # SSO Integration
    main_portal_id = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        db_index=True,
        help_text="Unique ID from the main Alpha Labs portal for SSO"
    )
    
    # Preferences
    email_notifications = models.BooleanField(
        default=True, 
        help_text="Whether to receive email notifications for complaint updates"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the profile was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when the profile was last updated"
    )

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.department or 'No Department'}"
    
    def clean(self):
        """Custom validation for UserProfile."""
        from django.core.exceptions import ValidationError
        
        # Ensure main_portal_id is unique when not blank
        if self.main_portal_id:
            existing = UserProfile.objects.filter(main_portal_id=self.main_portal_id)
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({
                    'main_portal_id': 'A user with this Main Portal ID already exists.'
                })

    @property
    def full_name(self):
        """Return user's full name or username if not available."""
        return self.user.get_full_name() or self.user.username

    @property
    def is_engineer(self):
        """
        Check if user is an engineer based on Django Group membership.
        
        Returns:
            bool: True if user belongs to 'Engineer' or 'AMC Admin' groups
        """
        return self.user.groups.filter(name__in=['Engineer', 'AMC Admin']).exists()

    @property
    def is_admin(self):
        """
        Check if user is an admin based on Django Group membership or staff status.
        
        Returns:
            bool: True if user belongs to 'Admin' or 'AMC Admin' groups, or is Django staff
        """
        return (
            self.user.groups.filter(name__in=['Admin', 'AMC Admin']).exists() or 
            self.user.is_staff
        )

    @property
    def user_groups(self):
        """
        Get all groups the user belongs to.
        
        Returns:
            QuerySet: All groups the user is a member of
        """
        return self.user.groups.all()


# Temporarily disable signal to prevent conflicts
# @receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to create or update UserProfile when User is saved.
    
    Args:
        sender: The User model class
        instance: The User instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    # Avoid creating profiles during migrations or when loading fixtures
    if kwargs.get('raw', False):
        return
    
    try:
        if created:
            # Create profile only if it doesn't exist
            profile, profile_created = UserProfile.objects.get_or_create(user=instance)
            if profile_created:
                print(f"Created profile for user {instance.username}")
        else:
            # For existing users, ensure they have a profile
            if not hasattr(instance, 'profile'):
                try:
                    profile = UserProfile.objects.get(user=instance)
                except UserProfile.DoesNotExist:
                    profile, profile_created = UserProfile.objects.get_or_create(user=instance)
                    if profile_created:
                        print(f"Created missing profile for user {instance.username}")
    except Exception as e:
        # Log the error but don't break user creation
        print(f"Error in profile creation for user {instance.username}: {e}")
        pass
