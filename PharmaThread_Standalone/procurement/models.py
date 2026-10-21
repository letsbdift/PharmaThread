from django.db import models
from inventory.models import Medicine, Batch

class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    gstin = models.CharField(max_length=50, blank=True)
    address = models.TextField()
    payment_terms = models.CharField(max_length=100, blank=True, help_text="e.g. Net 30, COD")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    pending_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

class PurchaseInvoice(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=100)
    purchase_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('supplier', 'invoice_number')

    def __str__(self):
        return f"{self.invoice_number} - {self.supplier.name}"

class PurchaseItem(models.Model):
    purchase_invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    quantity = models.IntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)

class PurchaseReturn(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
