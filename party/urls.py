from django.urls import path
from .views import *

urlpatterns = [
    path("parties-list/", PartyInvoiceSelectionView.as_view(), name="party-list"),
    path("state-codes/", get_state_code_list, name="statecodes-list"),
    path("party-create/", PartyCreationView.as_view(), name="party-list"),
    path("party-upload/", PartyBulkUploadView.as_view(), name="party-bulk"),
    path("party-csv/", get_parties_csv, name="party-csv"),
    path("party-details/<int:party_id>", PartyInvoiceCompletionView.as_view(), name="party-detail"),
    path("party-search/<search_str>", get_parties_list, name="party-search"),
]