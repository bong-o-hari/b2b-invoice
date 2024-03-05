import csv
import io
from inboicing_system.settings import logger
from inboicing_system.core.permissions import *
from django.views.decorators.csrf import csrf_exempt
from inboicing_system.pagination import StandardResultsSetPagination
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .choices import *
from .services import get_invoice_by_id
from .utils import (
    create_invoice_from_data,
    add_products_to_invoice,
    update_invoice_data,
)
from .tasks import create_draft_invoice_task
from .serializers import *

# Create your views here.


@csrf_exempt
@api_view(["GET"])
def invoice_duplicate(request, invoice_id):
    invoice = get_invoice_by_id(invoice_id=invoice_id)
    if invoice:
        invoice.id = None
        invoice.invoice_number = None
        invoice.box_label_url = None
        invoice.e_invoice_url = None
        invoice.irn = None
        invoice.ewb_number = None
        invoice.invoice_pdf_url = None
        invoice.eway_bill = None
        invoice.save()
        serializer = InvoiceExpandedDetailSerializer(invoice)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )
    return Response(
        {"success": False, "data": f"Invoice by ID {invoice_id} does not exist!"},
        status=status.HTTP_400_BAD_REQUEST,
    )


@csrf_exempt
@api_view(["GET"])
def get_marketplace_list(request):
    from .choices import MarketPlaces

    market_places = MarketPlaces.names
    return Response(
        {"success": True, "choices": market_places}, status=status.HTTP_200_OK
    )


@csrf_exempt
@api_view(["GET"])
def get_invoice_types_list(request):
    from .choices import InvoiceTypes

    invoice_types = InvoiceTypes.names
    return Response(
        {"success": True, "choices": invoice_types}, status=status.HTTP_200_OK
    )


@csrf_exempt
@api_view(["GET"])
def get_transport_types_list(request):
    from .choices import TransportTypes

    transport_types = TransportTypes.names
    return Response(
        {"success": True, "choices": transport_types}, status=status.HTTP_200_OK
    )


@csrf_exempt
@api_view(["GET"])
def get_payment_mode_list(request):
    from .choices import PaymentModes

    payment_modes = PaymentModes.names
    return Response(
        {"success": True, "choices": payment_modes}, status=status.HTTP_200_OK
    )


