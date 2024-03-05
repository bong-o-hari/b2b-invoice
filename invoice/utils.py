import simplejson as json
import pdfkit
from inboicing_system.settings import logger
from django.template.loader import render_to_string
from fiscalyear import *
from datetime import datetime
from party.utils import get_party_by_id
from .choices import *
from products.utils import get_product_from_id
from party.utils import get_party_by_id
from .constants import invoice_number_starter_point


def get_invoice_by_id(invoice_id):
    from .models import InvoiceDetails

    if invoice_id and (
        invoice := InvoiceDetails.objects.get(id=invoice_id, is_deleted=False)
    ):
        return invoice
    return None


def get_accounting_year(year, invoice_date):
    fiscal_range = FiscalYear(year)
    if invoice_date > fiscal_range.end.date():
        return get_accounting_year(year + 1, invoice_date)
    elif invoice_date < fiscal_range.start.date():
        return get_accounting_year(year - 1, invoice_date)
    elif fiscal_range.start.date() < invoice_date < fiscal_range.end.date():
        return abs(year) % 100


def get_last_invoice_number_from_type(invoice_type):
    from .models import InvoiceDetails

    invoice = (
        InvoiceDetails.objects.filter(invoice_type=invoice_type)
        .order_by("-invoice_sequence")
        .first()
    )
    return invoice


def get_invoice_number_from_type(curr_invoice):
    last_invoice = get_last_invoice_number_from_type(
        invoice_type=curr_invoice.invoice_type
    )

    if last_invoice:
        value_list = last_invoice.invoice_number.split("-")
        seq = value_list[0]
        seq_num = str(last_invoice.invoice_sequence + 1).zfill(5)
    else:
        seq_num = str(invoice_number_starter_point[curr_invoice.invoice_type]).zfill(5)
        seq = curr_invoice.invoice_type

    year = curr_invoice.invoice_date.year
    accounting_year = get_accounting_year(year, curr_invoice.invoice_date)

    return f"{seq}-{accounting_year}-{seq_num}", int(seq_num), accounting_year


def create_invoice_from_data(data):
    from .models import InvoiceDetails

    try:
        marketplace = data.get("marketplace")
        invoicetype = data.get("invoice_type")
        invoicedate = data.get("invoice_date")
        transportmode = data.get("transport_mode")
        paymentmode = data.get("mode_of_payment")
        seller = get_party_by_id(data.get("seller_id"))
        billtoparty = get_party_by_id(data.get("bill_to_id"))
        shiptoparty = get_party_by_id(data.get("ship_to_id"))
        appointmentdate = data.get("appointment_date", "")

        logger.info(f"CREATE INVOICE FROM DATA: {data}")

        invoice = InvoiceDetails(
            marketplace=MarketPlaces[marketplace],
            invoice_type=InvoiceTypes[invoicetype],
            invoice_date=datetime.strptime(invoicedate, "%Y-%m-%d").date(),
            transport_mode=TransportTypes[transportmode],
            mode_of_payment=PaymentModes[paymentmode],
            seller=seller,
            bill_to_party=billtoparty,
            ship_to_party=shiptoparty,
            place_of_supply=data.get("place_of_supply", ""),
            city_of_supply=data.get("city_of_supply", ""),
            status=InvoiceStatus.DRAFT,
        )

        if appointmentdate:
            invoice.appointment_date = datetime.strptime(
                appointmentdate, "%Y-%m-%d"
            ).date()

        invoice.save()
        return invoice

    except Exception as err:
        logger.error(
            f"CREATE INVOICE FROM DATA: Something went wrong! {str(err)} INVOICE DATA: {data}"
        )
        return None


def add_products_to_invoice(invoice_id, products_list):
    boxes = 0
    try:
        invoice = get_invoice_by_id(invoice_id=invoice_id)
        if invoice:
            for product in products_list:
                loose = 0
                product_obj = get_product_from_id(product_id=product.get("id"))

                if product_obj:
                    qty = product.get("quantity")
                    boxes += qty // product_obj.primary_box_qty
                    loose = qty % product_obj.primary_box_qty

                    logger.info(
                        f"ADD PRODUCT TO INVOICE: Passing values to add_product_to_invoice PRODUCT JSON: {product} INVOICE: {invoice.invoice_number}"
                    )
                    add_product_to_invoice(invoice, product_obj, product, boxes, loose)

            return invoice
    except Exception as err:
        logger.error(f"ADD PRODUCT TO INVOICE: Something went wrong! ERROR: {str(err)}")
        return None


