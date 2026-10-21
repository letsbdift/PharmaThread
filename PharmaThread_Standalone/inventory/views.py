from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
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
        med.delete()
        return redirect('medicine_list')
    return render(request, 'medicine_delete.html', {'med': med})
