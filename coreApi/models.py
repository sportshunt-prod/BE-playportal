from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_organizer = models.BooleanField('organizer status', default=False)
    
    def __str__(self):
        return (
            f"{self.username}"
        )


class Order(models.Model):
    # Payment Status Choices
    PAYMENT_STATUS = [
        ('pending', 'Payment Pending'),
        ('completed', 'Payment Completed'),
        ('failed', 'Payment Failed'),
        ('cancelled', 'Payment Cancelled'),
    ]
    
    # Keep order_id as PK for backward compatibility with existing data
    order_id = models.CharField(max_length=100, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Amount stored in rupees (INR). Multiply by 100 for Razorpay (paise).
    # Conversion happens in views at create_order() call.
    amount = models.IntegerField()
    
    # Payment Details
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    signature = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    order_timestamp = models.DateTimeField(auto_now_add=True)
    payment_timestamp = models.DateTimeField(blank=True, null=True)
    
    # References to payment context
    team_instance = models.ForeignKey("organizationApi.Team", on_delete=models.CASCADE, blank=True, null=True)
    team_name = models.CharField(max_length=100)
    category_instance = models.ForeignKey("organizationApi.Category", on_delete=models.CASCADE, blank=True, null=True)
    tournament_instance = models.ForeignKey("organizationApi.Tournament", on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"Order {self.order_id} - {self.team_name} ({self.payment_status})"
    