def update_invoice_data(invoice, invoice_json):
    try:
        invoicetype = invoice_json.get("invoice_type", None)
        seller = get_party_by_id(invoice_json.get("seller_id", None))
        billtoparty = get_party_by_id(invoice_json.get("bill_to_id", None))
        shiptoparty = get_party_by_id(invoice_json.get("ship_to_id", None))
        appointmentdate = invoice_json.get("appointment_date", None)
        deliverydate = invoice_json.get("delivery_date", None)
        awb_number = invoice_json.get("awb_number", None)
        courier_partner = invoice_json.get("courier_partner", None)
        aw_vw = invoice_json.get("aw_vw", None)
        transport_id = invoice_json.get("transport_id", None)
        transport_name = invoice_json.get("transport_name", None)
        transport_vehicle = invoice_json.get("transport_vehicle", None)

        if invoicetype:
            invoice.invoice_type = InvoiceTypes[invoicetype] or invoice.invoice_type

        invoice.seller = seller or invoice.seller
        invoice.bill_to_party = billtoparty or invoice.bill_to_party
        invoice.ship_to_party = shiptoparty or invoice.ship_to_party
        invoice.courier_partner = courier_partner or invoice.courier_partner
        invoice.aw_vw = aw_vw or invoice.aw_vw
        invoice.status = InvoiceStatus.PROCESSED

        if appointmentdate:
            logger.info(f"Adding appointment date to invoice {invoice.invoice_number}")
            invoice.appointment_date = datetime.strptime(
                appointmentdate, "%Y-%m-%d"
            ).date()
            invoice.status = InvoiceStatus.ACCEPTED
        if deliverydate:
            logger.info(f"Adding delivery date to invoice {invoice.invoice_number}")
            invoice.delivery_date = datetime.strptime(deliverydate, "%Y-%m-%d").date()
            invoice.status = InvoiceStatus.IN_TRANSIT
        if awb_number:
            logger.info(f"Adding awb number to invoice {invoice.invoice_number}")
            invoice.awb_number = awb_number
            invoice.status = InvoiceStatus.IN_TRANSIT
        if transport_vehicle or transport_id or transport_name:
            logger.info(f"Adding transport details to invoice {invoice.invoice_number}")
            invoice.transport_vehicle = transport_vehicle or invoice.transport_vehicle
            invoice.transport_id = transport_id or invoice.transport_id
            invoice.transport_name = transport_name or invoice.transport_name
            invoice.status = InvoiceStatus.IN_TRANSIT

        invoice.save()
        return invoice

    except Exception as err:
        logger.error(
            f"UPDATE INVOICE DATA: Something went wrong while updating invoice object! INVOICE: {invoice_json} ERROR: {str(err)}"
        )


def get_tax(to_state, supply_state, rate, gst_percent, box_qty):
    taxes = {"igst": 0, "cgst": 0, "sgst": 0}

    tax = (box_qty * rate) * (gst_percent / 100)

    if to_state.replace(" ", "").lower() == supply_state.replace(" ", "").lower():
        taxes["cgst"] = tax / 2
        taxes["sgst"] = tax / 2
        return TaxTypes.COMBINED, taxes
    taxes["igst"] = tax
    return TaxTypes.IGST, taxes


def get_last_box_no(last_product):
    last_box = last_product.values_list("box_no").first()[0]
    return last_box


