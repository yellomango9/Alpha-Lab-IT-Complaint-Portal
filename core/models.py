from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Department(models.Model):
    """Model for organizational departments."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, help_text="Description of the department")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return self.name


class Role(models.Model):
    """Model for user roles and permissions."""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, help_text="Description of the role")
    permissions = models.TextField(
        blank=True, 
        help_text="JSON string of permissions for this role"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Extended user profile with additional information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="User's department"
    )
    role = models.ForeignKey(
        Role, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="User's role in the system"
    )
    
    # Contact Information
    phone_number = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=50, blank=True, unique=True)
    
    # Profile Details
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, max_length=500)
    
    # Preferences
    email_notifications = models.BooleanField(
        default=True, 
        help_text="Receive email notifications for complaint updates"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.role or 'No Role'}"

    @property
    def full_name(self):
        """Return user's full name or username if not available."""
        return self.user.get_full_name() or self.user.username

    @property
    def is_engineer(self):
        """Check if user is an engineer."""
        return self.role and self.role.name.lower() in ['engineer', 'amc_admin']

    @property
    def is_admin(self):
        """Check if user is an admin."""
        return self.role and self.role.name.lower() in ['admin', 'amc_admin'] or self.user.is_staff


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)
