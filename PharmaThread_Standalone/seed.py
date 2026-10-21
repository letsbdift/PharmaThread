import os
import sys
import django
import random
from datetime import date, timedelta
from decimal import Decimal

# Setup django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meezan_pharma.settings")
django.setup()

from inventory.models import Medicine, Batch
from sales.models import Customer, SalesInvoice, SalesItem

def create_dummy_data():
    print("Clearing old data...")
    SalesItem.objects.all().delete()
    SalesInvoice.objects.all().delete()
    Customer.objects.all().delete()
    Batch.objects.all().delete()
    Medicine.objects.all().delete()

    print("Creating Medicines and Batches...")
    meds_data = [
        {"name": "Paracetamol 500mg", "generic_name": "Paracetamol", "manufacturer": "GSK", "category": "Tablet", "rack_location": "A1", "schedule_type": "GENERAL", "units_per_pack": 10},
        {"name": "Amoxicillin 250mg", "generic_name": "Amoxicillin", "manufacturer": "Cipla", "category": "Capsule", "rack_location": "B2", "schedule_type": "H1", "units_per_pack": 15},
        {"name": "Cough Syrup", "generic_name": "Dextromethorphan", "manufacturer": "Sun Pharma", "category": "Syrup", "rack_location": "C1", "schedule_type": "GENERAL", "units_per_pack": 1},
        {"name": "Vitamin C 1000mg", "generic_name": "Ascorbic Acid", "manufacturer": "Abbott", "category": "Tablet", "rack_location": "A3", "schedule_type": "GENERAL", "units_per_pack": 20},
        {"name": "Alprazolam 0.25mg", "generic_name": "Alprazolam", "manufacturer": "Mankind", "category": "Tablet", "rack_location": "Secure1", "schedule_type": "X", "units_per_pack": 10},
    ]

    medicines = []
    batches = []
    for m in meds_data:
        med = Medicine.objects.create(
            name=m["name"],
            generic_name=m["generic_name"],
            manufacturer=m["manufacturer"],
            category=m["category"],
            rack_location=m["rack_location"],
            schedule_type=m["schedule_type"],
            units_per_pack=m["units_per_pack"],
            min_stock_level=50,
            hsn_code=str(random.randint(3000, 3100)),
            gst_rate=Decimal("12.00")
        )
        medicines.append(med)
        
        # Create 1-2 batches per medicine
        for i in range(random.randint(1, 2)):
            batch = Batch.objects.create(
                medicine=med,
                batch_number=f"B{random.randint(1000, 9999)}",
                expiry_date=date.today() + timedelta(days=random.randint(100, 700)),
                purchase_price=Decimal(str(random.uniform(10.0, 50.0))).quantize(Decimal('0.01')),
                mrp=Decimal(str(random.uniform(60.0, 100.0))).quantize(Decimal('0.01')),
                selling_price=Decimal(str(random.uniform(55.0, 90.0))).quantize(Decimal('0.01')),
                quantity=random.randint(100, 500)
            )
            batches.append(batch)

    print("Creating Customers...")
    c1 = Customer.objects.create(name="Walk-in Customer", phone="")
    c2 = Customer.objects.create(name="John Doe", phone="9876543210", outstanding_credit=Decimal("50.00"))
    c3 = Customer.objects.create(name="Jane Smith", phone="8765432109")
    customers = [c1, c2, c3]

    print("Creating Sales Invoices...")
    for i in range(10):
        cust = random.choice(customers)
        inv = SalesInvoice.objects.create(
            invoice_number=f"INV-{1000 + i}",
            customer=cust,
            customer_name_manual=cust.name,
            payment_method=random.choice(['CASH', 'UPI', 'CARD']),
            total_taxable_value=Decimal("0.00"),
            total_cgst=Decimal("0.00"),
            total_sgst=Decimal("0.00"),
            total_igst=Decimal("0.00"),
            subtotal=Decimal("0.00"),
            net_amount=Decimal("0.00"),
            total_cogs=Decimal("0.00")
        )
        
        # Add 1-3 items
        subtotal = Decimal("0")
        cogs = Decimal("0")
        for j in range(random.randint(1, 3)):
            batch = random.choice(batches)
            qty = random.randint(1, 3)
            base_units = qty * batch.medicine.units_per_pack
            rate = batch.selling_price
            line_tot = rate * qty
            
            SalesItem.objects.create(
                invoice=inv,
                batch=batch,
                quantity=qty,
                base_units=base_units,
                rate=rate,
                line_total=line_tot,
                unit_cogs=batch.purchase_price,
                taxable_value=line_tot * Decimal("0.88"), # approx 12% gst backward
                cgst_amount=line_tot * Decimal("0.06"),
                sgst_amount=line_tot * Decimal("0.06")
            )
            subtotal += line_tot
            cogs += (batch.purchase_price * qty)
            
            # Deduct from batch
            batch.quantity -= base_units
            batch.save()
            
        inv.subtotal = subtotal
        inv.net_amount = subtotal
        inv.total_cogs = cogs
        inv.save()
        
    print("Dummy data creation complete!")

if __name__ == "__main__":
    create_dummy_data()
