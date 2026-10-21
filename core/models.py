from django.db import models
from django.core.exceptions import ValidationError

class PharmacyProfile(models.Model):
    name = models.CharField(max_length=200, default="Meezan Pharmacy")
    address = models.TextField(default="123 Health Street")
    phone = models.CharField(max_length=20, default="")
    
    # DL Numbers
    dl_number_20 = models.CharField(max_length=100, blank=True, null=True, verbose_name="DL No. (Form 20)")
    dl_number_21 = models.CharField(max_length=100, blank=True, null=True, verbose_name="DL No. (Form 21)")
    
    # GST Details
    gstin = models.CharField(max_length=15, blank=True, null=True, verbose_name="GSTIN")
    state_code = models.CharField(max_length=2, default="29", help_text="e.g., 29 for Karnataka")
    
    def save(self, *args, **kwargs):
        if not self.pk and PharmacyProfile.objects.exists():
            raise ValidationError('There can be only one PharmacyProfile instance')
        return super(PharmacyProfile, self).save(*args, **kwargs)

    @classmethod
    def get_profile(cls):
        profile, created = cls.objects.get_or_create(id=1)
        return profile

    def __str__(self):
        return self.name
