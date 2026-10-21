import os
import django
from datetime import date, timedelta
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meezan_pharma.settings")
django.setup()

from django.contrib.auth.models import User
from inventory.models import Medicine, Batch, StockAdjustment
from procurement.models import Supplier, PurchaseInvoice, PurchaseItem
from finance.models import Expense

def seed():
    # Create superuser
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    
    # Create medicines
    med1 = Medicine.objects.create(name='Paracetamol 650mg Dolo', generic_name='Paracetamol', manufacturer='Micro Labs', category='Tablet', rack_location='A1', min_stock_level=50)
    med2 = Medicine.objects.create(name='Amoxicillin-Clav 625mg Augmentin', generic_name='Amoxicillin and Clavulanate', manufacturer='GSK', category='Tablet', rack_location='A2', min_stock_level=20)
    med3 = Medicine.objects.create(name='Pantoprazole 40mg', generic_name='Pantoprazole', manufacturer='Sun Pharma', category='Tablet', rack_location='B1', min_stock_level=30)
    med4 = Medicine.objects.create(name='Ceftriaxone 1g Inj', generic_name='Ceftriaxone', manufacturer='Cipla', category='Injection', rack_location='Fridge', min_stock_level=10)

    # Create supplier
    sup = Supplier.objects.create(name='Pharma Distributors Inc', phone='1234567890', address='123 Health St')

    # Create batches
    today = date.today()
    Batch.objects.create(medicine=med1, batch_number='B001', expiry_date=today + timedelta(days=365), purchase_price=10.00, mrp=20.00, selling_price=15.00, quantity=100)
    Batch.objects.create(medicine=med1, batch_number='B002', expiry_date=today + timedelta(days=60), purchase_price=9.00, mrp=20.00, selling_price=15.00, quantity=50) # near expiry
    Batch.objects.create(medicine=med1, batch_number='B003', expiry_date=today - timedelta(days=10), purchase_price=10.00, mrp=20.00, selling_price=15.00, quantity=10) # expired
    Batch.objects.create(medicine=med2, batch_number='B004', expiry_date=today + timedelta(days=20), purchase_price=50.00, mrp=75.00, selling_price=70.00, quantity=30) # <30d
    Batch.objects.create(medicine=med3, batch_number='B005', expiry_date=today + timedelta(days=80), purchase_price=15.00, mrp=30.00, selling_price=25.00, quantity=40) # <90d

    # Log Expense
    Expense.objects.create(date=today, category='Rent', amount=5000.00, description='Monthly Rent')

if __name__ == '__main__':
    seed()
    print("Database seeded successfully.")
