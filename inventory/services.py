from inventory.models import Medicine, Batch
from datetime import date
from django.db.models import Sum

class AlertService:
    @staticmethod
    def get_alerts():
        today = date.today()
        alerts = {
            'low_stock': [],
            'expired': [],
            'near_expiry_30': [],
            'near_expiry_60': [],
            'near_expiry_90': [],
            'near_expiry_180': [],
        }
        
        medicines = Medicine.objects.filter(is_active=True).annotate(total_stock=Sum('batches__quantity'))
        for med in medicines:
            stock = med.total_stock or 0
            units_per_pack = med.units_per_pack if med.units_per_pack > 0 else 1
            stock_in_packs = stock / units_per_pack
            
            if stock_in_packs <= med.min_stock_level:
                packs = stock // units_per_pack
                loose = stock % units_per_pack
                
                if packs > 0 and loose > 0:
                    display_stock = f"{packs} strips, {loose} tablets"
                elif packs > 0:
                    display_stock = f"{packs} strips"
                elif loose > 0:
                    display_stock = f"{loose} tablets"
                else:
                    display_stock = "0 strips"
                    
                alerts['low_stock'].append({'medicine': med.name, 'stock': display_stock, 'min': med.min_stock_level, 'rack': med.rack_location})
                
        batches = Batch.objects.filter(quantity__gt=0)
        for batch in batches:
            days_to_expiry = (batch.expiry_date - today).days
            item = {'medicine': batch.medicine.name, 'batch': batch.batch_number, 'qty': batch.quantity, 'expiry': batch.expiry_date.strftime('%Y-%m-%d'), 'rack': batch.medicine.rack_location}
            
            if days_to_expiry <= 0:
                alerts['expired'].append(item)
            elif days_to_expiry <= 30:
                alerts['near_expiry_30'].append(item)
            elif days_to_expiry <= 60:
                alerts['near_expiry_60'].append(item)
            elif days_to_expiry <= 90:
                alerts['near_expiry_90'].append(item)
            elif days_to_expiry <= 180:
                alerts['near_expiry_180'].append(item)
                
        return alerts