@csrf_exempt
@api_view(["GET"])
def create_invoice_pdf(request, invoice_id):
    # from config import NEXT_PUBLIC_FILE_REPO_URL
    from .tasks import generate_invoice_pdf_task

    try:
        invoice = get_invoice_by_id(invoice_id=invoice_id)

        if not (invoice_pdf_path := invoice.invoice_pdf_url):
            invoice_pdf_path = generate_invoice_pdf_task(invoice_id=invoice_id)

        logger.info(
            f"CREATE INVOICE PDF: Generated pdf for invoice {invoice.invoice_number}"
        )
        return Response(
            {"success": True, "invoice_url": invoice_pdf_path},
            status=status.HTTP_200_OK,
        )

    except Exception as err:
        logger.error(
            f"CREATE INVOICE PDF: Something went wrong while generating pdf! INVOICE: {invoice_id} ERROR: {str(err)}"
        )
        return Response(
            {"success": False, "message": str(err)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(["GET"])
def create_box_label_pdf(request, invoice_id):
    # from config import NEXT_PUBLIC_FILE_REPO_URL
    from .tasks import generate_box_label_pdf_task

    try:
        invoice = get_invoice_by_id(invoice_id=invoice_id)

        if not (box_label_path := invoice.box_label_url):
            box_label_path = generate_box_label_pdf_task(invoice_id=invoice_id)

        logger.info(
            f"CREATE BOX LABEL PDF: Generated box label pdf for invoice {invoice.invoice_number}"
        )
        return Response(
            {"success": True, "box_label_url": box_label_path},
            status=status.HTTP_200_OK,
        )

    except Exception as err:
        logger.error(
            f"CREATE INVOICE PDF: Something went wrong while generating pdf! INVOICE: {invoice_id} ERROR: {str(err)}"
        )
        return Response(
            {"success": False, "message": str(err)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(["GET"])
def generate_e_invoice(request, invoice_id):
    from .clear_tax import generate_irn, download_e_invoice

    try:
        invoice = get_invoice_by_id(invoice_id=invoice_id)

        if not (irn := invoice.irn):
            irn = generate_irn(invoice=invoice)

        if irn:
            if not (e_invoice_path := invoice.e_invoice_url):
                e_invoice_path = download_e_invoice(irn, invoice.seller.gstin)

                invoice.e_invoice_url = e_invoice_path
                invoice.save()

            logger.info(
                f"GENERATE E INVOICE: Generated e-invoice for invoice {invoice.invoice_number}"
            )
            return Response(
                {"success": True, "e_invoice_url": e_invoice_path},
                status=status.HTTP_200_OK,
            )

        logger.error(f"GENERATE E INVOICE: IRN not generated! INVOICE: {invoice_id}")
        return Response(
            {"success": False, "message": "IRN not generated"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as err:
        logger.error(
            f"GENERATE E INVOICE: Something went wrong while generating e-invoice pdf! INVOICE: {invoice_id} ERROR: {str(err)}"
        )
        return Response(
            {"success": False, "message": str(err)}, status=status.HTTP_400_BAD_REQUEST
        )


@csrf_exempt
@api_view(["GET"])
def generate_ewaybill(request, invoice_id):
    from .clear_tax import generate_ewaybill, download_ewaybill

    try:
        invoice = get_invoice_by_id(invoice_id=invoice_id)

        if not (ewb_number := invoice.ewb_number):
            ewb_number = generate_ewaybill(invoice=invoice)

        if ewb_number:
            if not (eway_bill_path := invoice.eway_bill):
                eway_bill_path = download_ewaybill(ewb_number, invoice.seller.gstin)

                invoice.eway_bill = eway_bill_path
                invoice.save()

            logger.info(
                f"GENERATE EWAYBILL: Generated ewaybill for invoice {invoice.invoice_number}"
            )
            return Response(
                {"success": True, "ewaybill_url": eway_bill_path},
                status=status.HTTP_200_OK,
            )

        logger.error(f"GENERATE E INVOICE: EWB not generated! INVOICE: {invoice_id}")
        return Response(
            {"success": False, "message": "EWB not generated"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as err:
        logger.error(
            f"GENERATE EWAYBILL: Something went wrong while generating ewaybill pdf! INVOICE: {invoice_id} ERROR: {str(err)}"
        )
        return Response(
            {"success": False, "message": str(err)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class InvoiceCreateView(APIView):
    """
    View to Create invoices and add products to it
    """

    permission_classes = (IsAuthenticatedOrReadOnly, IsWarehouseOperator)

    def post(self, request):
        data = request.data
        try:
            logger.info(f"Sending data to create invoice")
            invoice = create_invoice_from_data(data)
            if invoice:
                serializer = InvoiceExpandedDetailSerializer(invoice)
                return Response(
                    {"success": True, "data": serializer.data},
                    status=status.HTTP_200_OK,
                )

        except Exception as err:
            logger.error(
                f"CREATE INVOICE VIEW: Something went wrong while creating invoice object! DATA: {data} ERROR: {str(err)}"
            )
            return Response(
                {"success": False, "data": str(err)}, status=status.HTTP_400_BAD_REQUEST
            )

    def patch(self, request):
        data = request.data
        try:
            invoice = get_invoice_by_id(invoice_id=data.get("invoice_id"))

            if invoice:
                logger.info(f"Sending data to update invoice {invoice.invoice_number}")
                invoice = update_invoice_data(invoice, data)
                serializer = InvoiceExpandedDetailSerializer(invoice)
                return Response(
                    {"success": True, "data": serializer.data},
                    status=status.HTTP_200_OK,
                )

        except Exception as err:
            logger.error(
                f"UPDATE INVOICE VIEW: Something went wrong while updating invoice object! DATA: {data} ERROR: {str(err)}"
            )
            return Response(
                {"success": False, "data": str(err)}, status=status.HTTP_400_BAD_REQUEST
            )


class InvoiceBulkUploadView(APIView):
    """
    View to Create invoices from csv uploads
    """

    permission_classes = (IsAuthenticatedOrReadOnly, IsWarehouseOperator)

    def post(self, request):
        try:
            invoice_csv = request.FILES["invoice_csv"].read().decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(invoice_csv))
        except Exception as err:
            logger.error(f"INVOICE BULK UPLOAD: CSV reading error! ERROR: {str(err)}")
            return Response(
                {"success": False, "message": str(err)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            invoice_data = [line for line in csv_reader]

            logger.info(
                f"INVOICE BULK UPLOAD: Length of CSV entries {len(invoice_data)}"
            )

            for data in invoice_data:
                logger.info(f"INVOICE BULK LOOP: Loop data {data}")
                create_draft_invoice_task(data)

            return Response(
                {"success": True, "message": "Tasks scheduled successfully!"},
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            logger.error(f"INVOICE BULK UPLOAD: Loop broke! ERROR: {str(err)}")
            return Response(
                {"success": False, "message": str(err)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class InvoiceDashboardListView(ListAPIView):
    """
    View to list all invoices with minimal data
    for dashboard listing
    """

    pagination_class = StandardResultsSetPagination
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsWarehouseOperator | IsFinanceOperator,
    )
    serializer_class = InvoiceShortDetailSerializer

    def get_queryset(self):
        logger.info("INVOICE DASHBOARD VIEW: filtering invoice data!")
        invoices = (
            InvoiceDetails.objects.filter(is_deleted=False)
            .order_by("-created_at")
            .all()
        )
        return invoices


class InvoiceDetailView(APIView):
    """
    View to list all invoices with all data
    for invoice level viewing
    """

    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsFinanceOperator | IsWarehouseOperator,
    )

    def get(self, request, invoice_id):
        try:
            invoice = InvoiceDetails.objects.get(id=invoice_id)
            if invoice:
                serializer = InvoiceExpandedDetailSerializer(invoice)
                return Response(
                    {"success": True, "data": serializer.data},
                    status=status.HTTP_200_OK,
                )

        except Exception as err:
            return Response(
                {"success": False, "data": str(err)}, status=status.HTTP_404_NOT_FOUND
            )


class InvoiceProductsAddView(APIView):
    """
    View to add products to an invoice with all data
    for invoice level viewing
    """

    permission_classes = (IsAuthenticatedOrReadOnly, IsWarehouseOperator)

    def post(self, request):
        data = request.data
        try:
            invoice_id = data.get("invoice_id")
            product_list = data.get("product_list", [])

            logger.info(
                f"ADDING PRODUCTS TO INVOICE: Sending products to add to invoice"
            )
            complete_invoice = add_products_to_invoice(
                invoice_id=invoice_id, products_list=product_list
            )

            if complete_invoice:
                logger.info(f"ADDING PRODUCTS TO INVOICE: Products added to invoice")
                serializer = InvoiceExpandedDetailSerializer(complete_invoice)
                return Response(
                    {"success": True, "data": serializer.data},
                    status=status.HTTP_201_CREATED,
                )
        except Exception as err:
            logger.error(
                f"ADDING PRODUCTS TO INVOICE: Something went wrong while adding products to invoice! PRODUCT: {product_list} ERROR: {str(err)}"
            )
            return Response(
                {"success": False, "data": str(err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def patch(self, request):
        from .services import get_invoice_product_by_id

        data = request.data
        try:
            invoice_id = data.get("invoice_id")
            invoice_products = data.get("invoice_products", [])

            invoice = get_invoice_by_id(invoice_id=invoice_id)

            for product in invoice_products:
                invoice_product = get_invoice_product_by_id(product.pop("id", None))
                serializer = InvoiceProductsDetailSerializer(
                    instance=invoice_product, data=product, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()

            invoice.save()

            serializer = InvoiceExpandedDetailSerializer(invoice)
            return Response(
                {"success": True, "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        except Exception as err:
            logger.error(
                f"UPDATING PRODUCTS FOR INVOICE: Something went wrong in patching data {invoice.invoice_number}! INVOICE PRODUCTS: {invoice_products} ERROR: {str(err)}"
            )
            return Response(
                {"success": False, "data": str(err)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
