from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q, ProtectedError
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from .models import Medicine, Batch

@login_required
@role_required(['Admin', 'Pharmacist'])
def medicine_list(request):
    query = request.GET.get('q', '')
    if query:
        medicines = Medicine.objects.filter(
            Q(name__icontains=query) | 
            Q(generic_name__icontains=query)
        ).annotate(total_stock=Sum('batches__quantity'))
    else:
        medicines = Medicine.objects.all().annotate(total_stock=Sum('batches__quantity'))
        
    return render(request, 'medicine_list.html', {'medicines': medicines, 'query': query})

@login_required
@role_required(['Admin', 'Pharmacist'])
def medicine_add(request):
    if request.method == 'POST':
        units_per_pack = int(request.POST.get('units_per_pack', 1))
        med = Medicine.objects.create(
            name=request.POST.get('name'),
            generic_name=request.POST.get('generic_name', ''),
            manufacturer=request.POST.get('manufacturer'),
            category=request.POST.get('category'),
            rack_location=request.POST.get('rack_location'),
            min_stock_level=request.POST.get('min_stock_level', 10),
            units_per_pack=units_per_pack,
            schedule_type=request.POST.get('schedule_type', 'GENERAL'),
            hsn_code=request.POST.get('hsn_code', ''),
            gst_rate=request.POST.get('gst_rate', 12.00)
        )
        return redirect('medicine_list')
    return render(request, 'medicine_add.html')

from django.shortcuts import get_object_or_404

@login_required
@role_required(['Admin', 'Pharmacist'])
def medicine_edit(request, pk):
    med = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        med.name = request.POST.get('name')
        med.generic_name = request.POST.get('generic_name', '')
        med.category = request.POST.get('category')
        med.manufacturer = request.POST.get('manufacturer')
        med.rack_location = request.POST.get('rack_location')
        med.units_per_pack = int(request.POST.get('units_per_pack', 1))
        med.min_stock_level = int(request.POST.get('min_stock_level', 10))
        med.schedule_type = request.POST.get('schedule_type', 'GENERAL')
        med.hsn_code = request.POST.get('hsn_code', '')
        med.gst_rate = request.POST.get('gst_rate', 12.00)
        med.save()
        messages.success(request, 'Medicine updated successfully.')
        return redirect('medicine_list')
        
    return render(request, 'medicine_edit.html', {'med': med})

@login_required
@role_required(['Admin'])
def medicine_delete(request, pk):
    med = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        try:
            med.delete()
            messages.success(request, f"Medicine '{med.name}' deleted successfully.")
        except ProtectedError:
            messages.error(request, f"Cannot delete '{med.name}' because it has existing stock batches or sales history.")
        return redirect('medicine_list')
    return render(request, 'medicine_delete.html', {'med': med})


import csv
from django.http import HttpResponse, JsonResponse
from datetime import datetime

@login_required
@role_required(['Admin', 'Pharmacist'])
def download_import_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="drug_master_template.csv"'
    writer = csv.writer(response)
    writer.writerow(['Medicine Name', 'Generic / Category', 'Pack Size', 'Total Stock', 'Minimum Stock Level', 'Location / Rack', 'Schedule H Drug (Prescription Required)'])
    writer.writerow(['Paracetamol 500mg', 'Paracetamol / TABLET', '10', '50', '10', 'Rack A1', 'No'])
    return response

@login_required
@role_required(['Admin', 'Pharmacist'])
def medicine_bulk_import(request):
    if request.method == 'POST':
        file = request.FILES.get('import_file')
        if not file:
            messages.error(request, 'No file uploaded.')
            return redirect('medicine_list')
            
        try:
            if not file.name.endswith('.csv'):
                messages.error(request, 'Invalid file format. Please upload a CSV file.')
                return redirect('medicine_list')
                
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            
            success_count = 0
            for row in reader:
                drug_name = str(row.get('Medicine Name', '')).strip()
                if not drug_name or drug_name.lower() == 'nan':
                    continue
                    
                gen_cat = str(row.get('Generic / Category', '')).strip()
                if '/' in gen_cat:
                    parts = gen_cat.split('/', 1)
                    generic_name = parts[0].strip()
                    category = parts[1].strip().upper()
                else:
                    generic_name = gen_cat
                    category = 'OTHER'
                    
                manufacturer = 'Unknown'
                units_per_pack = row.get('Pack Size', '1').strip()
                if not units_per_pack: units_per_pack = 1
                
                min_stock_level = row.get('Minimum Stock Level', '10').strip()
                if not min_stock_level: min_stock_level = 10
                
                rack_location = str(row.get('Location / Rack', '')).strip()
                
                sched_h_str = str(row.get('Schedule H Drug (Prescription Required)', '')).strip().lower()
                schedule_type = 'H' if sched_h_str in ['yes', 'y', 'true', '1'] else 'GENERAL'
                
                batch_number = 'INITIAL'
                from datetime import date, timedelta
                expiry_date = date.today() + timedelta(days=365)
                
                purchase_price = 0.0
                mrp = 0.0
                selling_price = 0.0
                
                iq_str = row.get('Total Stock', '0').strip()
                initial_quantity = float(iq_str) if iq_str else 0.0
                
                med, created = Medicine.objects.get_or_create(
                    name=drug_name,
                    defaults={
                        'generic_name': generic_name,
                        'manufacturer': manufacturer,
                        'category': category if category in ['TABLET', 'SYRUP', 'INJECTION', 'OINTMENT', 'DROPS', 'OTHER'] else 'OTHER',
                        'units_per_pack': int(float(units_per_pack)),
                        'min_stock_level': int(float(min_stock_level)),
                        'rack_location': rack_location,
                        'schedule_type': schedule_type
                    }
                )
                
                if initial_quantity > 0:
                    batch, b_created = Batch.objects.get_or_create(
                        medicine=med,
                        batch_number=batch_number,
                        defaults={
                            'expiry_date': expiry_date,
                            'purchase_price': purchase_price,
                            'mrp': mrp,
                            'selling_price': selling_price,
                            'quantity': int(initial_quantity)
                        }
                    )
                    if not b_created:
                        batch.quantity += int(initial_quantity)
                        batch.save()
                
                success_count += 1
                
            messages.success(request, f'Successfully imported/updated {success_count} medicines.')
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            
        return redirect('medicine_list')
    return redirect('medicine_list')
