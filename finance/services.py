from django.db.models import Sum, F
from datetime import date
from sales.models import SalesInvoice, SalesReturn
from finance.models import Expense
from inventory.models import StockAdjustment, Batch

class FinancialService:
    @staticmethod
    def get_pnl(start_date=None, end_date=None):
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = date.today()

        # 1. Net Sales Revenue
        sales_invoices = SalesInvoice.objects.filter(date__date__gte=start_date, date__date__lte=end_date)
        gross_sales = sales_invoices.aggregate(total=Sum(F('subtotal')))['total'] or 0
        total_discounts = sales_invoices.aggregate(total=Sum(F('discount')))['total'] or 0

        cash_collection = sales_invoices.filter(payment_method='CASH').aggregate(total=Sum(F('net_amount')))['total'] or 0
        upi_collection = sales_invoices.filter(payment_method='UPI').aggregate(total=Sum(F('net_amount')))['total'] or 0
        card_collection = sales_invoices.filter(payment_method='CARD').aggregate(total=Sum(F('net_amount')))['total'] or 0
        due_collection = sales_invoices.filter(payment_method='CREDIT').aggregate(total=Sum(F('net_amount')))['total'] or 0


        sales_returns = SalesReturn.objects.filter(date__date__gte=start_date, date__date__lte=end_date)
        total_sales_returns = sales_returns.aggregate(total=Sum('refund_amount'))['total'] or 0

        net_sales_revenue = gross_sales - total_discounts - total_sales_returns

        # 2. Cost of Goods Sold (COGS)
        total_cogs = sales_invoices.aggregate(total=Sum('total_cogs'))['total'] or 0
        
        # COGS of Restocked Sales Returns
        restocked_returns = sales_returns.filter(restock_to_inventory=True)
        cogs_returned = 0
        for r in restocked_returns:
            cogs_returned += (r.quantity * r.batch.purchase_price)
            
        total_cogs = total_cogs - cogs_returned

        # 3. Gross Profit & Gross Margin
        gross_profit = net_sales_revenue - total_cogs
        gross_margin = (gross_profit / net_sales_revenue * 100) if net_sales_revenue > 0 else 0

        # 4. Operating Expenses (OPEX)
        expenses = Expense.objects.filter(date__gte=start_date, date__lte=end_date)
        total_opex = expenses.aggregate(total=Sum('amount'))['total'] or 0

        # 5. Inventory Expiry Losses
        adjustments = StockAdjustment.objects.filter(date__date__gte=start_date, date__date__lte=end_date, reason='EXPIRED')
        expiry_loss = 0
        for adj in adjustments:
            expiry_loss += (abs(adj.quantity_adjusted) * adj.batch.purchase_price)

        # 6. Net Profit & Net Margin
        net_profit = gross_profit - total_opex - expiry_loss
        net_margin = (net_profit / net_sales_revenue * 100) if net_sales_revenue > 0 else 0

        return {
            'gross_sales': float(gross_sales),
            'cash_collection': float(cash_collection),
            'upi_collection': float(upi_collection),
            'card_collection': float(card_collection),
            'due_collection': float(due_collection),
            'total_discounts': float(total_discounts),
            'total_sales_returns': float(total_sales_returns),
            'net_sales_revenue': float(net_sales_revenue),
            'total_cogs': float(total_cogs),
            'gross_profit': float(gross_profit),
            'gross_margin': float(gross_margin),
            'total_opex': float(total_opex),
            'expiry_loss': float(expiry_loss),
            'net_profit': float(net_profit),
            'net_margin': float(net_margin),
        }