def add_product_to_invoice(invoice, product, product_json, boxes=0, loose=0):
    from .models import InvoiceProductDetails
    from .utils import get_last_product_for_invoice

    try:
        last_box = 0
        last_product = get_last_product_for_invoice(invoice)
        if last_product:
            last_box = get_last_box_no(last_product)

        discount = product_json.get("discount", 0.0)
        expiry = product_json.get("expiry")
        po_date = product_json.get("po_date")
        rate = product.mrp - (product.mrp * (discount / 100))
    except Exception as err:
        logger.error(
            f"DIVIDING PRODUCTS FOR INVOICE: Data fetching or Last box detail failed! PRODUCT: {product_json} ERROR: {str(err)}"
        )

    try:
        tax_type, tax = get_tax(
            invoice.bill_to_party.state,
            invoice.place_of_supply,
            rate,
            product.gst_percent,
            product.primary_box_qty,
        )
        total_tax = sum(tax.values())
    except Exception as err:
        logger.error(
            f"DIVIDING PRODUCTS FOR INVOICE: Tax calculation failed! ERROR: {str(err)}"
        )

    try:
        for i in range(boxes):
            taxable_amount = rate * product.primary_box_qty

            invoice_product = InvoiceProductDetails(
                invoice=invoice,
                product=product,
                mrp=product.mrp,
                discount_percent=discount,
                rate=rate,
                expiry=datetime.strptime(expiry, "%Y-%m-%d"),
                po=product_json.get("po", ""),
                po_date=datetime.strptime(po_date, "%Y-%m-%d"),
                gst_percent=product.gst_percent,
                hsn_code=product.hsn_code,
                tax_type=tax_type,
                igst=tax["igst"],
                cgst=tax["cgst"],
                sgst=tax["sgst"],
                taxable_amount=taxable_amount,
                total_tax=total_tax,
                net_amount=taxable_amount + total_tax,
                status=product_json.get("status", ""),
                box_no=last_box + i + 1,
                box_qty=product.primary_box_qty,
                box_contents=f"{product.product_name} x {product.primary_box_qty}",
            )
            invoice_product.save()
    except Exception as err:
        logger.error(
            f"DIVIDING PRODUCTS FOR INVOICE: Box addition failed! ERROR: {str(err)}"
        )

    try:
        if loose:
            tax_type, tax = get_tax(
                invoice.bill_to_party.state,
                invoice.place_of_supply,
                rate,
                product.gst_percent,
                loose,
            )
            total_tax = sum(tax.values())
            taxable_amount = rate * loose

            invoice_product = InvoiceProductDetails(
                invoice=invoice,
                product=product,
                mrp=product.mrp,
                discount_percent=discount,
                rate=rate,
                expiry=datetime.strptime(expiry, "%Y-%m-%d"),
                po=product_json.get("po", ""),
                po_date=datetime.strptime(po_date, "%Y-%m-%d"),
                gst_percent=product.gst_percent,
                hsn_code=product.hsn_code,
                tax_type=tax_type,
                igst=tax["igst"],
                cgst=tax["cgst"],
                sgst=tax["sgst"],
                taxable_amount=taxable_amount,
                total_tax=total_tax,
                net_amount=taxable_amount + total_tax,
                status=product_json.get("status", ""),
                box_no=0,
                box_qty=loose,
                box_contents=f"{product.product_name} x {loose}",
            )
            invoice_product.save()
    except Exception as err:
        logger.error(
            f"DIVIDING PRODUCTS FOR INVOICE: Loose addition failed! ERROR {str(err)}"
        )


def create_draft_invoice(invoice_data):
    from .models import InvoiceDetails

    invoice_date = invoice_data.get("invoice_date")

    try:
        logger.info(
            f"CREATE DRAFT INVOICE: Creating Invoice Object INVOICE DATA: {invoice_data}"
        )
        invoice = InvoiceDetails(
            marketplace=invoice_data.get("marketplace"),
            invoice_date=datetime.strptime(invoice_date, "%Y-%m-%d"),
            transport_mode=invoice_data.get("transport_mode"),
            mode_of_payment=invoice_data.get("mode_of_payment"),
            place_of_supply=invoice_data.get("place_of_supply"),
            status=InvoiceStatus.DRAFT,
        )

        invoice.save()
        logger.info(f"CREATE DRAFT INVOICE: Created Invoice Object {invoice.id}")
    except Exception as err:
        logger.error(
            f"CREATE DRAFT INVOICE: Saving object failed! INVOICE DATA: {invoice_data} ERROR: {str(err)}"
        )
        return False
    return True


def get_last_product_for_invoice(invoice):
    from .models import InvoiceProductDetails

    try:
        logger.info(f"GET LAST BOX INFO FOR INVOICE: {invoice.invoice_number}")
        last_product = InvoiceProductDetails.objects.filter(invoice=invoice).order_by(
            "-box_no"
        )
        return last_product
    except Exception as err:
        logger.error(
            f"GET LAST BOX INFO FOR INVOICE: {invoice.invoice_number} ERROR: {str(err)}"
        )


