from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from reports.views import dashboard, receipt, export_stock_excel, export_sales_excel, db_backup, system_cleanup, export_pnl_excel, export_pnl_pdf, pnl_report, export_stock_pdf, export_sales_pdf, reports_hub, schedule_register
from inventory.views import medicine_list, medicine_add, medicine_edit, medicine_delete
from sales.views import pos, pos_checkout, api_customer_lookup, api_medicines_list
from procurement.views import supplier_list, grn_entry, api_process_grn, api_supplier_history

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', dashboard, name='dashboard'),
    path('pos/', pos, name='pos'),
    path('pos/checkout/', pos_checkout, name='pos_checkout'),
    path('pos/api/customer/', api_customer_lookup, name='api_customer_lookup'),
    path('pos/api/medicines/', api_medicines_list, name='api_medicines_list'),
    path('medicines/', medicine_list, name='medicine_list'),
    path('medicines/add/', medicine_add, name='medicine_add'),
    path('medicines/edit/<int:pk>/', medicine_edit, name='medicine_edit'),
    path('medicines/delete/<int:pk>/', medicine_delete, name='medicine_delete'),
    path('procurement/suppliers/', supplier_list, name='supplier_list'),
    path('procurement/api/supplier/<int:supplier_id>/history/', api_supplier_history, name='api_supplier_history'),
    path('procurement/grn/', grn_entry, name='grn_entry'),
    path('procurement/api/grn/submit/', api_process_grn, name='api_process_grn'),
    path('receipt/<int:invoice_id>/', receipt, name='receipt'),
    path('reports/', reports_hub, name='reports_hub'),
    path('reports/pnl/', pnl_report, name='pnl_report'),
    path('reports/schedule-register/', schedule_register, name='schedule_register'),
    path('export/stock/', export_stock_excel, name='export_stock'),
    path('export/stock/pdf/', export_stock_pdf, name='export_stock_pdf'),
    path('export/sales/', export_sales_excel, name='export_sales'),
    path('export/sales/pdf/', export_sales_pdf, name='export_sales_pdf'),
    path('export/pnl/excel/', export_pnl_excel, name='export_pnl_excel'),
    path('export/pnl/pdf/', export_pnl_pdf, name='export_pnl_pdf'),
    path('backup/', db_backup, name='db_backup'),
    path('cleanup/', system_cleanup, name='system_cleanup'),
]
