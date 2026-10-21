from django.db import transaction
from inventory.models import Medicine, Batch
from sales.models import SalesInvoice, SalesItem
from decimal import Decimal, ROUND_HALF_UP
import math
from datetime import date

class DispensingService:
    @staticmethod
    @transaction.atomic
    def process_sale(invoice_data, items_data):
        """
        Process a sale using FEFO (First-Expire-First-Out) with strict loose pricing rules,
        GST compliance, and Schedule H/H1 validations.
        """
        # Validate Schedule H/H1 requirements
        requires_compliance = False
        for item in items_data:
            med = Medicine.objects.get(id=item['medicine_id'])
            if med.schedule_type in ['H', 'H1', 'X']:
                requires_compliance = True
                break
                
        if requires_compliance:
            if not invoice_data.get('customer_name_manual') or not invoice_data.get('patient_address') or not invoice_data.get('doctor_name') or not invoice_data.get('doctor_reg_no'):
                raise ValueError("Mandatory Patient Demographics and Doctor Registration No are required for Schedule H/H1/X drugs.")

        is_interstate = invoice_data.get('is_interstate', False)

        invoice = SalesInvoice.objects.create(
            invoice_number=invoice_data['invoice_number'],
            customer_name_manual=invoice_data.get('customer_name_manual', ''),
            customer_phone=invoice_data.get('customer_phone', ''),
            patient_age=invoice_data.get('patient_age'),
            patient_address=invoice_data.get('patient_address', ''),
            doctor_name=invoice_data.get('doctor_name', ''),
            doctor_reg_no=invoice_data.get('doctor_reg_no', ''),
            is_interstate=is_interstate,
            payment_method=invoice_data.get('payment_method', 'CASH'),
            discount=Decimal(str(invoice_data.get('discount', 0))),
            is_paid=(invoice_data.get('payment_method') != 'CREDIT')
        )

        cart_subtotal = Decimal('0.00')
        total_cogs = Decimal('0.00')
        
        inv_taxable = Decimal('0.00')
        inv_cgst = Decimal('0.00')
        inv_sgst = Decimal('0.00')
        inv_igst = Decimal('0.00')

        for item_data in items_data:
            med = Medicine.objects.get(id=item_data['medicine_id'])
            quantity = int(item_data.get('quantity', 0))
            loose = int(item_data.get('loose', 0))
            units_per_pack = med.units_per_pack
            gst_rate = med.gst_rate
            
            total_req_base = (quantity * units_per_pack) + loose
            
            if total_req_base <= 0:
                continue

            # Lock batches using select_for_update. Filter out expired batches.
            batches = list(Batch.objects.select_for_update().filter(
                medicine=med, quantity__gt=0, expiry_date__gt=date.today()
            ).order_by('expiry_date'))

            units_remaining = total_req_base
            item_line_total = Decimal('0.00')
            item_unit_cogs = Decimal('0.00')
            item_rate = Decimal('0.00')

            for batch in batches:
                if units_remaining <= 0:
                    break
                    
                deduct_qty = min(units_remaining, batch.quantity)
                batch.quantity -= deduct_qty
                batch.save()
                
                # Formula implementation
                rate = Decimal(batch.selling_price)
                loose_unit_rate = round(rate / Decimal(units_per_pack), 2)
                
                if deduct_qty == total_req_base:
                    full_pack_amount = Decimal(quantity) * rate
                    loose_amount = Decimal(loose) * loose_unit_rate
                    val = full_pack_amount + loose_amount
                    cogs_val = Decimal(quantity) * Decimal(batch.purchase_price) + Decimal(loose) * round(Decimal(batch.purchase_price)/Decimal(units_per_pack), 2)
                    item_rate = rate
                else:
                    val = Decimal(deduct_qty) * loose_unit_rate
                    cogs_val = Decimal(deduct_qty) * round(Decimal(batch.purchase_price)/Decimal(units_per_pack), 2)
                    item_rate = rate

                item_line_total += val
                item_unit_cogs += cogs_val
                units_remaining -= deduct_qty
                
                # GST Reverse Calculation (MRP is inclusive of taxes)
                taxable = round(val / (1 + (gst_rate / Decimal('100'))), 2)
                tax_amt = val - taxable
                
                cgst = Decimal('0.00')
                sgst = Decimal('0.00')
                igst = Decimal('0.00')
                
                if is_interstate:
                    igst = tax_amt
                else:
                    cgst = round(tax_amt / 2, 2)
                    sgst = tax_amt - cgst
                    
                inv_taxable += taxable
                inv_cgst += cgst
                inv_sgst += sgst
                inv_igst += igst

                SalesItem.objects.create(
                    invoice=invoice,
                    batch=batch,
                    base_units=deduct_qty, 
                    quantity=quantity if deduct_qty == total_req_base else 0,
                    loose=loose if deduct_qty == total_req_base else deduct_qty,
                    rate=item_rate,
                    hsn_code=med.hsn_code,
                    gst_rate=gst_rate,
                    taxable_value=taxable,
                    cgst_amount=cgst,
                    sgst_amount=sgst,
                    igst_amount=igst,
                    line_total=val,
                    unit_cogs=cogs_val
                )

            if units_remaining > 0:
                raise ValueError(f"Insufficient unexpired stock for {med.name}. Short by {units_remaining} base units.")

            cart_subtotal += item_line_total
            total_cogs += item_unit_cogs

        discount_amount = invoice.discount
        discounted_total = max(Decimal('0.00'), cart_subtotal - discount_amount)
        final_payable_price = discounted_total.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        round_off_amount = final_payable_price - discounted_total
        
        invoice.subtotal = cart_subtotal
        invoice.net_amount = final_payable_price
        invoice.round_off = round_off_amount
        invoice.total_cogs = total_cogs
        invoice.total_taxable_value = inv_taxable
        invoice.total_cgst = inv_cgst
        invoice.total_sgst = inv_sgst
        invoice.total_igst = inv_igst
        invoice.save()

        return invoice
