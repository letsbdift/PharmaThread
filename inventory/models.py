from django.db import models

class Medicine(models.Model):
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True)
    manufacturer = models.CharField(max_length=255)
    category = models.CharField(max_length=50)
    rack_location = models.CharField(max_length=20)
    min_stock_level = models.IntegerField(default=10)
    
    SCHEDULE_CHOICES = [
        ('GENERAL', 'General'),
        ('H', 'Schedule H'),
        ('H1', 'Schedule H1'),
        ('X', 'Schedule X')
    ]
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default='GENERAL')
    hsn_code = models.CharField(max_length=10, blank=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12.00)
    
    unit_measure = models.CharField(max_length=20, default='units')
    units_per_pack = models.IntegerField(default=1, help_text="Packaging size from medicine master")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        cat = self.category.upper()
        if cat in ['TABLET', 'CAPSULE']:
            self.unit_measure = 'units'
        elif cat in ['SYRUP', 'INJECTION', 'DROPS']:
            self.unit_measure = 'ml'
        elif cat == 'OINTMENT':
            self.unit_measure = 'g'
        else:
            self.unit_measure = 'units'
        super().save(*args, **kwargs)

    @property
    def total_base_stock(self):
        from django.db.models import Sum
        return self.batches.aggregate(s=Sum('quantity'))['s'] or 0
        
    @property
    def stock_formatted(self):
        total = self.total_base_stock
        c = self.category.upper()
        if c in ['TABLET', 'CAPSULE']:
            if self.units_per_pack > 1:
                strips = total // self.units_per_pack
                tabs = total % self.units_per_pack
                if strips > 0 and tabs > 0:
                    return f"{strips} strips, {tabs} {self.unit_measure}"
                elif strips > 0:
                    return f"{strips} strips"
                else:
                    return f"{tabs} {self.unit_measure}"
            return f"{total} {self.unit_measure}"
        elif c in ['SYRUP', 'DROPS']:
            bottles = total // self.units_per_pack if self.units_per_pack else 0
            rem = total % self.units_per_pack if self.units_per_pack else 0
            return f"{bottles} bottles" + (f" (+{rem}{self.unit_measure})" if rem else "")
        elif c == 'INJECTION':
            vials = total // self.units_per_pack if self.units_per_pack else 0
            rem = total % self.units_per_pack if self.units_per_pack else 0
            return f"{vials} vials" + (f" (+{rem}{self.unit_measure})" if rem else "")
        elif c == 'OINTMENT':
            tubes = total // self.units_per_pack if self.units_per_pack else 0
            rem = total % self.units_per_pack if self.units_per_pack else 0
            return f"{tubes} tubes" + (f" (+{rem}{self.unit_measure})" if rem else "")
        return f"{total} {self.unit_measure}"
        
    @property
    def avg_rate(self):
        batches = self.batches.filter(quantity__gt=0)
        if not batches.exists():
            return 0
        total_qty = sum(b.quantity for b in batches)
        total_val = sum(b.quantity * float(b.selling_price) for b in batches)
        return total_val / total_qty

    def __str__(self):
        return self.name

class Batch(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)

    class Meta:
        unique_together = ('medicine', 'batch_number')
        ordering = ['expiry_date']

    def __str__(self):
        return f"{self.medicine.name} - {self.batch_number}"

class StockAdjustment(models.Model):
    REASON_CHOICES = [
        ('DAMAGE', 'Damage'),
        ('THEFT', 'Theft'),
        ('CORRECTION', 'Correction'),
        ('EXPIRED', 'Expired'),
    ]
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='adjustments')
    quantity_adjusted = models.IntegerField()
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    remarks = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.batch} - {self.quantity_adjusted} ({self.reason})"
