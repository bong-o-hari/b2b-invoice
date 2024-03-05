import os
import pdfkit

from PyPDF2 import PdfMerger
from celery import shared_task
from datetime import datetime

from inboicing_system.settings import logger

# from communication.s3_upload import s3_upload_file
from invoice.utils import generate_invoice_html, generate_box_label_pdfs
from invoice.models import InvoiceDetails
from .utils import create_draft_invoice


@shared_task
def create_draft_invoice_task(invoice_data):
    logger.info(f"Create Invoice Task Scheduled INVOICE DATA: {invoice_data}")
    create_draft_invoice(invoice_data=invoice_data)
    return None


@shared_task
def generate_invoice_pdf_task(invoice_id):
    invoice_model_object = InvoiceDetails.objects.filter(id=invoice_id).first()

    try:
        generated_invoice_html = generate_invoice_html(invoice_model_object)
        current_date = datetime.now()
        file_name = str(invoice_model_object.invoice_number)
        file_path = os.path.join(
            "/b2b-invoices",
            str(current_date.year),
            str(current_date.month),
            str(current_date.day),
        )
        file_url = os.path.join(file_path, file_name + ".pdf")
        tmp_path = "/tmp" + file_path
        os.makedirs(tmp_path, exist_ok=True)
        tmp_file_path = "/tmp" + file_url

        options = {
            "page-size": "A4",
            "margin-top": "0.5in",
            "margin-right": "0.1in",
            "margin-bottom": "0.5in",
            "margin-left": "0.1in",
        }

        pdfkit.from_string(generated_invoice_html, tmp_file_path, options=options)
        # s3_file_obj = s3_upload_file(tmp_file_path, remove_tmp=True)
        # if os.path.exists(tmp_file_path):
        #     os.remove(tmp_file_path)
        # invoice_model_object.invoice_pdf_url = s3_file_obj["file_path"]
        invoice_model_object.invoice_pdf_url = tmp_file_path
        invoice_model_object.save()
        logger.info(
            msg="invoice_pdf_generation",
            extra={"invoice_id": invoice_model_object.id, "file_obj": tmp_file_path},
        )
        return tmp_file_path
    except Exception as e:
        logger.error(
            "invoice_pdf_failed",
            extra={"invoice_id": invoice_model_object.id, "error": str(e)},
        )
        raise e


@shared_task
def generate_box_label_pdf_task(invoice_id):
    invoice_model_object = InvoiceDetails.objects.filter(id=invoice_id).first()
    merger = PdfMerger()
    try:
        pdf_list = generate_box_label_pdfs(invoice_model_object)

        for pdf in pdf_list:
            merger.append(pdf)
            if os.path.exists(pdf):
                os.remove(pdf)

        current_date = datetime.now()
        file_name = f"{str(invoice_model_object.invoice_number)}-box-label"
        file_path = os.path.join(
            "/b2b-invoices",
            str(current_date.year),
            str(current_date.month),
            str(current_date.day),
        )
        file_url = os.path.join(file_path, file_name + ".pdf")
        tmp_path = "/tmp" + file_path
        os.makedirs(tmp_path, exist_ok=True)
        tmp_file_path = "/tmp" + file_url
        merger.write(tmp_file_path)
        merger.close()

        # s3_file_obj = s3_upload_file(tmp_file_path, remove_tmp=True)
        # if os.path.exists(tmp_file_path):
        # os.remove(tmp_file_path)
        # invoice_model_object.box_label_url = s3_file_obj["file_path"]
        invoice_model_object.box_label_url = tmp_file_path
        invoice_model_object.save()
        logger.info(
            msg="box_label_pdf_generation",
            extra={"invoice_id": invoice_model_object.id, "file_obj": tmp_file_path},
        )
        return tmp_file_path
    except Exception as e:
        logger.error(
            "box_label_pdf_failed",
            extra={"invoice_id": invoice_model_object.id, "error": str(e)},
        )
        raise e
