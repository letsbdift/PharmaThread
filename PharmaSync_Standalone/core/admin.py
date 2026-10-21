from django.contrib import admin
from .models import PharmacyProfile

@admin.register(PharmacyProfile)
class PharmacyProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'gstin', 'dl_number_20', 'dl_number_21')
    
    def has_add_permission(self, request):
        # Allow adding only if no instance exists
        if PharmacyProfile.objects.exists():
            return False
        return super().has_add_permission(request)
