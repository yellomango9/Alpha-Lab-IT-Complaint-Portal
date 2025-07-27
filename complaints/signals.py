"""
Django signals for the complaints app.
Handles automatic notifications and status updates.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Count
from datetime import datetime, timedelta

from .models import Complaint, Status, StatusHistory
from core.models import UserProfile


@receiver(pre_save, sender=Complaint)
def complaint_status_change(sender, instance, **kwargs):
    """
    Handle complaint status changes.
    Creates status history entries and updates metrics.
    """
    if instance.pk:  # Only for existing complaints
        try:
            old_complaint = Complaint.objects.get(pk=instance.pk)
            
            # Check if status changed
            if old_complaint.status != instance.status:
                # If status changed to closed, set resolved_at
                if instance.status and instance.status.is_closed and not instance.resolved_at:
                    instance.resolved_at = timezone.now()
                
                # Store status change info for post_save signal
                instance._status_changed = True
                instance._old_status = old_complaint.status
                instance._new_status = instance.status
                
                # Send notification email
                send_status_change_notification(instance, old_complaint.status, instance.status)
                
        except Complaint.DoesNotExist:
            pass


@receiver(post_save, sender=Complaint)
def complaint_created(sender, instance, created, **kwargs):
    """
    Handle new complaint creation and status changes.
    Creates status history and updates metrics.
    """
    if created:
        # Create initial status history entry
        StatusHistory.objects.create(
            complaint=instance,
            previous_status=None,
            new_status=instance.status,
            changed_by=instance.user,
            notes="Complaint created"
        )
        
        # Send confirmation email to user
        send_complaint_confirmation(instance)
        
        # Notify IT staff about new complaint
        notify_it_staff_new_complaint(instance)
        
        # Note: Metrics calculation removed - will be implemented as scheduled task
    
    else:
        # Handle status changes for existing complaints
        if hasattr(instance, '_status_changed') and instance._status_changed:
            # Create status history entry
            StatusHistory.objects.create(
                complaint=instance,
                previous_status=instance._old_status,
                new_status=instance._new_status,
                changed_by=getattr(instance, '_changed_by', instance.user),
                notes=getattr(instance, '_status_change_notes', '')
            )
            
            # Note: Metrics calculation removed - will be implemented as scheduled task
            
            # Clean up temporary attributes
            delattr(instance, '_status_changed')
            delattr(instance, '_old_status')
            delattr(instance, '_new_status')


def send_complaint_confirmation(complaint):
    """Send confirmation email to user who submitted complaint."""
    if not complaint.user.email:
        return
    
    try:
        subject = f'Complaint #{complaint.id} - Confirmation'
        
        context = {
            'complaint': complaint,
            'user': complaint.user,
        }
        
        # Render email templates
        html_message = render_to_string('emails/complaint_confirmation.html', context)
        plain_message = render_to_string('emails/complaint_confirmation.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[complaint.user.email],
            fail_silently=True,
        )
        
    except Exception as e:
        # Log error but don't raise exception
        print(f"Error sending complaint confirmation email: {e}")


def send_status_change_notification(complaint, old_status, new_status):
    """Send notification when complaint status changes."""
    if not complaint.user.email:
        return
    
    # Check if user wants email notifications
    if hasattr(complaint.user, 'profile') and not complaint.user.profile.email_notifications:
        return
    
    try:
        subject = f'Complaint #{complaint.id} - Status Updated'
        
        context = {
            'complaint': complaint,
            'user': complaint.user,
            'old_status': old_status,
            'new_status': new_status,
        }
        
        # Render email templates
        html_message = render_to_string('emails/status_change.html', context)
        plain_message = render_to_string('emails/status_change.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[complaint.user.email],
            fail_silently=True,
        )
        
    except Exception as e:
        # Log error but don't raise exception
        print(f"Error sending status change notification: {e}")


def notify_it_staff_new_complaint(complaint):
    """Notify IT staff about new complaints."""
    try:
        # Get IT engineers and managers
        from django.contrib.auth.models import Group
        engineer_groups = Group.objects.filter(name__icontains='engineer')
        it_staff = UserProfile.objects.filter(
            user__groups__in=engineer_groups,
            email_notifications=True,
            user__email__isnull=False
        ).exclude(user__email='').distinct()
        
        if not it_staff.exists():
            return
        
        subject = f'New Complaint #{complaint.id} - {complaint.title}'
        
        context = {
            'complaint': complaint,
        }
        
        # Render email templates
        html_message = render_to_string('emails/new_complaint_staff.html', context)
        plain_message = render_to_string('emails/new_complaint_staff.txt', context)
        
        recipient_list = [profile.user.email for profile in it_staff]
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=True,
        )
        
    except Exception as e:
        # Log error but don't raise exception
        print(f"Error sending new complaint notification to staff: {e}")


@receiver(post_save, sender=Complaint)
def complaint_assignment_notification(sender, instance, **kwargs):
    """Send notification when complaint is assigned to an engineer."""
    if instance.assigned_to and instance.assigned_to.email:
        # Check if this is a new assignment
        if kwargs.get('update_fields') and 'assigned_to' in kwargs['update_fields']:
            send_assignment_notification(instance)


def send_assignment_notification(complaint):
    """Send notification to engineer when complaint is assigned."""
    if not complaint.assigned_to.email:
        return
    
    # Check if engineer wants email notifications
    if hasattr(complaint.assigned_to, 'profile') and not complaint.assigned_to.profile.email_notifications:
        return
    
    try:
        subject = f'Complaint #{complaint.id} Assigned to You'
        
        context = {
            'complaint': complaint,
            'engineer': complaint.assigned_to,
        }
        
        # Render email templates
        html_message = render_to_string('emails/complaint_assignment.html', context)
        plain_message = render_to_string('emails/complaint_assignment.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[complaint.assigned_to.email],
            fail_silently=True,
        )
        
    except Exception as e:
        # Log error but don't raise exception
        print(f"Error sending assignment notification: {e}")


# Note: Daily metrics calculation function removed
# This functionality will be reimplemented as a scheduled task to avoid performance bottlenecks