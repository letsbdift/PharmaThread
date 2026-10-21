from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError
from django.contrib.auth.decorators import login_required
from core.decorators import role_required
from .models import Supplier, PurchaseInvoice, PurchaseItem
from inventory.models import Medicine, Batch
import json

@login_required
@role_required(['Admin', 'Pharmacist'])
def supplier_list(request):
    if request.method == 'POST':
        Supplier.objects.create(
            name=request.POST.get('name'),
            contact_person=request.POST.get('contact_person', ''),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            gstin=request.POST.get('gstin', ''),
            address=request.POST.get('address', ''),
            payment_terms=request.POST.get('payment_terms', ''),
            credit_limit=request.POST.get('credit_limit', 0.00),
            is_active=request.POST.get('status', 'active') == 'active'
        )
        return redirect('supplier_list')
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'suppliers.html', {'suppliers': suppliers})

from django.core.serializers.json import DjangoJSONEncoder

@login_required
@role_required(['Admin', 'Pharmacist'])
def grn_entry(request):
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    suppliers_list = list(suppliers.values('id', 'name'))
    medicines = list(Medicine.objects.filter(is_active=True).values('id', 'name', 'category', 'schedule_type', 'hsn_code', 'gst_rate'))
    
    context = {
        'suppliers': suppliers,
        'suppliers_json': json.dumps(suppliers_list),
        'medicines_json': json.dumps(medicines, cls=DjangoJSONEncoder)
    }
    return render(request, 'grn.html', context)

@login_required
@role_required(['Admin', 'Pharmacist'])
@csrf_exempt
@transaction.atomic
def api_process_grn(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            supplier_id = data.get('supplier_id')
            invoice_number = data.get('invoice_number')
            purchase_date = data.get('purchase_date') or data.get('invoice_date')
            items = data.get('items', [])
            
            if not all([supplier_id, invoice_number, purchase_date, items]):
                raise ValueError("Missing mandatory GRN fields.")
            
            supplier = Supplier.objects.get(id=supplier_id)
            
            # Create Invoice
            invoice = PurchaseInvoice.objects.create(
                supplier=supplier,
                invoice_number=invoice_number,
                purchase_date=purchase_date,
                total_amount=0
            )
            
            total_amount = 0
            
            for item in items:
                med = Medicine.objects.get(id=item['medicine_id'])
                qty = int(item['quantity'])
                p_price = float(item['purchase_price'])
                mrp = float(item['mrp'])
                s_price = float(item.get('selling_price', mrp))
                
                # Create Purchase Item
                PurchaseItem.objects.create(
                    purchase_invoice=invoice,
                    medicine=med,
                    batch_number=item['batch_number'],
                    expiry_date=item['expiry_date'],
                    quantity=qty,
                    purchase_price=p_price,
                    mrp=mrp,
                    selling_price=s_price
                )
                
                # Base Stock Calculation
                base_qty = qty * med.units_per_pack
                
                # Update or Create Batch in Inventory
                batch, created = Batch.objects.get_or_create(
                    medicine=med,
                    batch_number=item['batch_number'],
                    defaults={
                        'expiry_date': item['expiry_date'],
                        'purchase_price': p_price,
                        'mrp': mrp,
                        'selling_price': s_price,
                        'quantity': 0
                    }
                )
                batch.quantity += base_qty
                batch.purchase_price = p_price
                batch.mrp = mrp
                batch.selling_price = s_price
                batch.save()
                
                total_amount += (qty * p_price)
                
            invoice.total_amount = total_amount
            invoice.save()
            
            # Update Supplier Balance
            supplier.pending_balance = float(supplier.pending_balance) + total_amount
            supplier.save()
            
            return JsonResponse({'status': 'success', 'message': 'GRN processed successfully', 'invoice_id': invoice.id})
        except IntegrityError:
            return JsonResponse({'status': 'error', 'message': 'An invoice with this number already exists for this supplier.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})

@login_required
@role_required(['Admin', 'Pharmacist'])
def api_supplier_history(request, supplier_id):
    invoices = PurchaseInvoice.objects.filter(supplier_id=supplier_id).order_by('-purchase_date')
    data = []
    for inv in invoices:
        data.append({
            'invoice_number': inv.invoice_number,
            'date': inv.purchase_date.strftime('%Y-%m-%d'),
            'amount': float(inv.total_amount)
        })
    return JsonResponse({'status': 'success', 'history': data})
