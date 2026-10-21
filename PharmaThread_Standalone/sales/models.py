from django.db import models
from inventory.models import Batch

class Customer(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    outstanding_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

class SalesInvoice(models.Model):
    PAYMENT_CHOICES = [
        ('CASH', 'Cash'),
        ('UPI', 'UPI'),
        ('CARD', 'Card'),
        ('CREDIT', 'Credit'),
    ]
    invoice_number = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name_manual = models.CharField(max_length=255, blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    
    # H/H1 Compliance Fields
    patient_age = models.IntegerField(null=True, blank=True)
    patient_address = models.TextField(blank=True)
    doctor_name = models.CharField(max_length=255, blank=True)
    doctor_reg_no = models.CharField(max_length=100, blank=True, verbose_name="Doctor Reg No.")
    
    date = models.DateTimeField(auto_now_add=True)
    
    # Tax fields
    total_taxable_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_cgst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_sgst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_igst = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_interstate = models.BooleanField(default=False)
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    round_off = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='CASH')
    is_paid = models.BooleanField(default=True)
    total_cogs = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.invoice_number

class SalesItem(models.Model):
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, related_name='items')
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT)
    base_units = models.IntegerField(help_text="Total base units")
    quantity = models.IntegerField(default=0, help_text="Number of full packs sold")
    loose = models.IntegerField(default=0, help_text="Number of individual units sold")
    rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Pack selling price")
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Tax breakdown per item
    hsn_code = models.CharField(max_length=10, blank=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    taxable_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cgst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sgst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    igst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cogs = models.DecimalField(max_digits=10, decimal_places=2)

class SalesReturn(models.Model):
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    restock_to_inventory = models.BooleanField(default=True)
    reason = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
