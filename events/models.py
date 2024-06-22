from django.db import models
from users.models import (
    User,
    Keyword,
    Wallet
    )
from django.conf import settings

class Event(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=1000)
    location_url = models.URLField(max_length=500)
    latitude = models.DecimalField(max_digits=30, decimal_places=20)
    longitude = models.DecimalField(max_digits=30, decimal_places=20)
    keywords = models.ManyToManyField(Keyword, related_name='events')
    host = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_events')
    start_datetime = models.DateTimeField(
        null=False, blank=False)
    end_datetime = models.DateTimeField(
        null=False, blank=False)
    description = models.CharField(max_length=1000, null=False, blank=False)

    def __str__(self):
        return self.name


class EventAttendee(models.Model):
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='attended_events')
    event_joined_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    referral_code = models.CharField(max_length=64, default=True, null=True)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user.username} joined {self.event.name} at {self.event_joined_at}"



class Transaction(models.Model):
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction of ${self.amount} for {self.user.email}"
