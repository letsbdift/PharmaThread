from django.db import models
from procurement.models import Supplier
from sales.models import Customer

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Rent', 'Rent'),
        ('Salary', 'Salary'),
        ('Electricity', 'Electricity'),
        ('Internet', 'Internet'),
        ('Transport', 'Transport'),
        ('Maintenance', 'Maintenance'),
        ('Other', 'Other'),
    ]
    date = models.DateField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.category} - {self.amount}"

class SupplierPayment(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    reference_number = models.CharField(max_length=100, blank=True)

class CustomerCreditPayment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50)
