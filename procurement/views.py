from decimal import Decimal
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
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from itertools import chain
from .models import SupplierPayment, PurchaseReturn

@login_required
@role_required(['Admin', 'Pharmacist'])
def supplier_ledger(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    purchases = supplier.purchaseinvoice_set.all().order_by('-purchase_date')
    payments = supplier.payments.all().order_by('-date')
    returns = supplier.returns.all().order_by('-date')
    
    # Combine transactions into a ledger timeline
    ledger = []
    for p in purchases:
        ledger.append({'date': p.purchase_date, 'type': 'PURCHASE', 'ref': p.invoice_number, 'amount': p.total_amount, 'obj': p})
    for p in payments:
        ledger.append({'date': p.date, 'type': 'PAYMENT', 'ref': p.reference_number or p.payment_method, 'amount': -p.amount, 'obj': p})
    for r in returns:
        ledger.append({'date': r.date.date(), 'type': 'DEBIT NOTE', 'ref': r.debit_note_number, 'amount': -r.refund_amount, 'obj': r})
        
    ledger.sort(key=lambda x: x['date'], reverse=True)
    
    # Get batches that this supplier provided (by joining PurchaseItem)
    # Or just all batches for simplicity in the UI
    available_batches = Batch.objects.filter(quantity__gt=0)
    
    context = {
        'supplier': supplier,
        'ledger': ledger,
        'available_batches': available_batches,
    }
    return render(request, 'supplier_ledger.html', context)

@login_required
@role_required(['Admin'])
def supplier_payment_add(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        date = request.POST.get('date')
        payment_method = request.POST.get('payment_method')
        reference_number = request.POST.get('reference_number', '')
        remarks = request.POST.get('remarks', '')
        
        if amount > 0:
            SupplierPayment.objects.create(
                supplier=supplier, amount=amount, date=date, 
                payment_method=payment_method, reference_number=reference_number, remarks=remarks
            )
            supplier.pending_balance -= amount
            supplier.save()
            messages.success(request, f'Payment of Rs. {amount} recorded for {supplier.name}.')
        return redirect('supplier_ledger', supplier_id=supplier.id)
    return redirect('supplier_ledger', supplier_id=supplier.id)

@login_required
@role_required(['Admin', 'Pharmacist'])
def supplier_return_add(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    if request.method == 'POST':
        batch_id = request.POST.get('batch_id')
        qty = int(request.POST.get('quantity', 0))
        reason = request.POST.get('reason', '')
        debit_note = request.POST.get('debit_note_number', '')
        
        if qty > 0 and batch_id:
            batch = get_object_or_404(Batch, id=batch_id)
            if qty > batch.quantity:
                messages.error(request, 'Cannot return more than available stock.')
                return redirect('supplier_ledger', supplier_id=supplier.id)
                
            refund_amount = Decimal(qty) * batch.purchase_price
            PurchaseReturn.objects.create(
                supplier=supplier,
                batch=batch,
                quantity=qty,
                refund_amount=refund_amount,
                reason=reason,
                debit_note_number=debit_note
            )
            
            # Deduct stock and update supplier balance
            batch.quantity -= qty
            batch.save()
            
            supplier.pending_balance -= refund_amount
            supplier.save()
            
            messages.success(request, f'Debit Note {debit_note} created. Rs. {refund_amount} deducted from supplier balance.')
            
    return redirect('supplier_ledger', supplier_id=supplier.id)


import csv
from datetime import datetime

from django.http import HttpResponse
import csv

@login_required
@role_required(['Admin', 'Pharmacist'])
def download_grn_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="grn_import_template.csv"'
    writer = csv.writer(response)
    writer.writerow(['Medicine', 'Batch No.', 'Expiry Date', 'Qty (Base)', 'Pur. Price', 'MRP/Rate'])
    writer.writerow(['Paracetamol 500mg', 'BCH-101', '2027-12-31', '50', '10.50', '15.00'])
    return response

@login_required
@role_required(['Admin', 'Pharmacist'])
@csrf_exempt
def api_parse_grn_import(request):
    if request.method == 'POST':
        file = request.FILES.get('grn_import_file')
        if not file:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded'})
            
        try:
            # Decode CSV file
            decoded_file = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            
            parsed_items = []
            errors = []
            
            for index, row in enumerate(reader, start=2): # Row 1 is header
                drug_name = row.get('Medicine', '').strip()
                batch_no = row.get('Batch No.', '').strip()

                expiry = row.get('Expiry Date', '').strip()
                # Attempt to standardize date format to YYYY-MM-DD for HTML input
                try:
                    if expiry:
                        from dateutil import parser
                        parsed_date = parser.parse(expiry)
                        expiry = parsed_date.strftime('%Y-%m-%d')
                except:
                    pass

                qty = row.get('Qty (Base)', '').strip()
                p_price = row.get('Pur. Price', '').strip()
                mrp = row.get('MRP/Rate', '').strip()
                
                if not drug_name:
                    continue
                    
                # Find Medicine ID
                try:
                    med = Medicine.objects.get(name__iexact=drug_name)
                    parsed_items.append({
                        'medicine_id': med.id,
                        'medicine_name': med.name,
                        'batch_number': batch_no,
                        'expiry_date': expiry,
                        'quantity': qty,
                        'purchase_price': p_price,
                        'mrp': mrp,
                        'selling_price': mrp # Default selling price to MRP in the grid
                    })
                except Medicine.DoesNotExist:
                    errors.append(f"Row {index}: Drug '{drug_name}' not found in Drug Master.")
                except Medicine.MultipleObjectsReturned:
                    med = Medicine.objects.filter(name__iexact=drug_name).first()
                    parsed_items.append({
                        'medicine_id': med.id,
                        'medicine_name': med.name,
                        'batch_number': batch_no,
                        'expiry_date': expiry,
                        'quantity': qty,
                        'purchase_price': p_price,
                        'mrp': mrp,
                        'selling_price': mrp
                    })
                    
            return JsonResponse({'status': 'success', 'items': parsed_items, 'errors': errors})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})