def generate_invoice_html(invoice_object):
    from num2words import num2words

    try:
        last_product = get_last_product_for_invoice(invoice_object)
        last_box = get_last_box_no(last_product)
    except Exception as err:
        logger.error(
            f"GENERATE INVOICE HTML: Something went wrong in fetching last box details INVOICE: {invoice_object.invoice_number} ERROR: {str(err)}"
        )

    try:
        products = invoice_object.product_details.order_by("box_no").all()
        net_amount = invoice_object.get_total_invoice_amount()
        net_amount_str = num2words(int(net_amount), lang="en_IN")

        invoice_data = {
            "invoice": invoice_object,
            "products": products,
            "po": products[0].po,
            "today": datetime.now().date().strftime("%d/%m/%Y"),
            "last_box": last_box,
            "discount_total": invoice_object.get_total_discount_amount(),
            "sub_total": invoice_object.get_total_taxable_amount(),
            "tax_total": invoice_object.get_total_tax_amount(),
            "net_amount": net_amount,
            "igst": products[0].igst,
            "net_amount_str": net_amount_str.title(),
        }

        if appt_date := invoice_object.appointment_date:
            invoice_data["appointment_date"] = appt_date.strftime("%d/%m/%Y")

        logger.info(
            f"GENERATE INVOICE HTML: Invoice json created, sending to render INVOICE: {invoice_object.invoice_number}"
        )

        generated_invoice_html = render_to_string("invoice/main.html", invoice_data)
        return generated_invoice_html
    except Exception as err:
        logger.error(
            f"GENERATE INVOICE HTML: Something went wrong while rendering html INVOICE: {invoice_object.invoice_number} ERROR: {str(err)}"
        )


def generate_box_label_pdfs(invoice_object):
    products = invoice_object.product_details.order_by("box_no").all()

    try:
        pdf_list = []
        product_details_list = []

        for product in products:
            per_product = {}
            box_number = product.box_no

            if product_details_list and len(product_details_list) == box_number:
                box_index = product_details_list[box_number - 1]
                box_index["box_contents"].append(
                    f"{product.box_contents}, ({product.batch})"
                )
            else:
                per_product["id"] = product.id
                per_product["box_no"] = product.box_no
                per_product["batch"] = product.batch
                per_product["invoice_number"] = product.invoice.invoice_number
                per_product["party_name"] = product.invoice.ship_to_party.name
                per_product["party_address"] = product.invoice.ship_to_party.address
                per_product["party_phone"] = product.invoice.ship_to_party.phone
                per_product["box_contents"] = [
                    f"{product.box_contents}, ({product.batch})"
                ]

                product_details_list.insert(box_number - 1, per_product)

        for product_detail in product_details_list:
            product_details = {
                "product": product_detail,
                "date": datetime.now().date().strftime("%d/%m/%Y"),
            }
            generated_box_label_html = render_to_string(
                "boxes/main.html", product_details
            )
            file_name = str(product_detail["id"]) + ".pdf"
            pdfkit.from_string(generated_box_label_html, file_name)
            pdf_list.append(file_name)

        logger.info(
            f"GENERATE BOX LABEL HTML: Box label json created, sending to merger INVOICE: {invoice_object.invoice_number}"
        )
        return pdf_list
    except Exception as err:
        logger.error(
            f"GENERATE BOX LABEL HTML: Something went wrong while rendering html INVOICE: {invoice_object.invoice_number} ERROR: {str(err)}"
        )


def get_distance_between_pincodes(pincode1, pincode2):
    import pgeocode

    dist = pgeocode.GeoDistance("in")
    return int(dist.query_postal_code(str(pincode1), str(pincode2)))


def get_dispatch_details(seller):
    dispatch_details = {
        "Nm": seller.name,
        "Addr1": seller.address,
        "Loc": seller.city,
        "Pin": seller.pincode,
        "Stcd": str(seller.state_code),
    }
    return dispatch_details


def get_seller_details(seller):
    seller_details = {
        "Gstin": seller.gstin,
        "LglNm": seller.name,
        "TrdNm": seller.name,
        "Addr1": seller.address,
        "Loc": seller.city,
        "Pin": seller.pincode,
        "Stcd": str(seller.state_code),
        "Ph": seller.phone,
        "Em": "care@youremail.com",
    }
    return seller_details


def get_buyer_details(ship_to_party):
    buyer_details = {
        "Gstin": ship_to_party.gstin,
        "LglNm": ship_to_party.name,
        "Pos": str(ship_to_party.state_code),
        "Addr1": ship_to_party.address,
        "Loc": ship_to_party.city,
        "Pin": ship_to_party.pincode,
        "Stcd": str(ship_to_party.state_code),
        "Ph": ship_to_party.phone,
    }
    return buyer_details


