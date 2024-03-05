from django.db import models


class TaxTypes(models.TextChoices):
    IGST = "igst"
    COMBINED = "cgst+sgst"


class MarketPlaces(models.TextChoices):
    ONE_MG = "1mg"
    AMAZON = "Amazon"
    BIG_BASKET = "BigBasket"
    FLIPKART = "Flipkart"
    MEESHO = "Meesho Offline"
    MENXP = "MenXP"
    MY_UPCHAR = "MyUpchar"
    PAYTM = "PayTM"
    PHARMEASY = "Pharmeasy"
    PURPLLE = "Purplle"
    SHOPIFY = "Shopify"
    SHOPIFY_2 = "Shopify_2"
    SNAPDEAL = "Snapdeal"
    CRED = "Cred"
    SHYKART = "Shykart"
    AAYU_CHEMIST = "Aayu Chemist"


class InvoiceTypes(models.TextChoices):
    B2B_TAX_INVOICE = "MJB2B"
    STOCK_TRANSFER = "MJST"
    DELIVERY_CHALLAN = "MJDC"
    TAX_INVOICE = "MJINV"
    CREDIT_NOTE = "MJCN"
    DEBIT_NOTE = "MJDN"
    PROFORMA_INVOICE = "MJ"
    SAMPLE = "MJSAM"
    PURCHASE_ORDER = "MJPO"
    PAYMENT_RECEIPT = "MJPR"


class TransportTypes(models.TextChoices):
    ROAD = "Road"
    AIR = "Air"


class PaymentModes(models.TextChoices):
    COD = "Cod"
    PREPAID = "Prepaid"
    CREDIT = "Credit"


class InvoiceStatus(models.TextChoices):
    DRAFT = "Draft"
    PROCESSED = "Processed"
    ACCEPTED = "Accepted for Fulfilment"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"
    RETURNED = "Returned"
