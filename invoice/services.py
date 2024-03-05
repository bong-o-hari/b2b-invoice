from .choices import *
from .models import InvoiceDetails, InvoiceProductDetails


def get_invoice_by_id(invoice_id):
    if invoice_id and (invoice := InvoiceDetails.objects.filter(id=invoice_id, is_deleted=False).first()):
        return invoice
    return None


def get_invoice_product_by_id(invoice_product_id):
    if invoice_product_id and (invoice_product := InvoiceProductDetails.objects.filter(id=invoice_product_id, is_deleted=False).first()):
        return invoice_product
    return None