def get_ship_details(ship_to_party, ewb_fields=False):
    if not ewb_fields:
        ship_details = {
            "Gstin": ship_to_party.gstin,
            "LglNm": ship_to_party.name,
            "Addr1": ship_to_party.address,
            "Loc": ship_to_party.city,
            "Pin": ship_to_party.pincode,
            "Stcd": str(ship_to_party.state_code),
        }
    else:
        ship_details = {
            "Addr1": ship_to_party.address,
            "Loc": ship_to_party.city,
            "Pin": ship_to_party.pincode,
            "Stcd": str(ship_to_party.state_code),
        }
    return ship_details


def get_value_details(invoice):
    taxes_json = invoice.get_individual_tax_json()
    value_details = {
        "AssVal": invoice.get_total_taxable_amount(),
        "CgstVal": taxes_json["cgst"],
        "SgstVal": taxes_json["sgst"],
        "IgstVal": taxes_json["igst"],
        "TotInvVal": invoice.get_total_invoice_amount(),
    }
    return value_details


def get_item_list(invoice):
    items_list = []
    for index, product_detail in enumerate(
        invoice.product_details.order_by("box_no").all()
    ):
        total_discount = (
            product_detail.mrp - product_detail.rate
        ) * product_detail.box_qty
        item = {
            "SlNo": index + 1,
            "PrdDesc": product_detail.product.product_name,
            "IsServc": "N",
            "HsnCd": product_detail.product.hsn_code,
            "Qty": product_detail.box_qty,
            "Unit": "BOX",
            "UnitPrice": product_detail.rate,
            "TotAmt": product_detail.get_total_mrp(),
            "Discount": total_discount,
            "PreTaxVal": product_detail.taxable_amount,
            "AssAmt": product_detail.taxable_amount,
            "GstRt": product_detail.gst_percent,
            "IgstAmt": product_detail.igst,
            "CgstAmt": product_detail.cgst,
            "SgstAmt": product_detail.sgst,
            "TotItemVal": product_detail.net_amount,
            "OrgCntry": "IN",
            "BchDtls": {"Nm": product_detail.batch},
            "AttribDtls": [
                {
                    "Nm": product_detail.box_contents,
                }
            ],
        }
        items_list.append(item)
    return items_list


def generate_cleartax_data(invoice):

    data = {
        "transaction": {
            "Version": "1.1",
            "TranDtls": {"TaxSch": "GST", "SupTyp": "B2B"},
            "DocDtls": {
                "Typ": "INV",
                "No": invoice.invoice_number,
                "Dt": datetime.now().date().strftime("%d/%m/%Y"),
            },
        }
    }
    data_dict = data["transaction"]

    seller_details = get_seller_details(invoice.seller)
    data_dict["SellerDtls"] = seller_details

    buyer_details = get_buyer_details(invoice.ship_to_party)
    data_dict["BuyerDtls"] = buyer_details

    dispatch_details = get_dispatch_details(invoice.seller)
    data_dict["DispDtls"] = dispatch_details

    ship_details = get_ship_details(invoice.ship_to_party)
    data_dict["ShipDtls"] = ship_details

    items_list = get_item_list(invoice)
    data_dict["ItemList"] = items_list

    value_details = get_value_details(invoice)
    data_dict["ValDtls"] = value_details

    data = json.dumps([data], use_decimal=True)
    return data


def generate_ewaybill_data(invoice):

    data = {
        "Irn": invoice.irn,
        "Distance": 0,
        "TransMode": "1",
        "TransId": invoice.transport_id,
        "TransName": "Transport" or invoice.transport_name,
        "TransDocDt": datetime.now().date().strftime("%d/%m/%Y"),
        "TransDocNo": invoice.invoice_number,
        "VehNo": invoice.transport_vehicle,
        "VehType": "R",
    }

    ship_details = get_ship_details(invoice.ship_to_party, ewb_fields=True)
    data["ExpShipDtls"] = ship_details

    dispatch_details = get_dispatch_details(invoice.seller)
    data["DispDtls"] = dispatch_details

    if ship_details["Pin"] == dispatch_details["Pin"]:
        data["Distance"] = get_distance_between_pincodes(
            ship_details["Pin"], dispatch_details["Pin"]
        )

    data = json.dumps([data], use_decimal=True)
    return data
