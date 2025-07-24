from django.db import models
from django.conf import settings
from core.models import Department

class ComplaintType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Status(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = 'Statuses'

class Complaint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='complaints')
    type = models.ForeignKey(ComplaintType, on_delete=models.PROTECT)
    status = models.ForeignKey(Status, on_delete=models.PROTECT)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class FileAttachment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='attachments')
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=512)
    uploaded_at = models.DateTimeField(auto_now_add=True)
