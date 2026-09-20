from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"W#{self.id} | {self.user.username}'s Wallet"



class Payment(models.Model):
    STATUS_CHOICES = [
       ("pending", "Pending"),
       ("processing", "Processing"),
       ("success", "Success"),
       ("failed", "Failed"),
       ("refunded","Refunded")
    ]

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    tracking_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"P#{self.id} | Payment's Tracking Code : {self.tracking_code}"



class Transaction(models.Model):
    TYPE_CHOICES = [
        ("payment", "Payment"),
        ("refund", "Refund"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("deposit", "Deposit")
    ]

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="transactions")
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="transactions", blank=True, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"T#{self.id} | Transaction {self.id}"



class Refund(models.Model):
    STATUS_CHOICES = [
       ("pending", "Pending"),
       ("processing", "Processing"),
       ("success", "Success"),
       ("failed", "Failed"),
    ]
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"R#{self.id} | Refund - Payment {self.payment.id}"
