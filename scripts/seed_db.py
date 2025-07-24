from complaints.models import ComplaintType, Status
from core.models import Department, Role
from faq.models import FAQ

ComplaintType.objects.bulk_create([
    ComplaintType(name="Hardware"),
    ComplaintType(name="Software"),
    ComplaintType(name="Network"),
    ComplaintType(name="Peripheral Devices"),
    ComplaintType(name="Data Transfer"),
    ComplaintType(name="Others"),
])

Status.objects.bulk_create([
    Status(name="Open"),
    Status(name="In Progress"),
    Status(name="Resolved"),
    Status(name="Closed"),
])

Department.objects.bulk_create([
    Department(name="IT"),
    Department(name="HR"),
    Department(name="Finance"),
])

Role.objects.bulk_create([
    Role(name="User"),
    Role(name="Engineer"),
    Role(name="AMC_Admin"),
    Role(name="Admin"),
])

FAQ.objects.bulk_create([
    FAQ(question="How do I reset my password?", answer="Contact the IT department."),
    FAQ(question="What to do if my laptop crashes?", answer="File a complaint under Hardware."),
])
