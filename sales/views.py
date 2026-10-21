from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from inventory.models import Medicine
from sales.models import SalesInvoice
from .services import DispensingService
import json
import uuid
from django.db.models import Sum

@login_required
@role_required(['Admin', 'Pharmacist', 'Staff'])
def pos(request):
    # Fetch medicines with active stock
    medicines_qs = Medicine.objects.filter(is_active=True).annotate(total_stock=Sum('batches__quantity')).filter(total_stock__gt=0)
    
    medicines = []
    for m in medicines_qs:
        # Check non-expired earliest batch
        from datetime import date
        earliest_batch = m.batches.filter(quantity__gt=0, expiry_date__gt=date.today()).order_by('expiry_date').first()
        if earliest_batch:
            medicines.append({
                'id': m.id,
                'name': m.name,
                'stock': m.total_stock,
                'units_per_pack': m.units_per_pack,
                'unit_measure': getattr(m, 'unit_measure', 'units'),
                'price': float(earliest_batch.selling_price),
                'schedule_type': m.schedule_type,
                'hsn_code': m.hsn_code,
                'gst_rate': float(m.gst_rate)
            })
            
    return render(request, 'pos.html', {'medicines_json': json.dumps(medicines)})

@csrf_exempt
def api_medicines_list(request):
    medicines_qs = Medicine.objects.filter(is_active=True).annotate(total_stock=Sum('batches__quantity')).filter(total_stock__gt=0)
    medicines = []
    for m in medicines_qs:
        from datetime import date
        earliest_batch = m.batches.filter(quantity__gt=0, expiry_date__gt=date.today()).order_by('expiry_date').first()
        if earliest_batch:
            medicines.append({
                'id': m.id,
                'name': m.name,
                'stock': m.total_stock,
                'units_per_pack': m.units_per_pack,
                'unit_measure': getattr(m, 'unit_measure', 'units'),
                'price': float(earliest_batch.selling_price),
                'schedule_type': m.schedule_type,
                'hsn_code': m.hsn_code,
                'gst_rate': float(m.gst_rate)
            })
    return JsonResponse({'medicines': medicines})

@csrf_exempt
def api_customer_lookup(request):
    phone = request.GET.get('phone')
    if not phone:
        return JsonResponse({'status': 'error'})
        
    invoices = SalesInvoice.objects.filter(customer_phone=phone).order_by('-date')
    if not invoices.exists():
        return JsonResponse({'status': 'not_found'})
        
    name = invoices.first().customer_name_manual
    lifetime_orders = invoices.count()
    due_balance = sum([float(inv.net_amount) for inv in invoices if inv.payment_method == 'CREDIT'])
    
    history = []
    for inv in invoices[:15]:
        items = []
        for i in inv.items.all():
            items.append({
                'id': i.batch.medicine.id,
                'name': i.batch.medicine.name,
                'qty': i.quantity,
                'loose': i.loose,
                'total': float(i.line_total)
            })
            
        history.append({
            'invoice_number': inv.invoice_number,
            'date': inv.date.strftime('%Y-%m-%d %H:%M'),
            'doctor': inv.doctor_name,
            'amount': float(inv.net_amount),
            'payment_mode': inv.payment_method,
            'items': items
        })
        
    return JsonResponse({
        'status': 'success', 
        'name': name, 
        'lifetime_orders': lifetime_orders,
        'due_balance': due_balance,
        'history': history
    })

@csrf_exempt
def pos_checkout(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            invoice_data = {
                'invoice_number': f"INV-{uuid.uuid4().hex[:8].upper()}",
                'customer_name_manual': data.get('customer_name', 'Walk-in'),
                'customer_phone': data.get('customer_phone', ''),
                'patient_age': data.get('patient_age'),
                'patient_address': data.get('patient_address', ''),
                'doctor_name': data.get('doctor_name', ''),
                'doctor_reg_no': data.get('doctor_reg_no', ''),
                'is_interstate': data.get('is_interstate', False),
                'payment_method': data.get('payment_method', 'CASH'),
                'discount': float(data.get('discount', 0.00))
            }
            items_data = data.get('items', [])
            
            invoice = DispensingService.process_sale(invoice_data, items_data)
            
            # Handle recurring subscriptions
            from .services import create_subscriptions
            create_subscriptions(invoice_data, items_data)
            
            return JsonResponse({'status': 'success', 'invoice_id': invoice.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'invalid method'})
