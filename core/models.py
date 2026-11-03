from django.db import models
from django.utils import timezone
import uuid

class FAQ(models.Model):
    category = models.CharField(max_length=100)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    keywords = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords for search matching")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['id']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return f"[{self.category}] {self.question}"


class ErrorCode(models.Model):
    code = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    cause = models.TextField()
    resolution = models.TextField()
    category = models.CharField(max_length=50)

    class Meta:
        ordering = ['code']
        verbose_name = "Error Code"
        verbose_name_plural = "Error Codes"

    def __str__(self):
        return f"{self.code} - {self.name}"


class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Normal', 'Normal'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]

    ticket_code = models.CharField(max_length=32, unique=True, editable=False)
    user_name = models.CharField(max_length=100, default='Anonymous')
    email = models.EmailField(blank=True)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Support Ticket"
        verbose_name_plural = "Support Tickets"

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            rand_suffix = uuid.uuid4().hex[:6].upper()
            year = timezone.now().year
            self.ticket_code = f"TKT-{year}-{rand_suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_code}: {self.subject} ({self.status})"


class RequestLog(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=255)
    status_code = models.IntegerField()
    duration_ms = models.FloatField()
    ip_address = models.CharField(max_length=45, default='127.0.0.1')
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Request Log"
        verbose_name_plural = "Request Logs"

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.method} {self.path} -> {self.status_code} ({self.duration_ms:.1f}ms)"
