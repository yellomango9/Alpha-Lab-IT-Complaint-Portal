from django.contrib import admin
from .models import Complaint, ComplaintType, Status, FileAttachment

admin.site.register(Complaint)
admin.site.register(ComplaintType)
admin.site.register(Status)
admin.site.register(FileAttachment)
