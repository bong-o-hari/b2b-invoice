from django.urls import path
from .views import *

urlpatterns = [
    path("market-places/", get_marketplace_list, name="marketplace-list"),
    path("invoice-types/", get_invoice_types_list, name="invoicetype-list"),
    path("transport-types/", get_transport_types_list, name="transporttype-list"),
    path("payment-modes/", get_payment_mode_list, name="paymentmodes-list"),
    path("invoice-duplicate/<int:invoice_id>", invoice_duplicate, name="invoice-duplicate"),
    path("invoice-pdf/<int:invoice_id>", create_invoice_pdf, name="invoice-as-pdf"),
    path("box-pdf/<int:invoice_id>", create_box_label_pdf, name="boxes-as-pdf"),
    path("e-invoice/<int:invoice_id>", generate_e_invoice, name="generate-e-invoice"),
    path("ewaybill/<int:invoice_id>", generate_ewaybill, name="generate-ewaybill"),
    path("invoice-upload/", InvoiceBulkUploadView.as_view(), name="invoice-bulk"),
    path("invoice-creation/", InvoiceCreateView.as_view(), name="invoice-creation"),
    path("invoice-dashboard/", InvoiceDashboardListView.as_view(), name="invoice-dashboard"),
    path("invoice-detail/<int:invoice_id>", InvoiceDetailView.as_view(), name="invoice-detail"),
    path("invoice-products/", InvoiceProductsAddView.as_view(), name="invoice-add-products"),
]