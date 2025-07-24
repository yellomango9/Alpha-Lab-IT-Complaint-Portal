from django.db import models
from complaints.models import Complaint

class Feedback(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for Complaint #{self.complaint_id}"
