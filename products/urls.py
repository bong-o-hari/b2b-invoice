from django.urls import path
from .views import *

urlpatterns = [
    path("product-list/", ProductInvoiceSelectionView.as_view(), name="product-list"),
    path("product-create/", ProductCreationView.as_view(), name="product-list"),
    path("product-upload/", ProductBulkUploadView.as_view(), name="product-bulk"),
    path("product-csv/", get_products_csv, name="product-csv"),
    path("product-details/<int:product_id>", ProductInvoiceCompletionView.as_view(), name="product-detail"),
    path("product-search/<name>", get_product_list, name="party-search"),
]