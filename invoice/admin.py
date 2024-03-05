from django.contrib import admin
from .models import InvoiceDetails, InvoiceProductDetails
# Register your models here.


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('company', 'invoice_number', 'invoice_type', 'appointment_date', 'status')
    exclude = ('is_deleted', 'deleted_at')
    readonly_fields = ('accounting_year', 'invoice_sequence', 'invoice_number', 'invoice_pdf_url', 'irn', 'box_label_url', 'ewb_number', 'e_invoice_url', 'eway_bill')
    search_fields = ('id', 'invoice_number', 'bill_to_party__gstin', 'bill_to_party__phone')
    autocomplete_fields = ('bill_to_party', 'ship_to_party')


class InvoiceProductAdmin(admin.ModelAdmin):
    exclude = ('deleted_at', 'is_deleted')
    autocomplete_fields = ('invoice', 'product')


admin.site.register(InvoiceDetails, InvoiceAdmin)
admin.site.register(InvoiceProductDetails, InvoiceProductAdmin)