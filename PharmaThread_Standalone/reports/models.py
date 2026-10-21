from django.db import models
from django.contrib.auth.models import User

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('DISPENSE', 'Dispense'),
        ('ADJUST', 'Adjust'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
