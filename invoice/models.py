from django.db import models

# Custom Imports
from party.models import PartyDetails
from products.models import ProductMaster
from .choices import *
from .utils import get_invoice_number_from_type
from inboicing_system.core.mixins import AuditModelMixin

# Create your models here.

# from config import NEXT_PUBLIC_FILE_REPO_URL


class InvoiceDetails(AuditModelMixin):
    """
    Invoice Model to store invoice data
    Completing this would have created a draft invoice with partial data
    """

    company = models.CharField(
        max_length=256, default="YOUR COMPANY", blank=False, null=False
    )
    accounting_year = models.IntegerField(default=0, blank=True, null=True)
    invoice_sequence = models.IntegerField(blank=True, null=True)
    invoice_number = models.CharField(max_length=30, blank=True, null=True, unique=True)
    marketplace = models.CharField(
        choices=MarketPlaces.choices, max_length=50, blank=True, null=True
    )
    invoice_type = models.CharField(
        choices=InvoiceTypes.choices, max_length=50, blank=True, null=True
    )
    invoice_date = models.DateField(blank=True, null=True)
    transport_mode = models.CharField(
        choices=TransportTypes.choices, max_length=25, blank=True, null=True
    )
    mode_of_payment = models.CharField(
        choices=PaymentModes.choices, max_length=25, blank=True, null=True
    )
    seller = models.ForeignKey(
        PartyDetails,
        related_name="seller_to_invoices",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    bill_to_party = models.ForeignKey(
        PartyDetails,
        related_name="bill_to_invoices",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    ship_to_party = models.ForeignKey(
        PartyDetails,
        related_name="ship_to_invoices",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    place_of_supply = models.CharField(max_length=50, blank=True, null=True)
    city_of_supply = models.CharField(max_length=50, blank=True, null=True)
    invoice_total = models.IntegerField(default=0, blank=True, null=True)
    eway_bill = models.URLField(max_length=256, blank=True, null=True)
    appointment_date = models.DateField(blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        choices=InvoiceStatus.choices, max_length=50, blank=True, null=True
    )
    awb_number = models.IntegerField(blank=True, null=True)
    courier_partner = models.CharField(max_length=50, blank=True, null=True)
    aw_vw = models.CharField(max_length=50, blank=True, null=True)
    invoice_pdf_url = models.URLField(max_length=256, blank=True, null=True)
    e_invoice_url = models.URLField(max_length=256, blank=True, null=True)
    box_label_url = models.URLField(max_length=256, blank=True, null=True)
    ewb_number = models.BigIntegerField(default=0, blank=True, null=True)
    irn = models.CharField(max_length=256, blank=True, null=True)
    transport_id = models.CharField(max_length=50, blank=True, null=True)
    transport_name = models.CharField(max_length=50, blank=True, null=True)
    transport_vehicle = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Invoices"
        ordering = ("-invoice_date", "-appointment_date")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_type = self.invoice_type

    @property
    def products(self):
        from .serializers import InvoiceProductsDetailSerializer

        return InvoiceProductsDetailSerializer(
            self.product_details.all(), many=True
        ).data

    def complete_invoice_url(self):
        if self.invoice_pdf_url:
            return self.invoice_pdf_url
        return None

    def complete_box_label_url(self):
        if self.box_label_url:
            return self.box_label_url
        return None

    def complete_e_invoice_url(self):
        if self.e_invoice_url:
            return self.e_invoice_url
        return None

    def complete_ewaybill_url(self):
        if self.eway_bill:
            return self.eway_bill
        return None

    def get_total_mrp_amount(self):
        products = self.product_details.all()
        return sum([product.get_total_mrp() for product in products])

    def get_total_invoice_amount(self):
        products = self.product_details.all()
        return sum([product.net_amount for product in products])

    def get_total_taxable_amount(self):
        products = self.product_details.all()
        return sum([product.taxable_amount for product in products])

    def get_total_discount_amount(self):
        total_mrp = self.get_total_mrp_amount()
        pre_tax_amount = self.get_total_taxable_amount()
        return total_mrp - pre_tax_amount

    def get_total_tax_amount(self):
        products = self.product_details.all()
        return sum([product.total_tax for product in products])

    def get_individual_tax_json(self):
        products = self.product_details.all()

        if products[0].tax_type == "igst":
            taxes = {
                "cgst": 0,
                "sgst": 0,
                "igst": sum([product.igst for product in products]),
            }
        else:
            tax = sum([product.cgst for product in products])
            taxes = {"cgst": tax, "sgst": tax, "igst": 0}
        return taxes

    def save(self, *args, **kwargs):
        if (
            not self.invoice_number and self.invoice_type
        ) or self.invoice_type != self.__original_type:
            num, seq, finyear = get_invoice_number_from_type(self)
            self.invoice_number = num
            self.invoice_sequence = seq
            self.accounting_year = finyear

        if products_list := self.product_details.all():
            invoice_total = 0
            for product in products_list:
                invoice_total += product.net_amount
            self.invoice_total = invoice_total

        super(InvoiceDetails, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number}"


class InvoiceProductDetails(AuditModelMixin):
    """
    Product Level entries for Invoice
    One Invoice can have multiple product entries
    """

    invoice = models.ForeignKey(
        InvoiceDetails,
        related_name="product_details",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        ProductMaster,
        related_name="invoice_detail",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    batch = models.CharField(max_length=50, blank=True, null=True)
    expiry = models.DateField(blank=True, null=True)
    po = models.CharField(max_length=30, blank=True, null=True)
    po_date = models.DateField(blank=True, null=True)
    discount_percent = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mrp = models.IntegerField(blank=True, null=True)
    gst_percent = models.IntegerField(blank=True, null=True)
    hsn_code = models.IntegerField(blank=True, null=True)
    tax_type = models.CharField(
        choices=TaxTypes.choices, max_length=30, blank=True, null=True
    )
    igst = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    cgst = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    sgst = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    taxable_amount = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    total_tax = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    net_amount = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    status = models.CharField(max_length=50, blank=True, null=True)
    box_qty = models.IntegerField(blank=True, null=True)
    box_contents = models.CharField(max_length=256, blank=True, null=True)
    box_no = models.IntegerField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Invoice Products Details"

    def get_total_mrp(self):
        return self.mrp * self.box_qty

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.product.product_name}"
